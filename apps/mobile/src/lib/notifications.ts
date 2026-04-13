/**
 * Push notifications setup via Expo Notifications.
 *
 * Flow:
 *   1. App startup calls registerForPushNotificationsAsync()
 *   2. It asks for permission, gets an Expo push token, and POSTs the
 *      token to /api/v1/push/register so the backend can send to it
 *   3. Backend enqueues notifications via Expo's push service
 *
 * Local notifications (scheduled reminders for timesheet submissions,
 * payroll runs, etc.) also run through the same permissions.
 */

import { Platform } from 'react-native';
import { api } from './api';

// Lazy import of expo-notifications so tests that don't install the
// native module don't choke on the import. Real builds will have it.
let Notifications: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  Notifications = require('expo-notifications');
} catch {
  Notifications = null;
}

export interface NotificationRegistration {
  token: string;
  platform: 'ios' | 'android' | 'web';
  device_id?: string;
}

export async function registerForPushNotificationsAsync(): Promise<
  string | null
> {
  if (!Notifications) {
    // Running in a test or environment without expo-notifications
    return null;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'ClaudERP',
      importance: Notifications.AndroidImportance.HIGH,
      lightColor: '#1E40AF',
    });
  }

  const { status: existingStatus } =
    await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    return null;
  }

  try {
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: 'claud-erp-mobile',
    });
    const token: string = tokenData.data;
    await sendTokenToBackend(token);
    return token;
  } catch {
    return null;
  }
}

export async function sendTokenToBackend(token: string): Promise<void> {
  const payload: NotificationRegistration = {
    token,
    platform: Platform.OS as any,
  };
  try {
    await api.post('/api/v1/push/register', payload);
  } catch {
    // Silently swallow — push is a nice-to-have, not a blocker for the
    // rest of the app. The backend will see the token on the next
    // successful registration.
  }
}

/**
 * Schedule a local reminder, e.g. "submit your timesheet by Friday 5pm".
 * Returns the notification identifier or null if notifications aren't
 * available in this environment.
 */
export async function scheduleLocalReminder(
  title: string,
  body: string,
  triggerDate: Date,
): Promise<string | null> {
  if (!Notifications) return null;
  return Notifications.scheduleNotificationAsync({
    content: { title, body },
    trigger: triggerDate,
  });
}

export async function cancelAllLocalNotifications(): Promise<void> {
  if (!Notifications) return;
  await Notifications.cancelAllScheduledNotificationsAsync();
}
