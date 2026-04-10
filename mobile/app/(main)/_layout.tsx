import React from 'react';
import { Tabs } from 'expo-router';
import { Text, StyleSheet } from 'react-native';

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  const icons: Record<string, string> = {
    Dashboard: '\u2302',
    Expenses: '\u2B24',
    Timesheet: '\u23F1',
    Payslips: '\u2B24',
    Leave: '\u2708',
  };

  return (
    <Text style={[styles.tabIcon, focused && styles.tabIconActive]}>
      {icons[label] || '\u2B24'}
    </Text>
  );
}

export default function MainLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#1e40af',
        tabBarInactiveTintColor: '#94a3b8',
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabBarLabel,
        headerStyle: styles.header,
        headerTitleStyle: styles.headerTitle,
        headerTintColor: '#1e40af',
      }}
    >
      <Tabs.Screen
        name="(employee)/dashboard"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ focused }) => <TabIcon label="Dashboard" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="(employee)/expenses"
        options={{
          title: 'Expenses',
          tabBarIcon: ({ focused }) => <TabIcon label="Expenses" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="(employee)/timesheet"
        options={{
          title: 'Timesheet',
          tabBarIcon: ({ focused }) => <TabIcon label="Timesheet" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="(employee)/payslips"
        options={{
          title: 'Payslips',
          tabBarIcon: ({ focused }) => <TabIcon label="Payslips" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="(employee)/leave"
        options={{
          title: 'Leave',
          tabBarIcon: ({ focused }) => <TabIcon label="Leave" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="(manager)/approvals"
        options={{
          href: null, // Hidden from tabs by default, shown for managers
          title: 'Approvals',
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#ffffff',
    borderTopColor: '#e2e8f0',
    borderTopWidth: 1,
    paddingTop: 4,
    paddingBottom: 8,
    height: 60,
  },
  tabBarLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  tabIcon: {
    fontSize: 20,
    color: '#94a3b8',
  },
  tabIconActive: {
    color: '#1e40af',
  },
  header: {
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  headerTitle: {
    fontWeight: '700',
    color: '#1e40af',
    fontSize: 18,
  },
});
