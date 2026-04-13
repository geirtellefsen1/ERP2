import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  Image,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Card } from '@/components/Card';
import { api, ApiError } from '@/lib/api';
import { colors, spacing, typography, radii } from '@/theme';

/**
 * Receipt capture screen.
 *
 * Flow:
 *   1. User taps "Take photo" → opens camera via expo-image-picker
 *   2. Image displayed, user adds vendor / amount / category (optional)
 *   3. Submit → POST /api/v1/documents/upload with the image
 *   4. Backend runs Claude Vision extraction async
 *   5. Receipt appears in the user's document queue
 *
 * If the user doesn't have camera permission the button prompts for it.
 */
export function ReceiptCaptureScreen() {
  const navigation = useNavigation();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [vendor, setVendor] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert(
        'Camera permission needed',
        'ClaudERP needs camera access to capture receipts.',
      );
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.7,
    });
    if (!result.canceled && result.assets[0]) {
      setImageUri(result.assets[0].uri);
    }
  };

  const pickFromLibrary = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.7,
    });
    if (!result.canceled && result.assets[0]) {
      setImageUri(result.assets[0].uri);
    }
  };

  const handleSubmit = async () => {
    if (!imageUri) {
      Alert.alert('No photo', 'Please capture or pick a receipt image first.');
      return;
    }
    setSubmitting(true);
    try {
      // In a real build this would POST multipart/form-data to the
      // document upload endpoint. For Tier 4 we send the metadata only
      // and leave the actual file upload for the upload service wiring.
      await api.post('/api/v1/documents/upload', {
        vendor: vendor || null,
        amount: amount ? parseFloat(amount) : null,
        description: description || null,
        // image_uri is a placeholder — real code would do a multipart
        // upload here or get a presigned URL from the backend first
        image_uri: imageUri,
      });
      Alert.alert(
        'Receipt submitted',
        'AI is processing it now. You will see it in your queue shortly.',
      );
      navigation.goBack();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Upload failed';
      Alert.alert('Upload failed', msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Card style={styles.imageCard}>
          {imageUri ? (
            <Image
              source={{ uri: imageUri }}
              style={styles.preview}
              resizeMode="contain"
            />
          ) : (
            <View style={styles.placeholder}>
              <Text style={styles.placeholderEmoji}>📷</Text>
              <Text style={styles.placeholderText}>
                Tap &quot;Take photo&quot; to capture a receipt
              </Text>
            </View>
          )}
        </Card>

        <View style={styles.imageButtons}>
          <Button
            title="Take photo"
            onPress={takePhoto}
            testID="take-photo-button"
          />
          <Button
            title="Pick from library"
            onPress={pickFromLibrary}
            variant="outline"
            testID="pick-library-button"
          />
        </View>

        <View style={styles.metadata}>
          <Input
            testID="vendor-input"
            label="Vendor"
            placeholder="e.g. Adobe, Uber, Starbucks"
            value={vendor}
            onChangeText={setVendor}
            hint="Leave blank to let AI extract it"
          />
          <Input
            testID="amount-input"
            label="Amount"
            placeholder="0.00"
            value={amount}
            onChangeText={setAmount}
            keyboardType="decimal-pad"
            hint="AI will correct this from the image if you skip it"
          />
          <Input
            testID="description-input"
            label="Description"
            placeholder="What was this for?"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={3}
          />
        </View>

        <Button
          testID="submit-receipt-button"
          title="Submit receipt"
          onPress={handleSubmit}
          loading={submitting}
          size="lg"
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  scroll: { padding: spacing.lg },
  imageCard: {
    padding: 0,
    marginBottom: spacing.md,
    overflow: 'hidden',
  },
  preview: {
    width: '100%',
    height: 280,
  },
  placeholder: {
    height: 280,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderEmoji: {
    fontSize: 56,
    marginBottom: spacing.sm,
  },
  placeholderText: {
    fontSize: typography.body,
    color: colors.muted,
  },
  imageButtons: {
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  metadata: {
    marginBottom: spacing.md,
  },
});
