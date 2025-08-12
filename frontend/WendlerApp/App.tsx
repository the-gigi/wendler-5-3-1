import React from 'react';
import { StatusBar, StyleSheet, useColorScheme, View } from 'react-native';
import { AuthProvider } from './src/context/AuthContext';
import { MainScreen } from './src/screens/MainScreen';

function App() {
  const isDarkMode = useColorScheme() === 'dark';

  return (
    <AuthProvider>
      <View style={styles.container}>
        <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
        <MainScreen />
      </View>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;
