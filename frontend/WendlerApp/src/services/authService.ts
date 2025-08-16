import { Storage } from '../utils/storage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const TOKEN_KEY = 'jwt_token';

export interface User {
  id: string;
  email: string;
  name: string;
  provider: string;
}

export class AuthService {
  static async loginWithGoogle(): Promise<string> {
    // For web, we'll open a popup window
    if (typeof window !== 'undefined') {
      const authUrl = `${BACKEND_URL}/auth/google`;
      
      // Open popup window
      const popup = window.open(authUrl, 'google-auth', 'width=500,height=600,scrollbars=yes,resizable=yes');
      
      if (!popup) {
        throw new Error('Popup blocked');
      }
      
      return new Promise((resolve, reject) => {
        // Set a timeout for the auth process (5 minutes)
        const timeout = setTimeout(() => {
          window.removeEventListener('message', messageListener);
          reject(new Error('Auth timeout'));
        }, 5 * 60 * 1000);
        
        // Listen for postMessage from popup
        const messageListener = (event: MessageEvent) => {
          if (event.origin !== BACKEND_URL) return;
          
          clearTimeout(timeout);
          window.removeEventListener('message', messageListener);
          
          if (event.data.access_token) {
            resolve(event.data.access_token);
          } else {
            reject(new Error('Auth failed'));
          }
        };
        
        window.addEventListener('message', messageListener);
      });
    }
    
    throw new Error('Platform not supported');
  }

  static async storeToken(token: string): Promise<void> {
    await Storage.setItem(TOKEN_KEY, token);
  }

  static async getToken(): Promise<string | null> {
    return await Storage.getItem(TOKEN_KEY);
  }

  static async removeToken(): Promise<void> {
    await Storage.removeItem(TOKEN_KEY);
  }

  static async getCurrentUser(): Promise<User | null> {
    try {
      const token = await this.getToken();
      if (!token) return null;

      const response = await fetch(`${BACKEND_URL}/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        return await response.json();
      }
      
      return null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  static async logout(): Promise<void> {
    await this.removeToken();
  }
}