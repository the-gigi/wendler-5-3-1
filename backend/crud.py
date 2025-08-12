from sqlmodel import Session, select
from models import (
    User, UserCreate, UserUpdate,
    OneRM, OneRMCreate, OneRMUpdate,
    WorkoutSchedule, WorkoutScheduleCreate,
    Cycle, CycleCreate,
    Workout, WorkoutCreate, WorkoutUpdate,
    OnboardingData
)
from wendler_service import WendlerService
from typing import Optional, List
from datetime import datetime

# User CRUD operations
def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

def get_user_by_oauth_id(session: Session, oauth_id: str, provider: str) -> Optional[User]:
    statement = select(User).where(User.oauth_id == oauth_id, User.provider == provider)
    return session.exec(statement).first()

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def create_user(session: Session, user: UserCreate) -> User:
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def update_user(session: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = get_user(session, user_id)
    if not db_user:
        return None
    
    user_data = user_update.model_dump(exclude_unset=True)
    for field, value in user_data.items():
        setattr(db_user, field, value)
    
    if user_data:
        db_user.updated_at = datetime.utcnow()
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# 1RM CRUD operations
def get_user_one_rms(session: Session, user_id: int) -> List[OneRM]:
    statement = select(OneRM).where(OneRM.user_id == user_id)
    return list(session.exec(statement).all())

def get_one_rm(session: Session, user_id: int, movement: str) -> Optional[OneRM]:
    statement = select(OneRM).where(OneRM.user_id == user_id, OneRM.movement == movement)
    return session.exec(statement).first()

def create_one_rm(session: Session, user_id: int, one_rm: OneRMCreate) -> OneRM:
    db_one_rm = OneRM.model_validate(one_rm, update={"user_id": user_id})
    session.add(db_one_rm)
    session.commit()
    session.refresh(db_one_rm)
    return db_one_rm

def update_one_rm(session: Session, user_id: int, movement: str, one_rm_update: OneRMUpdate) -> Optional[OneRM]:
    db_one_rm = get_one_rm(session, user_id, movement)
    if not db_one_rm:
        return None
    
    update_data = one_rm_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_one_rm, field, value)
    
    if update_data:
        db_one_rm.updated_at = datetime.utcnow()
    
    session.add(db_one_rm)
    session.commit()
    session.refresh(db_one_rm)
    return db_one_rm

def delete_one_rm(session: Session, user_id: int, movement: str) -> bool:
    db_one_rm = get_one_rm(session, user_id, movement)
    if not db_one_rm:
        return False
    
    session.delete(db_one_rm)
    session.commit()
    return True

# Workout Schedule CRUD operations
def get_user_workout_schedule(session: Session, user_id: int) -> Optional[WorkoutSchedule]:
    statement = select(WorkoutSchedule).where(WorkoutSchedule.user_id == user_id)
    return session.exec(statement).first()

def create_workout_schedule(session: Session, user_id: int, schedule: WorkoutScheduleCreate) -> WorkoutSchedule:
    db_schedule = WorkoutSchedule.model_validate(schedule, update={"user_id": user_id})
    session.add(db_schedule)
    session.commit()
    session.refresh(db_schedule)
    return db_schedule

def update_workout_schedule(session: Session, user_id: int, schedule: WorkoutScheduleCreate) -> Optional[WorkoutSchedule]:
    db_schedule = get_user_workout_schedule(session, user_id)
    if not db_schedule:
        return None
    
    db_schedule.day1_movements = schedule.day1_movements
    db_schedule.day2_movements = schedule.day2_movements
    db_schedule.updated_at = datetime.utcnow()
    
    session.add(db_schedule)
    session.commit()
    session.refresh(db_schedule)
    return db_schedule

# Cycle CRUD operations
def get_user_cycles(session: Session, user_id: int, active_only: bool = False) -> List[Cycle]:
    statement = select(Cycle).where(Cycle.user_id == user_id)
    if active_only:
        statement = statement.where(Cycle.is_active == True)
    statement = statement.order_by(Cycle.cycle_number.desc())
    return list(session.exec(statement).all())

def get_active_cycle(session: Session, user_id: int) -> Optional[Cycle]:
    statement = select(Cycle).where(Cycle.user_id == user_id, Cycle.is_active == True)
    return session.exec(statement).first()

def create_cycle(session: Session, user_id: int, cycle_data: CycleCreate) -> Cycle:
    # Deactivate any existing active cycles
    active_cycle = get_active_cycle(session, user_id)
    if active_cycle:
        active_cycle.is_active = False
        session.add(active_cycle)
        session.commit()
    
    # Create new cycle
    db_cycle = Cycle(
        user_id=user_id,
        cycle_number=cycle_data.cycle_number,
        training_maxes=cycle_data.training_maxes,
        is_active=True
    )
    session.add(db_cycle)
    session.commit()
    session.refresh(db_cycle)
    
    # Generate workouts for this cycle
    schedule = get_user_workout_schedule(session, user_id)
    if schedule:
        workout_data = WendlerService.generate_cycle_workouts(
            cycle_data.training_maxes,
            {
                "day1_movements": schedule.day1_movements,
                "day2_movements": schedule.day2_movements
            }
        )
        
        # Create workout records
        for workout in workout_data:
            db_workout = Workout(
                cycle_id=db_cycle.id,
                week=workout["week"],
                day=workout["day"],
                movements=workout["movements"],
                sets_reps_data=workout["sets"],
                completed=False
            )
            session.add(db_workout)
        
        session.commit()
    
    return db_cycle

def get_cycle_workouts(session: Session, cycle_id: int) -> List[Workout]:
    statement = select(Workout).where(Workout.cycle_id == cycle_id).order_by(Workout.week, Workout.day)
    return list(session.exec(statement).all())

def update_workout_sets(session: Session, workout_id: int, sets_data: dict) -> Optional[Workout]:
    workout = session.get(Workout, workout_id)
    if not workout:
        return None
    
    # Update the sets data with actual completed values
    workout.sets_reps_data = sets_data
    workout.updated_at = datetime.utcnow()
    
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout

def complete_workout(session: Session, workout_id: int) -> Optional[Workout]:
    workout = session.get(Workout, workout_id)
    if not workout:
        return None
    
    workout.completed = True
    workout.status = "completed"
    workout.completed_at = datetime.utcnow()
    workout.updated_at = datetime.utcnow()
    
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout

def update_workout_status(session: Session, workout_id: int, status: str) -> Optional[Workout]:
    workout = session.get(Workout, workout_id)
    if not workout:
        return None
    
    workout.status = status
    if status == "completed":
        workout.completed = True
        workout.completed_at = datetime.utcnow()
    elif status in ["dnf", "skipped"]:
        workout.completed = False
        workout.completed_at = None
    
    workout.updated_at = datetime.utcnow()
    
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout

# Onboarding operations - updated to include workout schedule
def complete_onboarding(session: Session, user_id: int, onboarding_data: OnboardingData) -> dict:
    """Complete user onboarding by setting all 4 1RM values, workout schedule, and creating first cycle"""
    
    # Create or update all 4 movements
    movements = {
        "squat": onboarding_data.squat,
        "bench": onboarding_data.bench,
        "deadlift": onboarding_data.deadlift,
        "overhead_press": onboarding_data.overhead_press
    }
    
    created_one_rms = []
    
    for movement, weight in movements.items():
        # Check if already exists
        existing = get_one_rm(session, user_id, movement)
        if existing:
            # Update existing
            existing.weight = weight
            existing.unit = onboarding_data.unit
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            created_one_rms.append(existing)
        else:
            # Create new
            one_rm = OneRMCreate(
                movement=movement,
                weight=weight,
                unit=onboarding_data.unit
            )
            created_one_rm = create_one_rm(session, user_id, one_rm)
            created_one_rms.append(created_one_rm)
    
    # Create workout schedule
    schedule_data = WorkoutScheduleCreate(
        day1_movements=onboarding_data.day1_movements,
        day2_movements=onboarding_data.day2_movements
    )
    workout_schedule = create_workout_schedule(session, user_id, schedule_data)
    
    # Generate training maxes from 1RMs
    one_rm_dict = {one_rm.movement: one_rm.weight for one_rm in created_one_rms}
    training_maxes = WendlerService.generate_training_maxes(one_rm_dict)
    
    # Create first cycle
    cycle_data = CycleCreate(
        cycle_number=1,
        training_maxes=training_maxes
    )
    first_cycle = create_cycle(session, user_id, cycle_data)
    
    # Mark user as onboarded
    update_user(session, user_id, UserUpdate(is_onboarded=True))
    
    return {
        "one_rms": created_one_rms,
        "workout_schedule": workout_schedule,
        "cycle": first_cycle
    }