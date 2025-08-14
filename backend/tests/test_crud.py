"""
Tests for CRUD operations.
"""
from models import (
    UserCreate, UserUpdate,
    OneRMCreate, OneRMUpdate,
    WorkoutScheduleCreate,
    CycleCreate,
    OnboardingData
)

import crud

class TestUserCRUD:
    def test_create_user(self, session):
        """Test creating a user."""
        user_data = UserCreate(
            oauth_id="test_oauth_id",
            email="test@example.com", 
            name="Test User",
            provider="google"
        )
        user = crud.create_user(session, user_data)
        
        assert user.oauth_id == "test_oauth_id"
        assert user.email == "test@example.com"
        assert user.is_onboarded is False
        assert user.id is not None

    def test_get_user(self, session, test_user):
        """Test retrieving a user by ID."""
        retrieved_user = crud.get_user(session, test_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email

    def test_get_user_by_oauth_id(self, session, test_user):
        """Test retrieving a user by OAuth ID."""
        retrieved_user = crud.get_user_by_oauth_id(
            session, test_user.oauth_id, test_user.provider
        )
        
        assert retrieved_user is not None
        assert retrieved_user.oauth_id == test_user.oauth_id

    def test_get_user_by_email(self, session, test_user):
        """Test retrieving a user by email."""
        retrieved_user = crud.get_user_by_email(session, test_user.email)
        
        assert retrieved_user is not None
        assert retrieved_user.email == test_user.email

    def test_update_user(self, session, test_user):
        """Test updating a user."""
        update_data = UserUpdate(name="Updated Name", is_onboarded=True)
        updated_user = crud.update_user(session, test_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.is_onboarded is True
        assert updated_user.updated_at is not None

    def test_update_user_not_found(self, session):
        """Test updating a non-existent user."""
        update_data = UserUpdate(name="Updated Name")
        result = crud.update_user(session, 999, update_data)
        assert result is None


class TestOneRMCRUD:
    def test_create_one_rm(self, session, test_user):
        """Test creating a 1RM."""
        onerm_data = OneRMCreate(
            movement="squat",
            weight=225.0,
            unit="lbs"
        )
        onerm = crud.create_one_rm(session, test_user.id, onerm_data)
        
        assert onerm.movement == "squat"
        assert onerm.weight == 225.0
        assert onerm.user_id == test_user.id

    def test_get_user_one_rms(self, session, test_user):
        """Test getting all 1RMs for a user."""
        # Create multiple 1RMs
        movements = ["squat", "bench", "deadlift"]
        for movement in movements:
            onerm_data = OneRMCreate(movement=movement, weight=200.0, unit="lbs")
            crud.create_one_rm(session, test_user.id, onerm_data)
        
        one_rms = crud.get_user_one_rms(session, test_user.id)
        assert len(one_rms) == 3
        
        movement_names = [orm.movement for orm in one_rms]
        assert all(movement in movement_names for movement in movements)

    def test_get_one_rm(self, session, test_user):
        """Test getting a specific 1RM."""
        onerm_data = OneRMCreate(movement="squat", weight=225.0, unit="lbs")
        created_onerm = crud.create_one_rm(session, test_user.id, onerm_data)
        
        retrieved_onerm = crud.get_one_rm(session, test_user.id, "squat")
        assert retrieved_onerm is not None
        assert retrieved_onerm.id == created_onerm.id

    def test_update_one_rm(self, session, test_user):
        """Test updating a 1RM."""
        onerm_data = OneRMCreate(movement="squat", weight=225.0, unit="lbs")
        crud.create_one_rm(session, test_user.id, onerm_data)
        
        update_data = OneRMUpdate(weight=235.0)
        updated_onerm = crud.update_one_rm(session, test_user.id, "squat", update_data)
        
        assert updated_onerm is not None
        assert updated_onerm.weight == 235.0

    def test_delete_one_rm(self, session, test_user):
        """Test deleting a 1RM."""
        onerm_data = OneRMCreate(movement="squat", weight=225.0, unit="lbs")
        crud.create_one_rm(session, test_user.id, onerm_data)
        
        result = crud.delete_one_rm(session, test_user.id, "squat")
        assert result is True
        
        # Verify it's deleted
        retrieved_onerm = crud.get_one_rm(session, test_user.id, "squat")
        assert retrieved_onerm is None

    def test_update_one_rm_not_found(self, session, test_user):
        """Test updating a non-existent 1RM."""
        update_data = OneRMUpdate(weight=235.0)
        result = crud.update_one_rm(session, test_user.id, "nonexistent", update_data)
        assert result is None

    def test_delete_one_rm_not_found(self, session, test_user):
        """Test deleting a non-existent 1RM."""
        result = crud.delete_one_rm(session, test_user.id, "nonexistent")
        assert result is False


class TestWorkoutScheduleCRUD:
    def test_create_workout_schedule(self, session, test_user):
        """Test creating a workout schedule."""
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        schedule = crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        assert schedule.user_id == test_user.id
        assert len(schedule.day1_movements) == 2
        assert "squat" in schedule.day1_movements

    def test_get_user_workout_schedule(self, session, test_user):
        """Test retrieving a user's workout schedule."""
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        created_schedule = crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        retrieved_schedule = crud.get_user_workout_schedule(session, test_user.id)
        assert retrieved_schedule is not None
        assert retrieved_schedule.id == created_schedule.id

    def test_update_workout_schedule(self, session, test_user):
        """Test updating a workout schedule."""
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        update_data = WorkoutScheduleCreate(
            day1_movements=["bench", "overhead_press"],
            day2_movements=["squat", "deadlift"]
        )
        updated_schedule = crud.update_workout_schedule(session, test_user.id, update_data)
        
        assert updated_schedule is not None
        assert "bench" in updated_schedule.day1_movements

    def test_update_workout_schedule_not_found(self, session, test_user):
        """Test updating a non-existent workout schedule."""
        update_data = WorkoutScheduleCreate(
            day1_movements=["bench", "overhead_press"],
            day2_movements=["squat", "deadlift"]
        )
        result = crud.update_workout_schedule(session, test_user.id, update_data)
        assert result is None


class TestCycleCRUD:
    def test_create_cycle(self, session, test_user):
        """Test creating a cycle."""
        # First create a workout schedule
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        training_maxes = {
            "squat": 200.0,
            "bench": 150.0,
            "deadlift": 250.0,
            "overhead_press": 100.0
        }
        cycle_data = CycleCreate(
            cycle_number=1,
            training_maxes=training_maxes
        )
        cycle = crud.create_cycle(session, test_user.id, cycle_data)
        
        assert cycle.cycle_number == 1
        assert cycle.user_id == test_user.id
        assert cycle.is_active is True
        
        # Check that workouts were created
        workouts = crud.get_cycle_workouts(session, cycle.id)
        assert len(workouts) == 8  # 4 weeks × 2 days

    def test_get_active_cycle(self, session, test_user):
        """Test getting the active cycle."""
        # Create workout schedule first
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        training_maxes = {
            "squat": 200.0,
            "bench": 150.0, 
            "deadlift": 250.0,
            "overhead_press": 100.0
        }
        cycle_data = CycleCreate(cycle_number=1, training_maxes=training_maxes)
        created_cycle = crud.create_cycle(session, test_user.id, cycle_data)
        
        active_cycle = crud.get_active_cycle(session, test_user.id)
        assert active_cycle is not None
        assert active_cycle.id == created_cycle.id
        assert active_cycle.is_active is True

    def test_get_user_cycles(self, session, test_user):
        """Test getting all user cycles."""
        # Create workout schedule first
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        # Create multiple cycles
        for i in range(3):
            training_maxes = {"squat": 200.0, "bench": 150.0, "deadlift": 250.0, "overhead_press": 100.0}
            cycle_data = CycleCreate(cycle_number=i+1, training_maxes=training_maxes)
            crud.create_cycle(session, test_user.id, cycle_data)
        
        all_cycles = crud.get_user_cycles(session, test_user.id)
        active_cycles = crud.get_user_cycles(session, test_user.id, active_only=True)
        
        assert len(all_cycles) == 3
        assert len(active_cycles) >= 1  # At least the last one should be active


class TestWorkoutCRUD:
    def test_update_workout_sets(self, session, test_user):
        """Test updating workout sets."""
        # Create cycle with workouts
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        training_maxes = {"squat": 200.0, "bench": 150.0, "deadlift": 250.0, "overhead_press": 100.0}
        cycle_data = CycleCreate(cycle_number=1, training_maxes=training_maxes)
        cycle = crud.create_cycle(session, test_user.id, cycle_data)
        
        workouts = crud.get_cycle_workouts(session, cycle.id)
        workout = workouts[0]
        
        # Update sets data
        new_sets_data = {
            "squat": [
                {"percentage": 65, "reps": 5, "weight": 130.0, "completed_reps": 5, "actual_weight": 130.0}
            ]
        }
        updated_workout = crud.update_workout_sets(session, workout.id, new_sets_data)
        
        assert updated_workout is not None
        assert updated_workout.sets_reps_data == new_sets_data

    def test_update_workout_status(self, session, test_user):
        """Test updating workout status."""
        # Create cycle with workouts  
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        training_maxes = {"squat": 200.0, "bench": 150.0, "deadlift": 250.0, "overhead_press": 100.0}
        cycle_data = CycleCreate(cycle_number=1, training_maxes=training_maxes)
        cycle = crud.create_cycle(session, test_user.id, cycle_data)
        
        workouts = crud.get_cycle_workouts(session, cycle.id)
        workout = workouts[0]
        
        # Update status to in-progress
        updated_workout = crud.update_workout_status(session, workout.id, "in-progress")
        assert updated_workout.status == "in-progress"
        
        # Update status to completed
        updated_workout = crud.update_workout_status(session, workout.id, "completed")
        assert updated_workout.status == "completed"
        assert updated_workout.completed is True
        assert updated_workout.completed_at is not None

    def test_complete_workout(self, session, test_user):
        """Test completing a workout."""
        # Create cycle with workouts
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        crud.create_workout_schedule(session, test_user.id, schedule_data)
        
        training_maxes = {"squat": 200.0, "bench": 150.0, "deadlift": 250.0, "overhead_press": 100.0}
        cycle_data = CycleCreate(cycle_number=1, training_maxes=training_maxes)
        cycle = crud.create_cycle(session, test_user.id, cycle_data)
        
        workouts = crud.get_cycle_workouts(session, cycle.id)
        workout = workouts[0]
        
        completed_workout = crud.complete_workout(session, workout.id)
        assert completed_workout.completed is True
        assert completed_workout.status == "completed"
        assert completed_workout.completed_at is not None


class TestOnboardingCRUD:
    def test_complete_onboarding(self, session, test_user):
        """Test completing user onboarding."""
        onboarding_data = OnboardingData(
            squat=200.0,
            bench=150.0,
            deadlift=250.0,
            overhead_press=100.0,
            unit="lbs",
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        
        result = crud.complete_onboarding(session, test_user.id, onboarding_data)
        
        # Check that 1RMs were created
        assert len(result["one_rms"]) == 4
        
        # Check that workout schedule was created
        assert result["workout_schedule"] is not None
        assert len(result["workout_schedule"].day1_movements) == 2
        
        # Check that first cycle was created
        assert result["cycle"] is not None
        assert result["cycle"].cycle_number == 1
        
        # Check that user is marked as onboarded
        updated_user = crud.get_user(session, test_user.id)
        assert updated_user.is_onboarded is True