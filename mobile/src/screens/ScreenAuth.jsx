import React, { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, View } from 'react-native';
import { Button, Field, Notice, styles, usePalette } from '../components/Ui';
import { request } from '../services/api-service';

export default function ScreenAuth({ onLogin }) {
  const c = usePalette();
  const [register, setRegister] = useState(false);
  const [form, setForm] = useState({ usuario: '', contrasena: '', email: '', full_name: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const submitting = useRef(false);
  function change(key, value) { setForm(previous => ({ ...previous, [key]: value })); }
  async function submit() {
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true); setError(''); setMessage('');
    try {
      if (!form.usuario.trim() || !form.contrasena) throw new Error('Introduce usuario y contraseña');
      if (register) {
        await request('/auth/register', { method: 'POST', body: form });
        setRegister(false); change('contrasena', ''); setMessage('Cuenta creada. Inicia sesión.');
      } else {
        const result = await request('/auth/login', { method: 'POST', body: { usuario: form.usuario, contrasena: form.contrasena } });
        await onLogin(result.data.token);
      }
    } catch (error) { setError(error.message); }
    finally { submitting.current = false; setBusy(false); }
  }
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.content, { maxWidth: 560, flexGrow: 1, justifyContent: 'center' }]}>
      <View style={{ gap: 14, paddingVertical: 20 }}><Text style={styles.eyebrow}>AIMHARDER / TU RUTINA</Text>
        <Text style={[styles.heading, { fontSize: 40, color: c.text }]}>Entrena más.{ '\n' }Organiza menos.</Text>
        <Text style={{ color: c.muted, fontSize: 16, lineHeight: 24 }}>Tu semana, tus clases, todo bajo control.</Text></View>
      <View style={[styles.card, { backgroundColor: c.card, borderColor: c.line }]}>
        <Text style={[styles.heading, { color: c.text }]}>{register ? 'Crear cuenta' : 'Bienvenido'}</Text>
        <Notice text={error} error /><Notice text={message} />
        <Field label="Usuario" value={form.usuario} onChangeText={value => change('usuario', value)} autoCapitalize="none" autoCorrect={false} maxLength={50} editable={!busy} textContentType="username" />
        {register && <><Field label="Nombre completo" value={form.full_name} onChangeText={value => change('full_name', value)} maxLength={150} editable={!busy} textContentType="name" />
          <Field label="Email" value={form.email} onChangeText={value => change('email', value)} autoCapitalize="none" autoCorrect={false} keyboardType="email-address" maxLength={200} editable={!busy} textContentType="emailAddress" /></>}
        <Field label={register ? 'Contraseña (mínimo 8 caracteres)' : 'Contraseña'} value={form.contrasena} onChangeText={value => change('contrasena', value)} secureTextEntry autoCapitalize="none" maxLength={256} editable={!busy} textContentType={register ? 'newPassword' : 'password'} />
        <Button title={register ? 'Crear cuenta' : 'Entrar'} busy={busy} onPress={submit} />
        <Button secondary disabled={busy} title={register ? 'Ya tengo cuenta' : 'Crear una cuenta'} onPress={() => { setRegister(!register); setError(''); setMessage(''); }} />
      </View>
    </ScrollView>
  </KeyboardAvoidingView>;
}
