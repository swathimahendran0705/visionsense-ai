import { useState, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Alert, ActivityIndicator, SafeAreaView } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';

const API_URL = 'http://10.199.131.132:8000/api/v1/describe-scene';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const cameraRef = useRef(null);

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.title}>👁️ VisionSense AI</Text>
        <Text style={styles.subtitle}>Camera permission needed</Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>Grant Permission</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const describeScene = async () => {
    if (!cameraRef.current) return;
    setLoading(true);
    setResult(null);
    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.5 });
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: photo.base64, language: 'both' }),
      });
      const data = await response.json();
      setResult(data);
      if (data.description_tamil) {
        Speech.speak(data.description_tamil, { language: 'ta-IN', rate: 0.8 });
      }
    } catch (err) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>👁️ VisionSense AI</Text>
      <CameraView style={styles.camera} ref={cameraRef} facing="back" />
      <TouchableOpacity style={[styles.btn, loading && styles.btnDisabled]} onPress={describeScene} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>📸 Describe Scene</Text>}
      </TouchableOpacity>
      {result && (
        <ScrollView style={styles.resultBox}>
          <Text style={styles.label}>🔍 Objects: {result.object_count}</Text>
          <Text style={styles.label}>🇬🇧 English:</Text>
          <Text style={styles.desc}>{result.description_english}</Text>
          <Text style={styles.label}>🇮🇳 Tamil:</Text>
          <Text style={styles.desc}>{result.description_tamil}</Text>
          <Text style={styles.time}>⚡ {result.processing_time_ms}ms</Text>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a', alignItems: 'center', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 12, marginTop: 40 },
  subtitle: { color: '#aaa', marginBottom: 20 },
  camera: { width: '100%', height: 300, borderRadius: 12, marginBottom: 16 },
  btn: { backgroundColor: '#6c63ff', padding: 16, borderRadius: 12, width: '100%', alignItems: 'center' },
  btnDisabled: { backgroundColor: '#444' },
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  resultBox: { marginTop: 16, width: '100%', backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16 },
  label: { color: '#6c63ff', fontWeight: 'bold', marginTop: 8 },
  desc: { color: '#fff', marginTop: 4, lineHeight: 22 },
  time: { color: '#888', marginTop: 8, fontSize: 12 },
});