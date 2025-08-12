from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import User, OneRM, WorkoutSchedule, Cycle, Workout
from schemas import UserCreate, UserUpdate, OneRMCreate, OneRMUpdate, OnboardingData, WorkoutScheduleCreate, CycleCreate
from wendler_service import WendlerService
from typing import Optional
from datetime import datetime

# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_oauth_id(db: Session, oauth_id: str, provider: str) -> Optional[User]:
    return db.query(User).filter(
        and_(User.oauth_id == oauth_id, User.provider == provider)
    ).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        oauth_id=user.oauth_id,
        email=user.email,
        name=user.name,
        provider=user.provider
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# 1RM CRUD operations
def get_user_one_rms(db: Session, user_id: int) -> list[OneRM]:
    return db.query(OneRM).filter(OneRM.user_id == user_id).all()

def get_one_rm(db: Session, user_id: int, movement: str) -> Optional[OneRM]:
    return db.query(OneRM).filter(
        and_(OneRM.user_id == user_id, OneRM.movement == movement)
    ).first()

def create_one_rm(db: Session, user_id: int, one_rm: OneRMCreate) -> OneRM:
    db_one_rm = OneRM(
        user_id=user_id,
        movement=one_rm.movement,
        weight=one_rm.weight,
        unit=one_rm.unit
    )
    db.add(db_one_rm)
    db.commit()
    db.refresh(db_one_rm)
    return db_one_rm

def update_one_rm(db: Session, user_id: int, movement: str, one_rm_update: OneRMUpdate) -> Optional[OneRM]:
    db_one_rm = get_one_rm(db, user_id, movement)
    if not db_one_rm:
        return None
    
    for field, value in one_rm_update.dict(exclude_unset=True).items():
        setattr(db_one_rm, field, value)
    
    db.commit()
    db.refresh(db_one_rm)
    return db_one_rm

def delete_one_rm(db: Session, user_id: int, movement: str) -> bool:
    db_one_rm = get_one_rm(db, user_id, movement)
    if not db_one_rm:
        return False
    
    db.delete(db_one_rm)
    db.commit()
    return True

# Workout Schedule CRUD operations
def get_user_workout_schedule(db: Session, user_id: int) -> Optional[WorkoutSchedule]:
    return db.query(WorkoutSchedule).filter(WorkoutSchedule.user_id == user_id).first()

def create_workout_schedule(db: Session, user_id: int, schedule: WorkoutScheduleCreate) -> WorkoutSchedule:
    db_schedule = WorkoutSchedule(
        user_id=user_id,
        day1_movements=schedule.day1_movements,
        day2_movements=schedule.day2_movements
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def update_workout_schedule(db: Session, user_id: int, schedule: WorkoutScheduleCreate) -> Optional[WorkoutSchedule]:
    db_schedule = get_user_workout_schedule(db, user_id)
    if not db_schedule:
        return None
    
    db_schedule.day1_movements = schedule.day1_movements
    db_schedule.day2_movements = schedule.day2_movements
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

# Cycle CRUD operations
def get_user_cycles(db: Session, user_id: int, active_only: bool = False) -> list[Cycle]:
    query = db.query(Cycle).filter(Cycle.user_id == user_id)
    if active_only:
        query = query.filter(Cycle.is_active == True)
    return query.order_by(Cycle.cycle_number.desc()).all()

def get_active_cycle(db: Session, user_id: int) -> Optional[Cycle]:
    return db.query(Cycle).filter(
        and_(Cycle.user_id == user_id, Cycle.is_active == True)
    ).first()

def create_cycle(db: Session, user_id: int, cycle_data: CycleCreate) -> Cycle:
    # Deactivate any existing active cycles
    active_cycle = get_active_cycle(db, user_id)
    if active_cycle:
        active_cycle.is_active = False
        db.commit()
    
    # Create new cycle
    db_cycle = Cycle(
        user_id=user_id,
        cycle_number=cycle_data.cycle_number,
        start_date=datetime.utcnow(),
        training_maxes=cycle_data.training_maxes,
        is_active=True
    )
    db.add(db_cycle)
    db.commit()
    db.refresh(db_cycle)
    
    # Generate workouts for this cycle
    schedule = get_user_workout_schedule(db, user_id)
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
            db.add(db_workout)
        
        db.commit()
    
    return db_cycle

def get_cycle_workouts(db: Session, cycle_id: int) -> list[Workout]:
    return db.query(Workout).filter(Workout.cycle_id == cycle_id).order_by(
        Workout.week, Workout.day
    ).all()

def update_workout_sets(db: Session, workout_id: int, sets_data: dict) -> Optional[Workout]:
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        return None
    
    # Update the sets data with actual completed values
    workout.sets_reps_data = sets_data
    
    db.commit()
    db.refresh(workout)
    return workout

def complete_workout(db: Session, workout_id: int) -> Optional[Workout]:
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        return None
    
    workout.completed = True
    workout.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workout)
    return workout

# Onboarding operations - updated to include workout schedule
def complete_onboarding(db: Session, user_id: int, onboarding_data: OnboardingData) -> dict:
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
        existing = get_one_rm(db, user_id, movement)
        if existing:
            # Update existing
            existing.weight = weight
            existing.unit = onboarding_data.unit
            db.commit()
            db.refresh(existing)
            created_one_rms.append(existing)
        else:
            # Create new
            one_rm = OneRMCreate(
                movement=movement,
                weight=weight,
                unit=onboarding_data.unit
            )
            created_one_rm = create_one_rm(db, user_id, one_rm)
            created_one_rms.append(created_one_rm)
    
    # Create workout schedule
    schedule_data = WorkoutScheduleCreate(
        day1_movements=onboarding_data.day1_movements,
        day2_movements=onboarding_data.day2_movements
    )
    workout_schedule = create_workout_schedule(db, user_id, schedule_data)
    
    # Generate training maxes from 1RMs
    one_rm_dict = {one_rm.movement: one_rm.weight for one_rm in created_one_rms}
    training_maxes = WendlerService.generate_training_maxes(one_rm_dict)
    
    # Create first cycle
    cycle_data = CycleCreate(
        cycle_number=1,
        training_maxes=training_maxes
    )
    first_cycle = create_cycle(db, user_id, cycle_data)
    
    # Mark user as onboarded
    update_user(db, user_id, UserUpdate(is_onboarded=True))
    
    return {
        "one_rms": created_one_rms,
        "workout_schedule": workout_schedule,
        "cycle": first_cycle
    }