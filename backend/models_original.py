from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    oauth_id = Column(String, unique=True, index=True)  # Provider-specific ID
    email = Column(String, unique=True, index=True)
    name = Column(String)
    provider = Column(String)  # google, github, facebook
    is_onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    one_rms = relationship("OneRM", back_populates="user")
    workout_schedule = relationship("WorkoutSchedule", back_populates="user", uselist=False)
    cycles = relationship("Cycle", back_populates="user")

class OneRM(Base):
    __tablename__ = "one_rms"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movement = Column(String, index=True)  # squat, bench, deadlift, overhead_press
    weight = Column(Float)  # 1RM weight
    unit = Column(String, default="lbs")  # lbs or kg
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to user
    user = relationship("User", back_populates="one_rms")

class WorkoutSchedule(Base):
    __tablename__ = "workout_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    day1_movements = Column(JSON)  # List of 2 movements for day 1
    day2_movements = Column(JSON)  # List of 2 movements for day 2
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to user
    user = relationship("User", back_populates="workout_schedule")

class Cycle(Base):
    __tablename__ = "cycles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cycle_number = Column(Integer)  # 1, 2, 3, etc.
    start_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    training_maxes = Column(JSON)  # Training max for each movement at cycle start
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cycles")
    workouts = relationship("Workout", back_populates="cycle")

class Workout(Base):
    __tablename__ = "workouts"
    
    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"))
    week = Column(Integer)  # 1, 2, 3, 4 (deload)
    day = Column(Integer)   # 1 or 2 (for the 2-day split)
    movements = Column(JSON)  # List of movements for this workout
    sets_reps_data = Column(JSON)  # Complete workout data with sets/reps/weights
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to cycle
    cycle = relationship("Cycle", back_populates="workouts")

# Valid movements for Wendler 5-3-1
VALID_MOVEMENTS = ["squat", "bench", "deadlift", "overhead_press"]

# Wendler 5-3-1 weekly templates
WEEKLY_TEMPLATES = {
    1: [  # Week 1: 5+ week
        {"percentage": 65, "reps": 5},
        {"percentage": 75, "reps": 5}, 
        {"percentage": 85, "reps": "5+"}
    ],
    2: [  # Week 2: 3+ week
        {"percentage": 70, "reps": 3},
        {"percentage": 80, "reps": 3},
        {"percentage": 90, "reps": "3+"}
    ],
    3: [  # Week 3: 5/3/1+ week
        {"percentage": 75, "reps": 5},
        {"percentage": 85, "reps": 3},
        {"percentage": 95, "reps": "1+"}
    ],
    4: [  # Week 4: Deload week
        {"percentage": 40, "reps": 5},
        {"percentage": 50, "reps": 5},
        {"percentage": 60, "reps": 5}
    ]
}