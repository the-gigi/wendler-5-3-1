from datetime import datetime, timedelta
import math
from models import WEEKLY_TEMPLATES

class WendlerService:
    """Service for generating Wendler 5/3/1 cycles and calculating training data"""
    
    @staticmethod
    def calculate_training_max(one_rm: float, percentage: float = 0.9) -> float:
        """Calculate training max (default 90% of 1RM)"""
        return one_rm * percentage  # Keep precise, no rounding
    
    @staticmethod
    def calculate_weight(training_max: float, percentage: int) -> float:
        """Calculate working weight based on training max and percentage"""
        weight = training_max * (percentage / 100)
        return round(weight / 5) * 5  # Round to nearest 5 lbs
    
    @staticmethod
    def generate_training_maxes(one_rms: dict[str, float]) -> dict[str, float]:
        """Generate training maxes for all movements from 1RMs"""
        return {
            movement: WendlerService.calculate_training_max(weight)
            for movement, weight in one_rms.items()
        }
    
    @staticmethod
    def generate_cycle_workouts(
        training_maxes: dict[str, float], 
        workout_schedule: dict[str, list[str]]
    ) -> list[dict]:
        """Generate all workouts for a 4-week cycle"""
        workouts = []
        
        # Generate workouts for all 4 weeks
        for week in range(1, 5):  # Weeks 1-4
            for day in [1, 2]:  # Days 1-2
                day_key = f"day{day}_movements"
                movements = workout_schedule[day_key]
                
                # Get the template for this week
                week_template = WEEKLY_TEMPLATES[week]
                
                # Generate sets data for each movement
                sets_data = {}
                for movement in movements:
                    movement_sets = []
                    tm = training_maxes[movement]
                    
                    # Generate warmup sets
                    warmup_sets = [
                        {"percentage": 0, "reps": 5, "weight": 45, "type": "warmup", "completed_reps": None, "notes": "Empty bar"},
                        {"percentage": 40, "reps": 5, "weight": WendlerService.calculate_weight(tm, 40), "type": "warmup", "completed_reps": None, "notes": "40% TM"},
                        {"percentage": 60, "reps": 3, "weight": WendlerService.calculate_weight(tm, 60), "type": "warmup", "completed_reps": None, "notes": "60% TM"}
                    ]
                    
                    # Add warmup sets first
                    movement_sets.extend(warmup_sets)
                    
                    # Generate 3 working sets based on template
                    for set_template in week_template:
                        weight = WendlerService.calculate_weight(tm, set_template["percentage"])
                        movement_sets.append({
                            "percentage": set_template["percentage"],
                            "reps": set_template["reps"],
                            "weight": weight,
                            "type": "working",
                            "completed_reps": None,
                            "notes": None
                        })
                    
                    sets_data[movement] = movement_sets
                
                workouts.append({
                    "week": week,
                    "day": day,
                    "movements": movements,
                    "sets": sets_data,
                    "completed": False,
                    "completed_at": None
                })
        
        return workouts
    
    @staticmethod
    def progress_training_maxes(current_maxes: dict[str, float]) -> dict[str, float]:
        """Progress training maxes for next cycle"""
        # Upper body: +5 lbs, Lower body: +10 lbs
        progression = {
            "bench": 5,
            "overhead_press": 5,
            "squat": 10,
            "deadlift": 10
        }
        
        return {
            movement: current_max + progression[movement]
            for movement, current_max in current_maxes.items()
        }
    
    @staticmethod
    def format_movement_name(movement: str) -> str:
        """Format movement name for display"""
        return movement.replace('_', ' ').title()
    
    @staticmethod
    def get_cycle_summary(cycle_data: dict) -> dict:
        """Get summary information for a cycle"""
        total_workouts = len(cycle_data.get('workouts', []))
        completed_workouts = sum(1 for w in cycle_data.get('workouts', []) if w.get('completed', False))
        
        return {
            "total_workouts": total_workouts,
            "completed_workouts": completed_workouts,
            "completion_percentage": (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0,
            "current_week": WendlerService._get_current_week(cycle_data.get('workouts', [])),
            "is_deload_week": WendlerService._is_deload_week(cycle_data.get('workouts', []))
        }
    
    @staticmethod
    def _get_current_week(workouts: list[dict]) -> int:
        """Determine current week based on completed workouts"""
        completed_weeks = set()
        for workout in workouts:
            if workout.get('completed', False):
                completed_weeks.add(workout['week'])
        
        # Find the first incomplete week
        for week in range(1, 5):
            if week not in completed_weeks:
                return week
        
        return 4  # All weeks completed
    
    @staticmethod
    def _is_deload_week(workouts: list[dict]) -> bool:
        """Check if currently in deload week (week 4)"""
        current_week = WendlerService._get_current_week(workouts)
        return current_week == 4
    
    @staticmethod
    def get_week_dates(cycle_start_date: datetime) -> dict[int, dict[str, str]]:
        """Get start and end dates for each week in the cycle"""
        week_dates = {}
        for week in range(1, 5):
            week_start = cycle_start_date + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            week_dates[week] = {
                "start": week_start.strftime("%b %d"),
                "end": week_end.strftime("%b %d"),
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat()
            }
        return week_dates