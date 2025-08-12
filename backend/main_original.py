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
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User as UserModel
import crud, schemas
from wendler_service import WendlerService

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wendler 5-3-1 API", version="0.1.0")

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET", "your-secret-key"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Get current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        oauth_id = payload.get("sub")
        provider = payload.get("provider")
        
        if not oauth_id or not provider:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = crud.get_user_by_oauth_id(db, oauth_id, provider)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

@app.get("/")
async def root():
    return {"message": "Wendler 5-3-1 API"}

@app.get("/auth/{provider}")
async def login(provider: str, request: Request):
    if provider not in ['google', 'github', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    client = oauth.create_client(provider)
    redirect_uri = request.url_for('callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/auth/{provider}/callback")
async def callback(provider: str, request: Request, db: Session = Depends(get_db)):
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
        db_user = crud.get_user_by_oauth_id(db, oauth_id, provider)
        if not db_user:
            # Create new user
            user_create = schemas.UserCreate(
                oauth_id=oauth_id,
                email=email,
                name=name,
                provider=provider
            )
            db_user = crud.create_user(db, user_create)
        
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
            }}, 'http://localhost:3000');
            window.close();
        </script>
        <p>Login successful! This window should close automatically.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error.error}")

@app.get("/me", response_model=schemas.UserComplete)
async def get_me(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user info with their 1RM data, workout schedule, and cycles"""
    user = crud.get_user(db, current_user.id)
    return user

# 1RM API endpoints
@app.get("/one-rms", response_model=list[schemas.OneRM])
async def get_user_one_rms(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all 1RM records for the current user"""
    return crud.get_user_one_rms(db, current_user.id)

@app.get("/one-rms/{movement}", response_model=schemas.OneRM)
async def get_one_rm(movement: str, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get 1RM for a specific movement"""
    one_rm = crud.get_one_rm(db, current_user.id, movement)
    if not one_rm:
        raise HTTPException(status_code=404, detail="1RM not found for this movement")
    return one_rm

@app.post("/one-rms", response_model=schemas.OneRM)
async def create_one_rm(one_rm: schemas.OneRMCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new 1RM record"""
    # Check if already exists
    existing = crud.get_one_rm(db, current_user.id, one_rm.movement)
    if existing:
        raise HTTPException(status_code=400, detail="1RM already exists for this movement. Use PUT to update.")
    
    return crud.create_one_rm(db, current_user.id, one_rm)

@app.put("/one-rms/{movement}", response_model=schemas.OneRM)
async def update_one_rm(movement: str, one_rm_update: schemas.OneRMUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update an existing 1RM record"""
    updated_one_rm = crud.update_one_rm(db, current_user.id, movement, one_rm_update)
    if not updated_one_rm:
        raise HTTPException(status_code=404, detail="1RM not found for this movement")
    return updated_one_rm

@app.delete("/one-rms/{movement}")
async def delete_one_rm(movement: str, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a 1RM record"""
    deleted = crud.delete_one_rm(db, current_user.id, movement)
    if not deleted:
        raise HTTPException(status_code=404, detail="1RM not found for this movement")
    return {"message": "1RM deleted successfully"}

# Workout Schedule endpoints
@app.get("/workout-schedule", response_model=schemas.WorkoutSchedule)
async def get_workout_schedule(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's workout schedule"""
    schedule = crud.get_user_workout_schedule(db, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Workout schedule not found")
    return schedule

@app.post("/workout-schedule", response_model=schemas.WorkoutSchedule)
async def create_workout_schedule(schedule_data: schemas.WorkoutScheduleCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create or update user's workout schedule"""
    existing = crud.get_user_workout_schedule(db, current_user.id)
    if existing:
        return crud.update_workout_schedule(db, current_user.id, schedule_data)
    return crud.create_workout_schedule(db, current_user.id, schedule_data)

# Cycle endpoints
@app.get("/cycles")
async def get_user_cycles(active_only: bool = False, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's cycles with basic info"""
    cycles = crud.get_user_cycles(db, current_user.id, active_only=active_only)
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

@app.get("/cycles/active", response_model=schemas.CycleWithWorkouts)
async def get_active_cycle(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's active cycle with workout data"""
    cycle = crud.get_active_cycle(db, current_user.id)
    if not cycle:
        raise HTTPException(status_code=404, detail="No active cycle found")
    
    # Get workouts for this cycle
    workouts = crud.get_cycle_workouts(db, cycle.id)
    
    # Get week dates
    week_dates = WendlerService.get_week_dates(cycle.start_date)
    
    # Convert to workout data format
    workout_data = []
    for workout in workouts:
        workout_dict = {
            "id": workout.id,
            "week": workout.week,
            "day": workout.day,
            "movements": workout.movements,
            "sets": workout.sets_reps_data,
            "completed": workout.completed
        }
        workout_data.append(workout_dict)
    
    return {
        "id": cycle.id,
        "user_id": cycle.user_id,
        "cycle_number": cycle.cycle_number,
        "start_date": cycle.start_date.isoformat(),
        "is_active": cycle.is_active,
        "training_maxes": cycle.training_maxes,
        "created_at": cycle.created_at.isoformat(),
        "workouts": workout_data,
        "week_dates": week_dates
    }

@app.post("/cycles/next")
async def create_next_cycle(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create next cycle with progressed training maxes"""
    current_cycle = crud.get_active_cycle(db, current_user.id)
    if not current_cycle:
        raise HTTPException(status_code=400, detail="No active cycle to progress from")
    
    # Progress training maxes
    new_training_maxes = WendlerService.progress_training_maxes(current_cycle.training_maxes)
    
    # Create next cycle
    cycle_data = schemas.CycleCreate(
        cycle_number=current_cycle.cycle_number + 1,
        training_maxes=new_training_maxes
    )
    
    new_cycle = crud.create_cycle(db, current_user.id, cycle_data)
    return {"message": "Next cycle created successfully", "cycle": new_cycle}

@app.post("/workouts/{workout_id}/complete")
async def complete_workout(workout_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a workout as completed"""
    workout = crud.complete_workout(db, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout completed successfully"}

@app.put("/workouts/{workout_id}/sets")
async def update_workout_sets(workout_id: int, sets_data: dict, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update workout sets with actual completed weights and reps"""
    workout = crud.update_workout_sets(db, workout_id, sets_data)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout sets updated successfully", "workout": workout}

# Onboarding endpoint - updated to include workout schedule
@app.post("/onboarding")
async def complete_onboarding(onboarding_data: schemas.OnboardingData, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Complete user onboarding by setting all 4 1RM values and workout schedule"""
    if current_user.is_onboarded:
        raise HTTPException(status_code=400, detail="User is already onboarded")
    
    result = crud.complete_onboarding(db, current_user.id, onboarding_data)
    return {
        "message": "Onboarding completed successfully",
        "data": result
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
