from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import validator

# Base classes for different types of models
class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

# User Models
class UserBase(SQLModel):
    email: str = Field(index=True)
    name: str
    provider: str
    oauth_id: str = Field(index=True)
    is_onboarded: bool = Field(default=False)

class User(UserBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    one_rms: List["OneRM"] = Relationship(back_populates="user")
    workout_schedules: List["WorkoutSchedule"] = Relationship(back_populates="user")
    cycles: List["Cycle"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    pass

class UserUpdate(SQLModel):
    name: Optional[str] = None
    is_onboarded: Optional[bool] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserComplete(UserRead):
    one_rms: List["OneRMRead"] = []
    workout_schedule: Optional["WorkoutScheduleRead"] = None
    cycles: List["CycleRead"] = []

# OneRM Models
class OneRMBase(SQLModel):
    movement: str = Field(index=True)
    weight: float
    unit: str = Field(default="lbs")
    
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

class OneRM(OneRMBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="one_rms")

class OneRMCreate(OneRMBase):
    pass

class OneRMUpdate(SQLModel):
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

class OneRMRead(OneRMBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# Workout Schedule Models
class WorkoutScheduleBase(SQLModel):
    day1_movements: List[str] = Field(sa_column=Column(JSON))
    day2_movements: List[str] = Field(sa_column=Column(JSON))
    
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

class WorkoutSchedule(WorkoutScheduleBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="workout_schedules")

class WorkoutScheduleCreate(WorkoutScheduleBase):
    pass

class WorkoutScheduleRead(WorkoutScheduleBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# Set Data (embedded model, not a table)
class SetData(SQLModel):
    percentage: int
    reps: str | int  # Can be "5+" or actual number
    weight: float
    completed_reps: Optional[int] = None
    actual_weight: Optional[float] = None

# Cycle Models
class CycleBase(SQLModel):
    cycle_number: int
    training_maxes: Dict[str, float] = Field(sa_column=Column(JSON))
    start_date: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

class Cycle(CycleBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="cycles")
    workouts: List["Workout"] = Relationship(back_populates="cycle")

class CycleCreate(SQLModel):
    cycle_number: int
    training_maxes: Dict[str, float]

class CycleRead(CycleBase):
    id: int
    user_id: int
    created_at: datetime

class CycleWithWorkouts(CycleRead):
    workouts: List["WorkoutRead"] = []
    week_dates: Optional[Dict[int, Dict[str, str]]] = None

# Workout status enum values
WORKOUT_STATUSES = ["not-started", "in-progress", "completed", "dnf", "skipped"]

# Workout Models
class WorkoutBase(SQLModel):
    week: int
    day: int
    movements: List[str] = Field(sa_column=Column(JSON))
    status: str = Field(default="not-started")
    completed: bool = Field(default=False)

class Workout(WorkoutBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cycle_id: int = Field(foreign_key="cycle.id")
    completed_at: Optional[datetime] = None
    
    # Database field for sets data
    sets_reps_data: Dict[str, List[Dict[str, Any]]] = Field(sa_column=Column(JSON))
    
    # Relationships
    cycle: Optional[Cycle] = Relationship(back_populates="workouts")

class WorkoutCreate(WorkoutBase):
    cycle_id: int

class WorkoutRead(SQLModel):
    id: int
    cycle_id: int
    week: int
    day: int
    movements: List[str]
    sets: Dict[str, List[Dict[str, Any]]]  # This will map to sets_reps_data
    status: str
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

class WorkoutUpdate(SQLModel):
    sets: Optional[Dict[str, List[Dict[str, Any]]]] = None
    status: Optional[str] = None
    completed: Optional[bool] = None
    completed_at: Optional[datetime] = None

# Onboarding Schema (not a table)
class OnboardingData(SQLModel):
    squat: float
    bench: float
    deadlift: float
    overhead_press: float
    unit: str = "lbs"
    day1_movements: List[str]
    day2_movements: List[str]
    
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

# Wendler 5-3-1 specific constants
WEEKLY_TEMPLATES = {
    1: [{"percentage": 65, "reps": 5}, {"percentage": 75, "reps": 5}, {"percentage": 85, "reps": "5+"}],
    2: [{"percentage": 70, "reps": 3}, {"percentage": 80, "reps": 3}, {"percentage": 90, "reps": "3+"}],
    3: [{"percentage": 75, "reps": 5}, {"percentage": 85, "reps": 3}, {"percentage": 95, "reps": "1+"}],
    4: [{"percentage": 40, "reps": 5}, {"percentage": 50, "reps": 5}, {"percentage": 60, "reps": 5}]
}

VALID_MOVEMENTS = ["squat", "bench", "deadlift", "overhead_press"]