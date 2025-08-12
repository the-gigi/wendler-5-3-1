# Wendler 5-3-1 Frontend

React Native frontend for the Wendler 5-3-1 workout tracking application. Built with React Native Web for cross-platform support (web, iOS, Android).

## Features

- **Cross-Platform**: Runs on web, iOS, and Android from single codebase
- **OAuth Authentication**: Social login with Google, GitHub, Facebook
- **Onboarding Flow**: New user setup with 1RM entry for 4 main lifts
- **User Dashboard**: View saved 1RM records and workout progress
- **Responsive Design**: Optimized for both mobile and web interfaces

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### First Time Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure backend URL** (if needed):
   Edit `src/services/authService.ts` and `src/services/apiService.ts`:
   ```typescript
   const BACKEND_URL = 'http://localhost:8000'; // Change if backend runs elsewhere
   ```

## Running

### Web Development
```bash
npm run web
```
Opens at `http://localhost:3000`

### React Native (Mobile)
First, make sure you have React Native development environment set up:
- [React Native CLI Quickstart](https://reactnative.dev/docs/environment-setup)

#### iOS (macOS only):
```bash
npm run ios
```

#### Android:
```bash
npm run android
```

### Other Commands
- `npm run start` - Start Metro bundler
- `npm run lint` - Run ESLint
- `npm test` - Run tests
- `npm run build:web` - Build for web production

## Project Structure

```
frontend/WendlerApp/
├── App.tsx                           # Main app component
├── src/
│   ├── components/                   # Reusable UI components
│   ├── context/
│   │   └── AuthContext.tsx          # Authentication state management
│   ├── screens/
│   │   ├── MainScreen.tsx           # Main dashboard
│   │   └── OnboardingScreen.tsx     # 1RM setup for new users
│   ├── services/
│   │   ├── authService.ts           # OAuth authentication logic
│   │   └── apiService.ts            # Backend API communication
│   └── utils/
│       └── storage.ts               # Cross-platform storage utilities
├── public/                          # Web-specific assets
├── webpack.config.js                # Web bundling configuration
├── babel.config.js                  # Babel configuration
└── metro.config.js                  # React Native bundler config
```

## User Flow

1. **Login**: User clicks "Login with Google" and authenticates via OAuth
2. **Onboarding**: New users enter their 1RM for:
   - Squat
   - Bench Press
   - Deadlift
   - Overhead Press
3. **Dashboard**: Returning users see their saved 1RM records
4. **Future**: Workout tracking and progression features

## Platform-Specific Notes

### Web
- Uses localStorage for token storage
- Handles OAuth popup flow
- Responsive design for desktop/mobile browsers

### Mobile (Coming Soon)
- Uses AsyncStorage for token storage
- Native OAuth integration
- Touch-optimized interface

## Configuration

The app automatically detects the platform and adjusts behavior:

- **Web**: Uses localStorage, popup OAuth flow
- **Mobile**: Uses AsyncStorage, in-app browser OAuth

Backend URL is configured in the service files and can be changed for different environments (development, staging, production).

## Development

### Adding New Screens
1. Create new component in `src/screens/`
2. Add navigation logic to `MainScreen.tsx`
3. Update authentication flow in `AuthContext.tsx` if needed

### API Integration
All backend communication goes through `src/services/apiService.ts`. Add new endpoints here following the existing pattern.

### Styling
Uses React Native StyleSheet for cross-platform styling. Styles are defined at the bottom of each component file.

---

*For original React Native setup instructions, see [README.react.md](README.react.md)*