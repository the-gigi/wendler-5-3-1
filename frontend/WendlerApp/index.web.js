import {AppRegistry} from 'react-native';
import App from './App';
import {name as appName} from './app.json';

// Register the main component
AppRegistry.registerComponent(appName, () => App);

// Run the app in the browser
AppRegistry.runApplication(appName, {
  initialProps: {},
  rootTag: document.getElementById('app-root'),
});