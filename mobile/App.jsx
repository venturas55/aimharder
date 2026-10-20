import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StatusBar, View, useColorScheme } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import ScreenAuth from './src/screens/ScreenAuth';
import ScreenDashboard from './src/screens/ScreenDashboard';
import { Notice, usePalette } from './src/components/Ui';

function AppContent() {
  const c = usePalette();
  const dark = useColorScheme() === 'dark';
  const [token, setToken] = useState(null);
  const [restoring, setRestoring] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let alive = true;
    SecureStore.getItemAsync('aimharder-session').then(value => { if (alive) setToken(value); })
      .catch(() => { if (alive) setError('No se pudo recuperar sesión guardada.'); })
      .finally(() => { if (alive) setRestoring(false); });
    return () => { alive = false; };
  }, []);
  async function login(value) { await SecureStore.setItemAsync('aimharder-session', value); setError(''); setToken(value); }
  async function logout() {
    try { await SecureStore.deleteItemAsync('aimharder-session'); setError(''); setToken(null); }
    catch { setError('No se pudo borrar sesión. Reintenta salir.'); }
  }
  return <SafeAreaView style={{ flex: 1, backgroundColor: c.bg }}>
    <StatusBar barStyle={dark ? 'light-content' : 'dark-content'} />
    {error ? <View style={{ padding: 16 }}><Notice text={error} error /></View> : null}
    {restoring ? <View style={{ flex: 1, justifyContent: 'center' }}><ActivityIndicator size="large" color={c.accent} /></View>
      : token ? <ScreenDashboard key={token} token={token} onLogout={logout} /> : <ScreenAuth onLogin={login} />}
  </SafeAreaView>;
}
export default function App() { return <SafeAreaProvider><AppContent /></SafeAreaProvider>; }
