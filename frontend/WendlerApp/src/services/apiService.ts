import { Storage } from '../utils/storage';

// Use environment variable or fallback to localhost for development
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export interface User {
  id: number;
  oauth_id: string;
  email: string;
  name: string;
  provider: string;
  is_onboarded: boolean;
  created_at: string;
  updated_at?: string;
  one_rms: OneRM[];
}

export interface OneRM {
  id: number;
  user_id: number;
  movement: string;
  weight: number;
  unit: string;
  created_at: string;
  updated_at?: string;
}

export interface OnboardingData {
  squat: number;
  bench: number;
  deadlift: number;
  overhead_press: number;
  unit: string;
  day1_movements: string[];
  day2_movements: string[];
}

export interface WorkoutSchedule {
  id: number;
  user_id: number;
  day1_movements: string[];
  day2_movements: string[];
  created_at: string;
  updated_at?: string;
}

export interface SetData {
  percentage: number;
  reps: string | number;
  weight: number;
  completed_reps?: number;
}

export interface WorkoutData {
  id?: number;
  week: number;
  day: number;
  movements: string[];
  sets: Record<string, SetData[]>;
  status?: string;
  completed?: boolean;
}

export interface Cycle {
  id: number;
  user_id: number;
  cycle_number: number;
  start_date: string;
  is_active: boolean;
  training_maxes: Record<string, number>;
  created_at: string;
}

export interface CycleWithWorkouts extends Cycle {
  workouts: WorkoutData[];
  week_dates?: Record<number, {
    start: string;
    end: string;
    start_date: string;
    end_date: string;
  }>;
}

export interface AdminStats {
  totalUsers: number;
  activeCycles: number;
  totalCycles: number;
  lastWeekNewUsers: number;
}

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  provider: string;
  is_onboarded: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AdminCycle {
  id: number;
  cycle_number: number;
  start_date: string;
  is_active: boolean;
  training_maxes: Record<string, number>;
  created_at: string;
  user?: {
    id: number;
    name: string;
    email: string;
  };
}

export interface AdminUserDetail extends AdminUser {
  oauth_id: string;
  one_rms: OneRM[];
  workout_schedule?: WorkoutSchedule;
  cycles: Cycle[];
}

export interface ExportResponse {
  message: string;
  export_type: string;
  timestamp: string;
  note: string;
}

export class ApiService {
  private static async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await Storage.getItem('jwt_token');
    if (!token) {
      throw new Error('No auth token found');
    }
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  static async getCurrentUser(): Promise<User> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/me`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting current user:', error);
      throw error;
    }
  }

  static async getOneRMs(): Promise<OneRM[]> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/one-rms`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting 1RMs:', error);
      throw error;
    }
  }

  static async getOneRM(movement: string): Promise<OneRM> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/one-rms/${movement}`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error getting ${movement} 1RM:`, error);
      throw error;
    }
  }

  static async createOneRM(data: { movement: string; weight: number; unit: string }): Promise<OneRM> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/one-rms`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating 1RM:', error);
      throw error;
    }
  }

  static async updateOneRM(movement: string, data: { weight?: number; unit?: string }): Promise<OneRM> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/one-rms/${movement}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error updating ${movement} 1RM:`, error);
      throw error;
    }
  }

  static async deleteOneRM(movement: string): Promise<void> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/one-rms/${movement}`, {
        method: 'DELETE',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error deleting ${movement} 1RM:`, error);
      throw error;
    }
  }

  static async completeOnboarding(data: OnboardingData): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/onboarding`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error completing onboarding:', error);
      throw error;
    }
  }

  // Workout Schedule endpoints
  static async getWorkoutSchedule(): Promise<WorkoutSchedule> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/workout-schedule`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting workout schedule:', error);
      throw error;
    }
  }

  static async createWorkoutSchedule(data: { day1_movements: string[]; day2_movements: string[] }): Promise<WorkoutSchedule> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/workout-schedule`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating workout schedule:', error);
      throw error;
    }
  }

  // Cycle endpoints
  static async getCycles(activeOnly: boolean = false): Promise<Cycle[]> {
    try {
      const headers = await this.getAuthHeaders();
      const url = `${BACKEND_URL}/cycles${activeOnly ? '?active_only=true' : ''}`;
      const response = await fetch(url, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting cycles:', error);
      throw error;
    }
  }

  static async getActiveCycle(): Promise<CycleWithWorkouts> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/cycles/active`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting active cycle:', error);
      throw error;
    }
  }

  static async getCycle(cycleId: number): Promise<CycleWithWorkouts> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/cycles/${cycleId}`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting cycle:', error);
      throw error;
    }
  }

  static async createNextCycle(): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/cycles/next`, {
        method: 'POST',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating next cycle:', error);
      throw error;
    }
  }

  static async updateCycle(cycleId: number, updateData: { start_date?: string }): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/cycles/${cycleId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(updateData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating cycle:', error);
      throw error;
    }
  }

  static async updateWorkoutSets(workoutId: number, setsData: Record<string, SetData[]>): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/workouts/${workoutId}/sets`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(setsData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating workout sets:', error);
      throw error;
    }
  }

  static async completeWorkout(workoutId: number): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/workouts/${workoutId}/complete`, {
        method: 'POST',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error completing workout:', error);
      throw error;
    }
  }

  static async updateWorkoutStatus(workoutId: number, status: string): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/workouts/${workoutId}/status`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ status }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating workout status:', error);
      throw error;
    }
  }

  // Admin endpoints
  static async getAdminStats(): Promise<AdminStats> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/admin/stats`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting admin stats:', error);
      throw error;
    }
  }

  static async getAdminUsers(limit: number = 100, offset: number = 0): Promise<AdminUser[]> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/admin/users?limit=${limit}&offset=${offset}`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting admin users:', error);
      throw error;
    }
  }

  static async getAdminCycles(limit: number = 100, offset: number = 0): Promise<AdminCycle[]> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/admin/cycles?limit=${limit}&offset=${offset}`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting admin cycles:', error);
      throw error;
    }
  }

  static async getAdminUserDetail(userId: number): Promise<AdminUserDetail> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/admin/users/${userId}`, { headers });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting admin user detail:', error);
      throw error;
    }
  }

  static async exportAdminData(exportType: string = 'users'): Promise<ExportResponse> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${BACKEND_URL}/admin/export?export_type=${exportType}`, {
        method: 'POST',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error exporting admin data:', error);
      throw error;
    }
  }
}