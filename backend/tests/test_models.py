"""
Tests for SQLModel models and validation.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models import (
    User, UserCreate, UserUpdate,
    OneRM, OneRMCreate, OneRMUpdate,
    WorkoutSchedule, WorkoutScheduleCreate,
    Cycle, CycleCreate,
    Workout, WorkoutRead, WorkoutStatusUpdate,
    OnboardingData,
    WORKOUT_STATUSES
)


class TestUserModels:
    def test_user_create_valid(self):
        """Test creating a valid user."""
        user_data = UserCreate(
            oauth_id="test_oauth_id",
            email="test@example.com",
            name="Test User",
            provider="google"
        )
        assert user_data.oauth_id == "test_oauth_id"
        assert user_data.email == "test@example.com"
        assert user_data.is_onboarded is False

    def test_user_update(self):
        """Test user update model."""
        update_data = UserUpdate(name="Updated Name", is_onboarded=True)
        assert update_data.name == "Updated Name"
        assert update_data.is_onboarded is True


class TestOneRMModels:
    def test_onerm_create_valid(self):
        """Test creating a valid 1RM."""
        onerm_data = OneRMCreate(
            movement="squat",
            weight=225.0,
            unit="lbs"
        )
        assert onerm_data.movement == "squat"
        assert onerm_data.weight == 225.0

    def test_onerm_invalid_movement(self):
        """Test 1RM with invalid movement."""
        with pytest.raises(ValidationError):
            OneRMCreate(
                movement="invalid_movement",
                weight=225.0,
                unit="lbs"
            )

    def test_onerm_invalid_weight(self):
        """Test 1RM with invalid weight."""
        with pytest.raises(ValidationError):
            OneRMCreate(
                movement="squat",
                weight=-10.0,  # Negative weight should be invalid
                unit="lbs"
            )

    def test_onerm_invalid_unit(self):
        """Test 1RM with invalid unit."""
        with pytest.raises(ValidationError):
            OneRMCreate(
                movement="squat",
                weight=225.0,
                unit="stones"  # Invalid unit
            )

    def test_onerm_update_valid(self):
        """Test valid 1RM update."""
        update_data = OneRMUpdate(weight=235.0, unit="kg")
        assert update_data.weight == 235.0
        assert update_data.unit == "kg"

    def test_onerm_update_invalid_weight(self):
        """Test 1RM update with invalid weight."""
        with pytest.raises(ValidationError):
            OneRMUpdate(weight=0.0)


class TestWorkoutScheduleModels:
    def test_workout_schedule_valid(self):
        """Test creating a valid workout schedule."""
        schedule_data = WorkoutScheduleCreate(
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        assert len(schedule_data.day1_movements) == 2
        assert "squat" in schedule_data.day1_movements

    def test_workout_schedule_invalid_movement_count(self):
        """Test workout schedule with wrong number of movements."""
        with pytest.raises(ValidationError):
            WorkoutScheduleCreate(
                day1_movements=["squat"],  # Only 1 movement
                day2_movements=["bench", "deadlift"]
            )

    def test_workout_schedule_invalid_movement(self):
        """Test workout schedule with invalid movement."""
        with pytest.raises(ValidationError):
            WorkoutScheduleCreate(
                day1_movements=["squat", "invalid_movement"],
                day2_movements=["bench", "deadlift"]
            )

    def test_workout_schedule_squat_deadlift_same_day(self):
        """Test workout schedule with squat and deadlift on same day."""
        with pytest.raises(ValidationError):
            WorkoutScheduleCreate(
                day1_movements=["squat", "deadlift"],  # Not recommended
                day2_movements=["bench", "overhead_press"]
            )


class TestCycleModels:
    def test_cycle_create_valid(self):
        """Test creating a valid cycle."""
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
        assert cycle_data.cycle_number == 1
        assert cycle_data.training_maxes["squat"] == 200.0


class TestWorkoutModels:
    def test_workout_status_update_valid(self):
        """Test valid workout status update."""
        for status in WORKOUT_STATUSES:
            status_update = WorkoutStatusUpdate(status=status)
            assert status_update.status == status

    def test_workout_status_update_invalid(self):
        """Test invalid workout status update."""
        with pytest.raises(ValidationError):
            WorkoutStatusUpdate(status="invalid_status")

    def test_workout_read_structure(self):
        """Test workout read model structure."""
        sets_data = {
            "squat": [
                {"percentage": 65, "reps": 5, "weight": 130.0}
            ]
        }
        workout_data = WorkoutRead(
            id=1,
            cycle_id=1,
            week=1,
            day=1,
            movements=["squat", "overhead_press"],
            sets=sets_data,
            status="not-started",
            completed=False,
            created_at=datetime.now(timezone.utc)
        )
        assert workout_data.week == 1
        assert workout_data.status == "not-started"
        assert len(workout_data.movements) == 2


class TestOnboardingData:
    def test_onboarding_data_valid(self):
        """Test valid onboarding data."""
        onboarding_data = OnboardingData(
            squat=200.0,
            bench=150.0,
            deadlift=250.0,
            overhead_press=100.0,
            unit="lbs",
            day1_movements=["squat", "overhead_press"],
            day2_movements=["bench", "deadlift"]
        )
        assert onboarding_data.squat == 200.0
        assert onboarding_data.unit == "lbs"
        assert onboarding_data.day1_movements == ["squat", "overhead_press"]
        assert onboarding_data.day2_movements == ["bench", "deadlift"]
    
    def test_onboarding_data_auto_calculate_day2(self):
        """Test auto-calculation of day2_movements when not provided."""
        onboarding_data = OnboardingData(
            squat=200.0,
            bench=150.0,
            deadlift=250.0,
            overhead_press=100.0,
            unit="lbs",
            day1_movements=["squat", "overhead_press"]
            # day2_movements not provided - should be auto-calculated
        )
        assert onboarding_data.day1_movements == ["squat", "overhead_press"]
        assert onboarding_data.day2_movements == ["bench", "deadlift"]

    def test_onboarding_data_invalid_weights(self):
        """Test onboarding data with invalid weights."""
        with pytest.raises(ValidationError):
            OnboardingData(
                squat=-200.0,  # Negative weight
                bench=150.0,
                deadlift=250.0,
                overhead_press=100.0,
                unit="lbs",
                day1_movements=["squat", "overhead_press"],
                day2_movements=["bench", "deadlift"]
            )

    def test_onboarding_data_invalid_unit(self):
        """Test onboarding data with invalid unit."""
        with pytest.raises(ValidationError):
            OnboardingData(
                squat=200.0,
                bench=150.0,
                deadlift=250.0,
                overhead_press=100.0,
                unit="stones",  # Invalid unit
                day1_movements=["squat", "overhead_press"],
                day2_movements=["bench", "deadlift"]
            )

    def test_onboarding_data_invalid_movements(self):
        """Test onboarding data with invalid movements."""
        with pytest.raises(ValidationError):
            OnboardingData(
                squat=200.0,
                bench=150.0,
                deadlift=250.0,
                overhead_press=100.0,
                unit="lbs",
                day1_movements=["squat"],  # Wrong number of movements
                day2_movements=["bench", "deadlift"]
            )