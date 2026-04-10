import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';

export default function CameraScreen() {
  const router = useRouter();
  const [captured, setCaptured] = useState(false);

  const handleCapture = () => {
    // Would use expo-camera:
    // const photo = await cameraRef.current.takePictureAsync();
    setCaptured(true);
    Alert.alert(
      'Receipt Captured',
      'Receipt photo has been captured successfully.',
      [
        {
          text: 'Use Photo',
          onPress: () => router.push('/(main)/(employee)/expenses/claim' as any),
        },
        {
          text: 'Retake',
          onPress: () => setCaptured(false),
          style: 'cancel',
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      {/* Camera preview placeholder */}
      <View style={styles.cameraPreview}>
        <View style={styles.placeholder}>
          <Text style={styles.placeholderIcon}>C</Text>
          <Text style={styles.placeholderText}>Camera Preview</Text>
          <Text style={styles.placeholderSubtext}>
            Point your camera at the receipt
          </Text>
        </View>

        {/* Viewfinder overlay */}
        <View style={styles.viewfinder}>
          <View style={[styles.corner, styles.topLeft]} />
          <View style={[styles.corner, styles.topRight]} />
          <View style={[styles.corner, styles.bottomLeft]} />
          <View style={[styles.corner, styles.bottomRight]} />
        </View>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={() => router.back()}
        >
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.captureButton}
          onPress={handleCapture}
        >
          <View style={styles.captureInner} />
        </TouchableOpacity>

        <View style={styles.spacer} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  cameraPreview: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholder: {
    alignItems: 'center',
  },
  placeholderIcon: {
    fontSize: 48,
    color: '#64748b',
    marginBottom: 12,
  },
  placeholderText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#94a3b8',
  },
  placeholderSubtext: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 8,
  },
  viewfinder: {
    position: 'absolute',
    top: '15%',
    left: '10%',
    right: '10%',
    bottom: '25%',
  },
  corner: {
    position: 'absolute',
    width: 32,
    height: 32,
    borderColor: '#3b82f6',
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderTopLeftRadius: 8,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderTopRightRadius: 8,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderBottomLeftRadius: 8,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderBottomRightRadius: 8,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 32,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  cancelButton: {
    width: 64,
  },
  cancelText: {
    color: '#ffffff',
    fontSize: 16,
  },
  captureButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#ffffff',
  },
  spacer: {
    width: 64,
  },
});
