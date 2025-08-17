"""
Tests for movement selection API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestMovementsAPI:
    def test_get_day2_movements_squat_bench(self):
        """Test getting day 2 movements when day 1 has squat and bench."""
        response = client.get("/movements/day2?day1_movements=squat,bench")
        assert response.status_code == 200
        data = response.json()
        assert data["day1_movements"] == ["squat", "bench"]
        assert set(data["day2_movements"]) == {"deadlift", "overhead_press"}
    
    def test_get_day2_movements_deadlift_overhead(self):
        """Test getting day 2 movements when day 1 has deadlift and overhead press."""
        response = client.get("/movements/day2?day1_movements=deadlift,overhead_press")
        assert response.status_code == 200
        data = response.json()
        assert data["day1_movements"] == ["deadlift", "overhead_press"]
        assert set(data["day2_movements"]) == {"squat", "bench"}
    
    def test_get_day2_movements_with_spaces(self):
        """Test getting day 2 movements with spaces in the input."""
        response = client.get("/movements/day2?day1_movements=squat, bench")
        assert response.status_code == 200
        data = response.json()
        assert data["day1_movements"] == ["squat", "bench"]
        assert set(data["day2_movements"]) == {"deadlift", "overhead_press"}
    
    def test_get_day2_movements_invalid_count(self):
        """Test error when day 1 doesn't have exactly 2 movements."""
        response = client.get("/movements/day2?day1_movements=squat")
        assert response.status_code == 400
        assert "exactly 2 movements" in response.json()["detail"]
        
        response = client.get("/movements/day2?day1_movements=squat,bench,deadlift")
        assert response.status_code == 400
        assert "exactly 2 movements" in response.json()["detail"]
    
    def test_get_day2_movements_invalid_movement(self):
        """Test error when day 1 has invalid movement."""
        response = client.get("/movements/day2?day1_movements=squat,bicep_curl")
        assert response.status_code == 400
        assert "Invalid movement" in response.json()["detail"]
    
    def test_get_day2_movements_invalid_format(self):
        """Test error when day1_movements parameter is malformed."""
        response = client.get("/movements/day2?day1_movements=")
        assert response.status_code == 400
        assert "exactly 2 movements" in response.json()["detail"]