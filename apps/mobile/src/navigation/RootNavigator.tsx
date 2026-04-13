import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ActivityIndicator, View } from 'react-native';
import { useAuth } from '@/lib/auth';
import { colors } from '@/theme';

import { LoginScreen } from '@/screens/LoginScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { ReceiptCaptureScreen } from '@/screens/ReceiptCaptureScreen';
import { TimesheetScreen } from '@/screens/TimesheetScreen';
import { PayslipsScreen } from '@/screens/PayslipsScreen';
import { LeaveRequestScreen } from '@/screens/LeaveRequestScreen';
import { ManagerApprovalsScreen } from '@/screens/ManagerApprovalsScreen';

export type RootStackParamList = {
  Login: undefined;
  Home: undefined;
  ReceiptCapture: undefined;
  Timesheet: undefined;
  Payslips: undefined;
  LeaveRequest: undefined;
  ManagerApprovals: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      {isAuthenticated ? (
        <>
          <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'ClaudERP' }} />
          <Stack.Screen
            name="ReceiptCapture"
            component={ReceiptCaptureScreen}
            options={{ title: 'New Expense' }}
          />
          <Stack.Screen
            name="Timesheet"
            component={TimesheetScreen}
            options={{ title: 'Timesheet' }}
          />
          <Stack.Screen
            name="Payslips"
            component={PayslipsScreen}
            options={{ title: 'Payslips' }}
          />
          <Stack.Screen
            name="LeaveRequest"
            component={LeaveRequestScreen}
            options={{ title: 'Request Leave' }}
          />
          <Stack.Screen
            name="ManagerApprovals"
            component={ManagerApprovalsScreen}
            options={{ title: 'Approvals' }}
          />
        </>
      ) : (
        <Stack.Screen
          name="Login"
          component={LoginScreen}
          options={{ headerShown: false }}
        />
      )}
    </Stack.Navigator>
  );
}
