import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from jose import JWTError, jwt
from dotenv import load_dotenv
import json
from sqlmodel import Session
from typing import List
from database import engine, get_session, create_db_and_tables
from models import (
    User, UserCreate, UserRead, UserComplete,
    OneRM, OneRMCreate, OneRMUpdate, OneRMRead,
    WorkoutSchedule, WorkoutScheduleCreate, WorkoutScheduleRead,
    Cycle, CycleCreate, CycleUpdate, CycleRead, CycleWithWorkouts,
    Workout, WorkoutRead, WorkoutUpdate, WorkoutStatusUpdate,
    OnboardingData
)
import crud
from wendler_service import WendlerService

load_dotenv()

app = FastAPI(title="Wendler 5-3-1 API", version="0.1.0")

# Create database tables
create_db_and_tables()

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET", "your-secret-key"))

# Add middleware to handle HTTPS proxy headers
@app.middleware("http")
async def https_redirect_middleware(request: Request, call_next):
    # Trust X-Forwarded-Proto header from Caddy
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://the-gigi.github.io", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

security = HTTPBearer()

# OAuth Configuration
oauth = OAuth()

# Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# GitHub OAuth
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# Facebook OAuth
oauth.register(
    name='facebook',
    client_id=os.getenv('FACEBOOK_CLIENT_ID'),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email'},
)

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

# Get current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        oauth_id = payload.get("sub")
        provider = payload.get("provider")
        
        if not oauth_id or not provider:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = crud.get_user_by_oauth_id(session, oauth_id, provider)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

# Admin middleware
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.email != "the.gigi@gmail.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@app.get("/")
async def root():
    return {"message": "Wendler 5-3-1 API"}

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "frontend_origin": os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
        "image": "ghcr.io/the-gigi/wendler-5-3-1:latest"
    }

@app.get("/cors-test")
async def cors_test():
    """Simple endpoint to test CORS configuration"""
    return {"message": "CORS working", "status": "success"}

@app.get("/admin/test")
async def admin_test():
    """Test admin route without authentication"""
    return {"message": "Admin route accessible", "status": "success"}

@app.get("/auth/{provider}")
async def login(provider: str, request: Request):
    if provider not in ['google', 'github', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    client = oauth.create_client(provider)
    redirect_uri = request.url_for('callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/auth/{provider}/callback")
async def callback(provider: str, request: Request, session: Session = Depends(get_session)):
    if provider not in ['google', 'github', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    try:
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        
        # Get user info based on provider
        if provider == 'google':
            user_info = token.get('userinfo')
            oauth_id = user_info['sub']
            email = user_info['email']
            name = user_info['name']
        elif provider == 'github':
            user_resp = await client.get('user', token=token)
            user_info = user_resp.json()
            oauth_id = str(user_info['id'])
            email = user_info.get('email')
            name = user_info.get('name') or user_info['login']
        elif provider == 'facebook':
            user_resp = await client.get('me?fields=id,name,email', token=token)
            user_info = user_resp.json()
            oauth_id = user_info['id']
            email = user_info.get('email')
            name = user_info['name']
        
        # Create or get user from database
        db_user = crud.get_user_by_oauth_id(session, oauth_id, provider)
        if not db_user:
            # Create new user
            user_create = UserCreate(
                oauth_id=oauth_id,
                email=email,
                name=name,
                provider=provider
            )
            db_user = crud.create_user(session, user_create)
        
        # Create JWT token with database user info
        jwt_payload = {
            "sub": db_user.oauth_id,
            "email": db_user.email,
            "name": db_user.name,
            "provider": db_user.provider,
            "user_id": db_user.id
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Return HTML that posts message to parent window and closes popup
        html_content = f"""
        <html>
        <body>
        <script>
            window.opener.postMessage({{
                access_token: '{jwt_token}',
                token_type: 'bearer',
                user: {json.dumps(jwt_payload)}
            }}, '{os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")}');
            window.close();
        </script>
        <p>Login successful! This window should close automatically.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error.error}")

@app.get("/me", response_model=UserComplete)
async def get_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get current user info with their 1RM data, workout schedule, and cycles"""
    user = crud.get_user(session, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Manually load relationships for response
    user_dict = user.model_dump()
    user_dict["one_rms"] = crud.get_user_one_rms(session, user.id)
    user_dict["workout_schedule"] = crud.get_user_workout_schedule(session, user.id)
    user_dict["cycles"] = crud.get_user_cycles(session, user.id)
    
    return UserComplete(**user_dict)

# 1RM API endpoints
@app.get("/one-rms", response_model=List[OneRMRead])
async def get_user_one_rms(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get all 1RM records for the current user"""
    return crud.get_user_one_rms(session, current_user.id)

@app.get("/one-rms/{movement}", response_model=OneRMRead)
async def get_one_rm(movement: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get 1RM for a specific movement"""
    one_rm = crud.get_one_rm(session, current_user.id, movement)
    if not one_rm:
        raise HTTPException(status_code=404, detail="1RM not found for this movement")
    return one_rm

@app.post("/one-rms", response_model=OneRMRead)
async def create_one_rm(one_rm: OneRMCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Create a new 1RM record"""
    # Check if already exists
    existing = crud.get_one_rm(session, current_user.id, one_rm.movement)
    if existing:
        raise HTTPException(status_code=400, detail="1RM already exists for this movement. Use PUT to update.")
    
    return crud.create_one_rm(session, current_user.id, one_rm)

@app.put("/one-rms/{movement}", response_model=OneRMRead)
async def update_one_rm(movement: str, one_rm_update: OneRMUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Update an existing 1RM record"""
    updated_one_rm = crud.update_one_rm(session, current_user.id, movement, one_rm_update)
    if not updated_one_rm:
        raise HTTPException(status_code=404, detail="1RM not found for this movement")
    return updated_one_rm

@app.delete("/one-rms/{movement}")
async def delete_one_rm(movement: str, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Delete a 1RM record"""
    deleted = crud.delete_one_rm(session, current_user.id, movement)
    if not deleted:
        raise HTTPException(status_code=404, detail="1RM not found for this movement")
    return {"message": "1RM deleted successfully"}

# Workout Schedule endpoints
@app.get("/workout-schedule", response_model=WorkoutScheduleRead)
async def get_workout_schedule(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get user's workout schedule"""
    schedule = crud.get_user_workout_schedule(session, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Workout schedule not found")
    return schedule

@app.post("/workout-schedule", response_model=WorkoutScheduleRead)
async def create_workout_schedule(schedule_data: WorkoutScheduleCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Create or update user's workout schedule"""
    existing = crud.get_user_workout_schedule(session, current_user.id)
    if existing:
        return crud.update_workout_schedule(session, current_user.id, schedule_data)
    return crud.create_workout_schedule(session, current_user.id, schedule_data)

# Cycle endpoints
@app.get("/cycles")
async def get_user_cycles(active_only: bool = False, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get user's cycles with basic info"""
    cycles = crud.get_user_cycles(session, current_user.id, active_only=active_only)
    return [
        {
            "id": cycle.id,
            "cycle_number": cycle.cycle_number,
            "start_date": cycle.start_date.isoformat(),
            "is_active": cycle.is_active,
            "training_maxes": cycle.training_maxes,
            "created_at": cycle.created_at.isoformat(),
        }
        for cycle in cycles
    ]

@app.get("/cycles/active", response_model=CycleWithWorkouts)
async def get_active_cycle(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get user's active cycle with workout data"""
    cycle = crud.get_active_cycle(session, current_user.id)
    if not cycle:
        raise HTTPException(status_code=404, detail="No active cycle found")
    
    # Get workouts for this cycle
    workouts = crud.get_cycle_workouts(session, cycle.id)
    
    # Get week dates
    week_dates = WendlerService.get_week_dates(cycle.start_date)
    
    # Convert to workout data format using SQLModel
    workout_reads = []
    for workout in workouts:
        workout_read = WorkoutRead(
            id=workout.id,
            cycle_id=workout.cycle_id,
            week=workout.week,
            day=workout.day,
            movements=workout.movements,
            sets=workout.sets_reps_data,  # Use the database field name
            status=workout.status,
            completed=workout.completed,
            completed_at=workout.completed_at,
            created_at=workout.created_at
        )
        workout_reads.append(workout_read)
    
    return CycleWithWorkouts(
        id=cycle.id,
        cycle_number=cycle.cycle_number,
        training_maxes=cycle.training_maxes,
        start_date=cycle.start_date,
        is_active=cycle.is_active,
        created_at=cycle.created_at,
        user_id=cycle.user_id,
        workouts=workout_reads,
        week_dates=week_dates
    )

@app.get("/cycles/{cycle_id}", response_model=CycleWithWorkouts)
async def get_cycle(cycle_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get a specific cycle with workout data"""
    # Get the cycle and verify it belongs to the user
    cycle = session.get(Cycle, cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Get workouts for this cycle
    workouts = crud.get_cycle_workouts(session, cycle.id)
    
    # Get week dates
    week_dates = WendlerService.get_week_dates(cycle.start_date)
    
    # Convert to workout data format using SQLModel
    workout_reads = []
    for workout in workouts:
        workout_read = WorkoutRead(
            id=workout.id,
            cycle_id=workout.cycle_id,
            week=workout.week,
            day=workout.day,
            movements=workout.movements,
            sets=workout.sets_reps_data,  # Use the database field name
            status=workout.status,
            completed=workout.completed,
            completed_at=workout.completed_at,
            created_at=workout.created_at
        )
        workout_reads.append(workout_read)
    
    return CycleWithWorkouts(
        id=cycle.id,
        cycle_number=cycle.cycle_number,
        training_maxes=cycle.training_maxes,
        start_date=cycle.start_date,
        is_active=cycle.is_active,
        created_at=cycle.created_at,
        user_id=cycle.user_id,
        workouts=workout_reads,
        week_dates=week_dates
    )

@app.post("/cycles/next")
async def create_next_cycle(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Create next cycle with progressed training maxes"""
    current_cycle = crud.get_active_cycle(session, current_user.id)
    if not current_cycle:
        raise HTTPException(status_code=400, detail="No active cycle to progress from")
    
    # Progress training maxes
    new_training_maxes = WendlerService.progress_training_maxes(current_cycle.training_maxes)
    
    # Create next cycle
    cycle_data = CycleCreate(
        cycle_number=current_cycle.cycle_number + 1,
        training_maxes=new_training_maxes
    )
    
    new_cycle = crud.create_cycle(session, current_user.id, cycle_data)
    return {"message": "Next cycle created successfully", "cycle": new_cycle}

@app.put("/cycles/{cycle_id}")
async def update_cycle(cycle_id: int, cycle_update: CycleUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Update cycle details"""
    # Get the cycle and verify it belongs to the user
    cycle = session.get(Cycle, cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    updated_cycle = crud.update_cycle(session, cycle_id, cycle_update)
    if not updated_cycle:
        raise HTTPException(status_code=400, detail="Failed to update cycle")
    
    return {"message": "Cycle updated successfully", "cycle": updated_cycle}

@app.post("/workouts/{workout_id}/complete")
async def complete_workout(workout_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Mark a workout as completed"""
    workout = crud.complete_workout(session, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout completed successfully"}

@app.put("/workouts/{workout_id}/sets")
async def update_workout_sets(workout_id: int, sets_data: dict, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Update workout sets with actual completed weights and reps"""
    workout = crud.update_workout_sets(session, workout_id, sets_data)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout sets updated successfully", "workout": workout}

@app.put("/workouts/{workout_id}/status")
async def update_workout_status(workout_id: int, status_data: WorkoutStatusUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Update workout status"""
    from models import WORKOUT_STATUSES
    
    if status_data.status not in WORKOUT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {WORKOUT_STATUSES}")
    
    workout = crud.update_workout_status(session, workout_id, status_data.status)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout status updated successfully", "workout": workout}

# Onboarding endpoint - updated to include workout schedule
@app.get("/movements/day2")
async def get_day2_movements(day1_movements: str):
    """Get available movements for day 2 based on day 1 selection"""
    from models import VALID_MOVEMENTS
    
    # Parse day1_movements (expecting comma-separated string)
    try:
        day1_list = [movement.strip() for movement in day1_movements.split(',')]
    except:
        raise HTTPException(status_code=400, detail="Invalid day1_movements format. Use comma-separated values.")
    
    # Validate day1 movements
    if len(day1_list) != 2:
        raise HTTPException(status_code=400, detail="Day 1 must have exactly 2 movements")
    
    for movement in day1_list:
        if movement not in VALID_MOVEMENTS:
            raise HTTPException(status_code=400, detail=f"Invalid movement: {movement}")
    
    # Calculate remaining movements for day 2
    day2_movements = [movement for movement in VALID_MOVEMENTS if movement not in day1_list]
    
    return {
        "day1_movements": day1_list,
        "day2_movements": day2_movements
    }

@app.post("/onboarding")
async def complete_onboarding(onboarding_data: OnboardingData, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Complete user onboarding by setting all 4 1RM values and workout schedule"""
    if current_user.is_onboarded:
        raise HTTPException(status_code=400, detail="User is already onboarded")
    
    result = crud.complete_onboarding(session, current_user.id, onboarding_data)
    return {
        "message": "Onboarding completed successfully",
        "data": result
    }

# Admin endpoints
@app.options("/admin/stats")
async def admin_stats_options():
    """Handle preflight OPTIONS request for admin stats"""
    return {}

@app.get("/admin/stats")
async def get_admin_stats(admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Get admin dashboard statistics"""
    from sqlalchemy import func
    from datetime import timedelta
    
    # Get total users count
    total_users_stmt = select(func.count(User.id))
    total_users = session.exec(total_users_stmt).first()
    
    # Get active cycles count
    active_cycles_stmt = select(func.count(Cycle.id)).where(Cycle.is_active == True)
    active_cycles = session.exec(active_cycles_stmt).first()
    
    # Get total cycles count
    total_cycles_stmt = select(func.count(Cycle.id))
    total_cycles = session.exec(total_cycles_stmt).first()
    
    # Get new users in last 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_stmt = select(func.count(User.id)).where(User.created_at >= week_ago)
    new_users_last_week = session.exec(new_users_stmt).first()
    
    return {
        "totalUsers": total_users or 0,
        "activeCycles": active_cycles or 0,
        "totalCycles": total_cycles or 0,
        "lastWeekNewUsers": new_users_last_week or 0
    }

@app.options("/admin/users")
async def admin_users_options():
    """Handle preflight OPTIONS request for admin users"""
    return {}

@app.get("/admin/users")
async def get_admin_users(limit: int = 100, offset: int = 0, admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Get all users with basic info for admin"""
    stmt = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
    users = session.exec(stmt).all()
    
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "provider": user.provider,
            "is_onboarded": user.is_onboarded,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        for user in users
    ]

@app.options("/admin/cycles")
async def admin_cycles_options():
    """Handle preflight OPTIONS request for admin cycles"""
    return {}

@app.get("/admin/cycles")
async def get_admin_cycles(limit: int = 100, offset: int = 0, admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Get all cycles with user info for admin"""
    from sqlalchemy.orm import selectinload
    
    stmt = select(Cycle).options(selectinload(Cycle.user)).offset(offset).limit(limit).order_by(Cycle.created_at.desc())
    cycles = session.exec(stmt).all()
    
    return [
        {
            "id": cycle.id,
            "cycle_number": cycle.cycle_number,
            "start_date": cycle.start_date.isoformat(),
            "is_active": cycle.is_active,
            "training_maxes": cycle.training_maxes,
            "created_at": cycle.created_at.isoformat(),
            "user": {
                "id": cycle.user.id,
                "name": cycle.user.name,
                "email": cycle.user.email
            } if cycle.user else None
        }
        for cycle in cycles
    ]

@app.get("/admin/users/{user_id}")
async def get_admin_user_detail(user_id: int, admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Get detailed user information for admin"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's 1RMs, workout schedule, and cycles
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "provider": user.provider,
        "oauth_id": user.oauth_id,
        "is_onboarded": user.is_onboarded,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "one_rms": crud.get_user_one_rms(session, user.id),
        "workout_schedule": crud.get_user_workout_schedule(session, user.id),
        "cycles": crud.get_user_cycles(session, user.id)
    }
    
    return user_data

@app.post("/admin/export")
async def export_admin_data(export_type: str = "users", admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Export data for admin (placeholder for now)"""
    if export_type not in ["users", "cycles", "workouts", "all"]:
        raise HTTPException(status_code=400, detail="Invalid export type. Use: users, cycles, workouts, or all")
    
    # This is a placeholder - in a real implementation, you'd generate CSV/JSON files
    return {
        "message": f"Export of {export_type} data initiated",
        "export_type": export_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "Export functionality is placeholder - implement file generation as needed"
    }

@app.delete("/admin/users/{user_id}")
async def delete_admin_user(user_id: int, admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Delete a user and all associated data (cascading delete)"""
    user_to_delete = session.get(User, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_to_delete.email == "the.gigi@gmail.com":
        raise HTTPException(status_code=403, detail="Cannot delete admin user")
    
    # SQLAlchemy will handle cascading deletes based on relationships
    session.delete(user_to_delete)
    session.commit()
    
    return {"message": f"User {user_to_delete.name} and all associated data deleted successfully"}

@app.delete("/admin/cycles/{cycle_id}")
async def delete_admin_cycle(cycle_id: int, admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Delete a cycle and all associated workouts"""
    cycle_to_delete = session.get(Cycle, cycle_id)
    if not cycle_to_delete:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # SQLAlchemy will handle cascading deletes for workouts
    session.delete(cycle_to_delete)
    session.commit()
    
    return {"message": f"Cycle {cycle_to_delete.cycle_number} and all associated workouts deleted successfully"}

@app.delete("/admin/workouts/{workout_id}")
async def delete_admin_workout(workout_id: int, admin_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """Delete a specific workout"""
    workout_to_delete = session.get(Workout, workout_id)
    if not workout_to_delete:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    session.delete(workout_to_delete)
    session.commit()
    
    return {"message": f"Workout deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)