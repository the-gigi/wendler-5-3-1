from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: str
    name: str
    provider: str

class UserCreate(UserBase):
    oauth_id: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_onboarded: Optional[bool] = None

class User(UserBase):
    id: int
    oauth_id: str
    is_onboarded: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 1RM schemas
class OneRMBase(BaseModel):
    movement: str
    weight: float
    unit: str = "lbs"
    
    @validator('movement')
    def validate_movement(cls, v):
        valid_movements = ["squat", "bench", "deadlift", "overhead_press"]
        if v not in valid_movements:
            raise ValueError(f"Movement must be one of: {valid_movements}")
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError("Weight must be positive")
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        if v not in ["lbs", "kg"]:
            raise ValueError("Unit must be 'lbs' or 'kg'")
        return v

class OneRMCreate(OneRMBase):
    pass

class OneRMUpdate(BaseModel):
    weight: Optional[float] = None
    unit: Optional[str] = None
    
    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Weight must be positive")
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        if v is not None and v not in ["lbs", "kg"]:
            raise ValueError("Unit must be 'lbs' or 'kg'")
        return v

class OneRM(OneRMBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Workout Schedule schemas
class WorkoutScheduleBase(BaseModel):
    day1_movements: list[str]
    day2_movements: list[str]
    
    @validator('day1_movements', 'day2_movements')
    def validate_movements(cls, v):
        if len(v) != 2:
            raise ValueError("Each day must have exactly 2 movements")
        valid_movements = ["squat", "bench", "deadlift", "overhead_press"]
        for movement in v:
            if movement not in valid_movements:
                raise ValueError(f"Movement must be one of: {valid_movements}")
        return v
    
    @validator('day1_movements')
    def validate_split_recommendation(cls, v, values):
        # Recommend splitting squat and deadlift
        if 'squat' in v and 'deadlift' in v:
            raise ValueError("Recommend splitting squat and deadlift between different days")
        return v

class WorkoutScheduleCreate(WorkoutScheduleBase):
    pass

class WorkoutSchedule(WorkoutScheduleBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Set/Rep data structure
class SetData(BaseModel):
    percentage: int
    reps: str | int  # Can be "5+" or actual number
    weight: float
    completed_reps: Optional[int] = None
    actual_weight: Optional[float] = None

class WorkoutData(BaseModel):
    id: Optional[int] = None
    week: int
    day: int
    movements: list[str]
    sets: dict[str, list[SetData]]  # movement -> list of sets
    completed: Optional[bool] = False

# Cycle schemas
class CycleBase(BaseModel):
    cycle_number: int
    training_maxes: dict[str, float]  # movement -> training max

class CycleCreate(CycleBase):
    pass

class Cycle(CycleBase):
    id: int
    user_id: int
    start_date: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class CycleWithWorkouts(Cycle):
    workouts: list[WorkoutData] = []

# Onboarding schema - now includes workout schedule
class OnboardingData(BaseModel):
    squat: float
    bench: float
    deadlift: float
    overhead_press: float
    unit: str = "lbs"
    day1_movements: list[str]
    day2_movements: list[str]
    
    @validator('squat', 'bench', 'deadlift', 'overhead_press')
    def validate_weights(cls, v):
        if v <= 0:
            raise ValueError("All weights must be positive")
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        if v not in ["lbs", "kg"]:
            raise ValueError("Unit must be 'lbs' or 'kg'")
        return v
    
    @validator('day1_movements', 'day2_movements')
    def validate_movements(cls, v):
        if len(v) != 2:
            raise ValueError("Each day must have exactly 2 movements")
        valid_movements = ["squat", "bench", "deadlift", "overhead_press"]
        for movement in v:
            if movement not in valid_movements:
                raise ValueError(f"Movement must be one of: {valid_movements}")
        return v

class UserWithOneRMs(User):
    one_rms: list[OneRM] = []

class UserComplete(User):
    one_rms: list[OneRM] = []
    workout_schedule: Optional[WorkoutSchedule] = None
    cycles: list[Cycle] = []