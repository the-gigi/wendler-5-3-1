"""
Tests for Wendler 5-3-1 business logic and calculations.
"""
import pytest
from datetime import datetime, timedelta

from wendler_service import WendlerService
from models import WEEKLY_TEMPLATES


class TestTrainingMaxCalculations:
    def test_calculate_training_max(self):
        """Test calculating training max from 1RM."""
        # Default 90% of 1RM
        tm = WendlerService.calculate_training_max(200.0)
        assert tm == 180.0  # 200 * 0.9
        
        # Custom percentage
        tm = WendlerService.calculate_training_max(200.0, 0.85)
        assert tm == 170.0  # 200 * 0.85

    def test_generate_training_maxes(self):
        """Test generating training maxes from 1RMs."""
        one_rms = {
            "squat": 200.0,
            "bench": 150.0,
            "deadlift": 250.0,
            "overhead_press": 100.0
        }
        
        training_maxes = WendlerService.generate_training_maxes(one_rms)
        
        # Training maxes should be 90% of 1RM
        assert training_maxes["squat"] == 180.0  # 200 * 0.9
        assert training_maxes["bench"] == 135.0  # 150 * 0.9
        assert training_maxes["deadlift"] == 225.0  # 250 * 0.9
        assert training_maxes["overhead_press"] == 90.0  # 100 * 0.9

    def test_progress_training_maxes(self):
        """Test progressing training maxes for next cycle."""
        current_maxes = {
            "squat": 180.0,
            "bench": 135.0,
            "deadlift": 225.0,
            "overhead_press": 90.0
        }
        
        new_maxes = WendlerService.progress_training_maxes(current_maxes)
        
        # Lower body should increase by 10 lbs, upper body by 5 lbs
        assert new_maxes["squat"] == 190.0  # 180 + 10
        assert new_maxes["deadlift"] == 235.0  # 225 + 10
        assert new_maxes["bench"] == 140.0  # 135 + 5
        assert new_maxes["overhead_press"] == 95.0  # 90 + 5

    def test_calculate_weight(self):
        """Test calculating working weights from percentages."""
        training_max = 180.0
        
        # Week 1: 65%, 75%, 85%
        weight_65 = WendlerService.calculate_weight(training_max, 65)
        weight_75 = WendlerService.calculate_weight(training_max, 75)
        weight_85 = WendlerService.calculate_weight(training_max, 85)
        
        # Should round to nearest 5 lbs
        assert weight_65 == 115.0  # 180 * 0.65 = 117, rounded to 115
        assert weight_75 == 135.0  # 180 * 0.75 = 135
        assert weight_85 == 155.0  # 180 * 0.85 = 153, rounded to 155

    def test_calculate_weight_rounding(self):
        """Test that working weights are rounded to nearest 5 lbs."""
        training_max = 183.0  # Odd number to test rounding
        
        weight_65 = WendlerService.calculate_weight(training_max, 65)
        # 183 * 0.65 = 118.95, should round to 120.0
        assert weight_65 == 120.0


class TestWeekTemplates:
    def test_weekly_templates_structure(self):
        """Test that weekly templates are structured correctly."""
        # Week 1: 5+ Week
        week1 = WEEKLY_TEMPLATES[1]
        expected_week1 = [
            {"percentage": 65, "reps": 5},
            {"percentage": 75, "reps": 5},
            {"percentage": 85, "reps": "5+"}
        ]
        assert week1 == expected_week1

        # Week 2: 3+ Week
        week2 = WEEKLY_TEMPLATES[2]
        expected_week2 = [
            {"percentage": 70, "reps": 3},
            {"percentage": 80, "reps": 3},
            {"percentage": 90, "reps": "3+"}
        ]
        assert week2 == expected_week2

        # Week 3: 5/3/1+ Week
        week3 = WEEKLY_TEMPLATES[3]
        expected_week3 = [
            {"percentage": 75, "reps": 5},
            {"percentage": 85, "reps": 3},
            {"percentage": 95, "reps": "1+"}
        ]
        assert week3 == expected_week3

        # Week 4: Deload Week
        week4 = WEEKLY_TEMPLATES[4]
        expected_week4 = [
            {"percentage": 40, "reps": 5},
            {"percentage": 50, "reps": 5},
            {"percentage": 60, "reps": 5}
        ]
        assert week4 == expected_week4


class TestWorkoutGeneration:
    def test_generate_cycle_workouts(self):
        """Test generating all workouts for a cycle."""
        training_maxes = {
            "squat": 180.0,
            "bench": 135.0,
            "deadlift": 225.0,
            "overhead_press": 90.0
        }
        workout_schedule = {
            "day1_movements": ["squat", "overhead_press"],
            "day2_movements": ["bench", "deadlift"]
        }
        
        workouts = WendlerService.generate_cycle_workouts(training_maxes, workout_schedule)
        
        # Should generate 8 workouts (4 weeks × 2 days)
        assert len(workouts) == 8
        
        # Check first workout (Week 1, Day 1)
        workout1 = workouts[0]
        assert workout1["week"] == 1
        assert workout1["day"] == 1
        assert workout1["movements"] == ["squat", "overhead_press"]
        assert "squat" in workout1["sets"]
        assert "overhead_press" in workout1["sets"]
        
        # Check that sets are generated correctly
        squat_sets = workout1["sets"]["squat"]
        assert len(squat_sets) == 6  # 3 warmup + 3 working sets per movement
        
        # Check warmup sets
        assert squat_sets[0]["type"] == "warmup"
        assert squat_sets[0]["percentage"] == 0
        assert squat_sets[0]["weight"] == 45  # Empty bar
        assert squat_sets[1]["type"] == "warmup"
        assert squat_sets[1]["percentage"] == 40
        assert squat_sets[2]["type"] == "warmup"
        assert squat_sets[2]["percentage"] == 60
        
        # Check working sets
        assert squat_sets[3]["type"] == "working"
        assert squat_sets[3]["percentage"] == 65
        assert squat_sets[3]["reps"] == 5
        assert squat_sets[5]["reps"] == "5+"  # AMRAP set
        
        # Check last workout (Week 4, Day 2)
        workout8 = workouts[7]
        assert workout8["week"] == 4
        assert workout8["day"] == 2
        assert workout8["movements"] == ["bench", "deadlift"]


class TestUtilityMethods:
    def test_format_movement_name(self):
        """Test formatting movement names for display."""
        assert WendlerService.format_movement_name("overhead_press") == "Overhead Press"
        assert WendlerService.format_movement_name("squat") == "Squat"
        assert WendlerService.format_movement_name("bench_press") == "Bench Press"

    def test_get_cycle_summary(self):
        """Test getting cycle summary information."""
        cycle_data = {
            "workouts": [
                {"week": 1, "day": 1, "completed": True},
                {"week": 1, "day": 2, "completed": True},
                {"week": 2, "day": 1, "completed": False},
                {"week": 2, "day": 2, "completed": False},
            ]
        }
        
        summary = WendlerService.get_cycle_summary(cycle_data)
        
        assert summary["total_workouts"] == 4
        assert summary["completed_workouts"] == 2
        assert summary["completion_percentage"] == 50.0
        assert summary["current_week"] == 2  # First incomplete week
        assert summary["is_deload_week"] is False

    def test_get_current_week(self):
        """Test determining current week from workout completion."""
        workouts = [
            {"week": 1, "completed": True},
            {"week": 1, "completed": True},
            {"week": 2, "completed": False},
            {"week": 2, "completed": False},
        ]
        
        current_week = WendlerService._get_current_week(workouts)
        assert current_week == 2  # First week with incomplete workouts

    def test_get_current_week_all_completed(self):
        """Test determining current week when all workouts completed."""
        workouts = [
            {"week": 1, "completed": True},
            {"week": 1, "completed": True},
            {"week": 2, "completed": True},
            {"week": 2, "completed": True},
            {"week": 3, "completed": True},
            {"week": 3, "completed": True},
            {"week": 4, "completed": True},
            {"week": 4, "completed": True},
        ]
        
        current_week = WendlerService._get_current_week(workouts)
        assert current_week == 4  # All weeks completed, return week 4

    def test_is_deload_week(self):
        """Test checking if currently in deload week."""
        # Week 3 workouts
        workouts = [
            {"week": 1, "completed": True},
            {"week": 2, "completed": True},
            {"week": 3, "completed": True},
            {"week": 4, "completed": False},  # Week 4 not completed
        ]
        
        is_deload = WendlerService._is_deload_week(workouts)
        assert is_deload is True  # Currently in week 4 (deload)


class TestDateCalculations:
    def test_get_week_dates(self):
        """Test getting week date ranges for a cycle."""
        # Use a known date for consistent testing
        start_date = datetime(2024, 1, 1)  # Monday
        
        week_dates = WendlerService.get_week_dates(start_date)
        
        # Should have 4 weeks
        assert len(week_dates) == 4
        
        # Check Week 1 dates
        week1 = week_dates[1]
        assert "start" in week1
        assert "end" in week1
        assert "start_date" in week1
        assert "end_date" in week1

    def test_get_week_dates_formatting(self):
        """Test that week dates are formatted correctly."""
        start_date = datetime(2024, 1, 1)
        week_dates = WendlerService.get_week_dates(start_date)
        
        week1 = week_dates[1]
        # Check that formatted dates are readable
        assert week1["start"] == "Jan 01"
        assert week1["end"] == "Jan 07"

    def test_get_week_dates_consecutive_weeks(self):
        """Test that weeks are consecutive with no gaps."""
        start_date = datetime(2024, 1, 1)
        week_dates = WendlerService.get_week_dates(start_date)
        
        # Week 2 should start the day after Week 1 ends
        week1_end_iso = week_dates[1]["end_date"]
        week2_start_iso = week_dates[2]["start_date"]
        
        week1_end = datetime.fromisoformat(week1_end_iso)
        week2_start = datetime.fromisoformat(week2_start_iso)
        
        assert week2_start == week1_end + timedelta(days=1)


class TestEdgeCases:
    def test_zero_training_max(self):
        """Test handling of zero training max."""
        training_maxes = {"squat": 0.0, "overhead_press": 90.0}
        workout_schedule = {
            "day1_movements": ["squat", "overhead_press"],
            "day2_movements": []
        }
        
        workouts = WendlerService.generate_cycle_workouts(training_maxes, workout_schedule)
        
        # Should handle gracefully, squat working sets would be 0 (except empty bar warmup)
        first_workout = workouts[0]
        squat_sets = first_workout["sets"]["squat"]
        
        # Warmup sets: empty bar stays 45, others are 0
        assert squat_sets[0]["weight"] == 45  # Empty bar
        assert squat_sets[1]["weight"] == 0.0  # 40% of 0 TM
        assert squat_sets[2]["weight"] == 0.0  # 60% of 0 TM
        
        # Working sets should all be 0
        assert all(set_data["weight"] == 0.0 for set_data in squat_sets[3:])

    def test_very_low_training_max_rounding(self):
        """Test rounding with very low training maxes."""
        # 10 lbs training max, 65% = 6.5 lbs, should round to 5
        weight = WendlerService.calculate_weight(10.0, 65)
        assert weight == 5.0  # Rounds to nearest 5 lbs

    def test_empty_cycle_data(self):
        """Test cycle summary with empty workout data."""
        cycle_data = {"workouts": []}
        summary = WendlerService.get_cycle_summary(cycle_data)
        
        assert summary["total_workouts"] == 0
        assert summary["completed_workouts"] == 0
        assert summary["completion_percentage"] == 0
        assert summary["current_week"] == 1  # Defaults to week 1