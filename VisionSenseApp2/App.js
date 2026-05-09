import { useState, useRef, useEffect, useCallback } from 'react';
import {
  StyleSheet, Text, View, TouchableOpacity,
  ScrollView, ActivityIndicator, SafeAreaView, StatusBar
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Speech from 'expo-speech';

const SCENE_API = 'http://10.199.131.132:8000/api/v1/describe-scene';
const FACE_API  = 'http://10.199.131.132:8000/api/v1/recognise-face';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [loading, setLoading]     = useState(false);
  const [faceLoading, setFaceLoading] = useState(false);
  const [result, setResult]       = useState(null);
  const [faceResult, setFaceResult] = useState(null);
  const [error, setError]         = useState(null);
  const [autoMode, setAutoMode]   = useState(false);
  const [mode, setMode]           = useState('scene'); // 'scene' | 'face'

  const cameraRef  = useRef(null);
  const autoRef    = useRef(null);
  const loadingRef = useRef(false);

  // ── Scene description ────────────────────────────────────────────────────
  const describeScene = useCallback(async () => {
    if (!cameraRef.current || loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    setError(null);
    setFaceResult(null);

    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.8 });
      const response = await fetch(SCENE_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: photo.base64, language: 'both' }),
      });
      const data = await response.json();
      setResult(data);

      if (data.description_tamil) {
        Speech.stop();
        Speech.speak(data.description_tamil, {
          language: 'ta-IN',
          rate: 0.8,
          onDone: () => { loadingRef.current = false; setLoading(false); },
          onError: () => { loadingRef.current = false; setLoading(false); },
        });
      } else {
        loadingRef.current = false;
        setLoading(false);
      }
    } catch (err) {
      const errMsg = 'சேவையகத்துடன் இணைப்பு தோல்வியடைந்தது!';
      setError(errMsg);
      Speech.speak(errMsg, { language: 'ta-IN' });
      loadingRef.current = false;
      setLoading(false);
    }
  }, []);

  // ── Face recognition ─────────────────────────────────────────────────────
  const recogniseFace = useCallback(async () => {
    if (!cameraRef.current || loadingRef.current) return;
    loadingRef.current = true;
    setFaceLoading(true);
    setError(null);
    setResult(null);

    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.8 });
      const response = await fetch(FACE_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: photo.base64 }),
      });
      const data = await response.json();
      setFaceResult(data);

      // Speak result in Tamil
      let speechText = '';
      if (data.matches && data.matches.length > 0) {
        const names = data.matches.map(m => m.identity).join(', ');
        speechText = `${names} இங்கே இருக்கிறார்கள்!`;
      } else {
        speechText = 'இந்த நபர் யார் என்று தெரியவில்லை.';
      }
      Speech.stop();
      Speech.speak(speechText, {
        language: 'ta-IN',
        rate: 0.8,
        onDone: () => { loadingRef.current = false; setFaceLoading(false); },
        onError: () => { loadingRef.current = false; setFaceLoading(false); },
      });
    } catch (err) {
      const errMsg = 'முகம் அடையாளம் காண தோல்வி!';
      setError(errMsg);
      Speech.speak(errMsg, { language: 'ta-IN' });
      loadingRef.current = false;
      setFaceLoading(false);
    }
  }, []);

  // ── Auto mode ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (autoMode) {
      autoRef.current = setInterval(() => {
        if (!loadingRef.current) describeScene();
      }, 8000);
    } else {
      clearInterval(autoRef.current);
    }
    return () => clearInterval(autoRef.current);
  }, [autoMode, describeScene]);

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.title}>👁️ VisionSense AI</Text>
        <Text style={styles.subtitle}>பார்வையற்றோருக்கான AI உதவியாளர்</Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>📷 Camera Permission கொடு</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const isLoading = loading || faceLoading;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0a" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>👁️ VisionSense AI</Text>
        <Text style={styles.subtitle}>பார்வையற்றோருக்கான AI உதவியாளர்</Text>
        <Text style={styles.hint}>📱 Screen தொட்டால் விவரிக்கும்!</Text>
      </View>

      {/* Camera — touch to describe scene */}
      <TouchableOpacity
        style={styles.cameraWrapper}
        onPress={describeScene}
        disabled={isLoading}
        activeOpacity={0.9}
      >
        <CameraView style={StyleSheet.absoluteFill} ref={cameraRef} facing="back" />
        {isLoading && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator color="#6c63ff" size="large" />
            <Text style={styles.loadingText}>
              {faceLoading ? 'முகம் அடையாளம் காண்கிறது...' : 'பேசுகிறது...'}
            </Text>
          </View>
        )}
        {!isLoading && (
          <View style={styles.tapHint}>
            <Text style={styles.tapHintText}>👆 காட்சி விவரிக்க தொடவும்</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Buttons */}
      <View style={styles.btnRow}>
        {/* Scene describe */}
        <TouchableOpacity
          style={[styles.btn, isLoading && styles.btnDisabled]}
          onPress={describeScene}
          disabled={isLoading}
        >
          <Text style={styles.btnText}>📸 காட்சி விவரி</Text>
        </TouchableOpacity>

        {/* Face recognition */}
        <TouchableOpacity
          style={[styles.faceBtn, isLoading && styles.btnDisabled]}
          onPress={recogniseFace}
          disabled={isLoading}
        >
          <Text style={styles.btnText}>👤 யார் இது?</Text>
        </TouchableOpacity>

        {/* Auto mode */}
        <TouchableOpacity
          style={[styles.autoBtn, autoMode && styles.autoBtnActive]}
          onPress={() => setAutoMode(!autoMode)}
        >
          <Text style={styles.autoBtnText}>
            {autoMode ? '⏹ Auto\nOFF' : '▶️ Auto\nON'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Error */}
      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      {/* Scene Result */}
      {result && !error && (
        <ScrollView style={styles.resultBox} showsVerticalScrollIndicator={false}>
          <Text style={styles.objectCount}>
            🔍 {result.object_count} பொருள்கள் கண்டறியப்பட்டன
          </Text>
          <Text style={styles.label}>🇮🇳 தமிழ்:</Text>
          <Text style={styles.desc}>{result.description_tamil}</Text>
          <Text style={styles.label}>🇬🇧 English:</Text>
          <Text style={styles.desc}>{result.description_english}</Text>
          <Text style={styles.time}>⚡ {result.processing_time_ms}ms</Text>
        </ScrollView>
      )}

      {/* Face Result */}
      {faceResult && !error && (
        <ScrollView style={styles.resultBox} showsVerticalScrollIndicator={false}>
          <Text style={styles.objectCount}>
            👤 {faceResult.faces_detected} முகங்கள் கண்டறியப்பட்டன
          </Text>
          {faceResult.matches && faceResult.matches.length > 0 ? (
            faceResult.matches.map((match, idx) => (
              <View key={idx} style={styles.matchCard}>
                <Text style={styles.matchName}>✅ {match.identity}</Text>
                <Text style={styles.matchConf}>
                  நம்பிக்கை: {(match.confidence * 100).toFixed(0)}%
                </Text>
              </View>
            ))
          ) : (
            <Text style={styles.desc}>❌ யார் என்று தெரியவில்லை</Text>
          )}
          <Text style={styles.time}>⚡ {faceResult.processing_time_ms}ms</Text>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a', padding: 16 },
  header: { alignItems: 'center', marginBottom: 10, marginTop: 8 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 12, color: '#6c63ff', marginTop: 3 },
  hint: { fontSize: 10, color: '#555', marginTop: 3 },
  cameraWrapper: {
    width: '100%', height: 220, borderRadius: 16, marginBottom: 12,
    borderWidth: 2, borderColor: '#6c63ff', overflow: 'hidden',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.65)',
    justifyContent: 'center', alignItems: 'center',
  },
  loadingText: { color: '#6c63ff', marginTop: 10, fontSize: 14, fontWeight: 'bold' },
  tapHint: {
    position: 'absolute', bottom: 10, alignSelf: 'center',
    backgroundColor: 'rgba(108,99,255,0.75)',
    paddingHorizontal: 14, paddingVertical: 5, borderRadius: 20,
  },
  tapHintText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  btnRow: { flexDirection: 'row', gap: 8, marginBottom: 10 },
  btn: {
    flex: 1, backgroundColor: '#6c63ff', padding: 14,
    borderRadius: 14, alignItems: 'center', justifyContent: 'center',
  },
  faceBtn: {
    flex: 1, backgroundColor: '#2d9cdb', padding: 14,
    borderRadius: 14, alignItems: 'center', justifyContent: 'center',
  },
  btnDisabled: { backgroundColor: '#333' },
  btnText: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  autoBtn: {
    backgroundColor: '#1a1a1a', padding: 12, borderRadius: 14,
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: '#6c63ff', width: 70,
  },
  autoBtnActive: { backgroundColor: '#6c63ff' },
  autoBtnText: { color: '#fff', fontSize: 10, fontWeight: 'bold', textAlign: 'center' },
  errorBox: {
    backgroundColor: '#2a0a0a', padding: 10, borderRadius: 10,
    marginBottom: 8, borderWidth: 1, borderColor: '#ff6b6b',
  },
  errorText: { color: '#ff6b6b', textAlign: 'center', fontSize: 12 },
  resultBox: { backgroundColor: '#1a1a1a', borderRadius: 14, padding: 14, flex: 1 },
  objectCount: { color: '#6c63ff', fontWeight: 'bold', fontSize: 14, marginBottom: 6 },
  label: { color: '#6c63ff', fontWeight: 'bold', marginTop: 8, fontSize: 12 },
  desc: { color: '#fff', marginTop: 4, lineHeight: 22, fontSize: 13 },
  time: { color: '#444', marginTop: 10, fontSize: 10, textAlign: 'right' },
  matchCard: {
    backgroundColor: '#0d2a0d', padding: 12, borderRadius: 10,
    marginTop: 8, borderWidth: 1, borderColor: '#27ae60',
  },
  matchName: { color: '#2ecc71', fontSize: 18, fontWeight: 'bold' },
  matchConf: { color: '#aaa', fontSize: 12, marginTop: 4 },
});