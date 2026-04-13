import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { AuthProvider } from '@/lib/auth';
import { RootNavigator } from '@/navigation/RootNavigator';

/**
 * ClaudERP mobile — entry component.
 *
 * Wraps the navigation tree in:
 *  - SafeAreaProvider  — respects notches and rounded corners
 *  - AuthProvider      — holds the JWT + user in AsyncStorage and
 *                        exposes signIn / signOut via React context
 *  - NavigationContainer — React Navigation's root
 *  - RootNavigator     — the actual screen tree
 */
export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <NavigationContainer>
          <StatusBar style="auto" />
          <RootNavigator />
        </NavigationContainer>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
