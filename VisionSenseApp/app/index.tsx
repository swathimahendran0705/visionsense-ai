import { useState, useRef } from 'react';
import {
  View, Text, TouchableOpacity,
  StyleSheet, ScrollView, ActivityIndicator, Alert
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';

const API_URL = 'http://YOUR_PC_IP:8000/api/v1/describe-scene';

export default function HomeScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const cameraRef = useRef<CameraView>(null);

  const captureAndDescribe = async () => {
    if (!cameraRef.current) return;
    setLoading(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true });
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: photo?.base64,
          language: 'both'
        }),
      });
      const data = await response.json();
      setResult(data);
      // Tamil description speak pannudu
      if (data.description_tamil) {
        Speech.speak(data.description_tamil, { language: 'ta-IN' });
      }
    } catch (err) {
      Alert.alert('Error', 'API call failed!');
    } finally {
      setLoading(false);
    }
  };

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Camera permission needed</Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>👁 VisionSense AI</Text>
      <CameraView style={styles.camera} ref={cameraRef} />
      <TouchableOpacity
        style={styles.btn}
        onPress={captureAndDescribe}
        disabled={loading}
      >
        {loading
          ? <ActivityIndicator color="#fff" />
          : <Text style={styles.btnText}>📸 Describe Scene</Text>
        }
      </TouchableOpacity>
      {result && (
        <ScrollView style={styles.result}>
          <Text style={styles.label}>🇬🇧 English:</Text>
          <Text style={styles.desc}>{result.description_english}</Text>
          <Text style={styles.label}>🇮🇳 Tamil:</Text>
          <Text style={styles.desc}>{result.description_tamil}</Text>
          <Text style={styles.count}>
            Objects: {result.object_count} | {result.processing_time_ms}ms
          </Text>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a', padding: 16 },
  title: { color: '#fff', fontSize: 24, fontWeight: 'bold',
           textAlign: 'center', marginTop: 50, marginBottom: 16 },
  camera: { flex: 1, borderRadius: 16, overflow: 'hidden' },
  btn: { backgroundColor: '#6C63FF', padding: 16, borderRadius: 12,
         marginTop: 16, alignItems: 'center' },
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  result: { marginTop: 16, maxHeight: 200 },
  label: { color: '#6C63FF', fontWeight: 'bold', marginTop: 8 },
  desc: { color: '#fff', fontSize: 14, marginTop: 4 },
  count: { color: '#888', fontSize: 12, marginTop: 8 },
});