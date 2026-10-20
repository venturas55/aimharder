import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, RefreshControl, ScrollView, Switch, Text, View } from 'react-native';
import { Button, Field, Notice, Select, styles, usePalette } from '../components/Ui';
import { request } from '../services/api-service';

const providers = [{ value: 'aimharder', label: 'AimHarder' }, { value: 'trainingmyapp', label: 'TrainingMyApp' }, { value: 'resamania', label: 'Resamania' }];
const frequencies = [{ value: 'hourly', label: 'Horaria' }, { value: 'daily', label: 'Diaria' }, { value: 'weekly', label: 'Semanal' }];

export default function ScreenDashboard({ token, onLogout }) {
  const c = usePalette();
  const [data, setData] = useState(null);
  const [config, setConfig] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [advanced, setAdvanced] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [dirtyForms, setDirtyForms] = useState({ config: false, bookings: false });
  const dirty = dirtyForms.config || dirtyForms.bookings;
  const alive = useRef(true);
  const pending = useRef(false);
  const logoutRef = useRef(onLogout);
  useEffect(() => { logoutRef.current = onLogout; }, [onLogout]);
  async function handleError(error) {
    if (!alive.current) return;
    setError(error.message);
    if (error.status === 401) await logoutRef.current();
  }
  async function load() {
    if (pending.current) return;
    pending.current = true; setLoading(true); setError('');
    try {
      const result = await request('/dashboard', { token });
      if (alive.current) {
        setData(result.data); setBookings(result.data.bookings);
        setConfig({ ...result.data.config, aimharder_pass: '' }); setDirtyForms({ config: false, bookings: false });
      }
    } catch (error) { await handleError(error); }
    finally { pending.current = false; if (alive.current) setLoading(false); }
  }
  useEffect(() => {
    alive.current = true;
    pending.current = true;
    request('/dashboard', { token }).then(result => {
      if (!alive.current) return;
      setData(result.data); setBookings(result.data.bookings);
      setConfig({ ...result.data.config, aimharder_pass: '' });
    }).catch(handleError).finally(() => {
      pending.current = false;
      if (alive.current) setLoading(false);
    });
    return () => { alive.current = false; };
    // Each authenticated session mounts a separate dashboard.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  function changeConfig(key, value) { setConfig(previous => ({ ...previous, [key]: value })); setDirtyForms(previous => ({ ...previous, config: true })); setMessage(''); }
  function changeDay(dia, key, value) { setBookings(previous => previous.map(row => row.dia === dia ? { ...row, [key]: value } : row)); setDirtyForms(previous => ({ ...previous, bookings: true })); setMessage(''); }
  async function save(section) {
    if (pending.current) return;
    pending.current = true; setSaving(section); setError(''); setMessage('');
    try {
      const body = section === 'config' ? { ...config, aimharder_pass: config.aimharder_pass || undefined } : { bookings };
      const result = await request(`/${section}`, { token, method: 'PUT', body });
      if (alive.current) {
        setMessage(result.message);
        if (section === 'config') setConfig(previous => ({ ...previous, has_password: true, aimharder_pass: '' }));
        setDirtyForms(previous => ({ ...previous, [section]: false }));
      }
    } catch (error) { await handleError(error); }
    finally { pending.current = false; if (alive.current) setSaving(''); }
  }
  if (!data) return <View style={[styles.content, { flex: 1, justifyContent: 'center' }]}>{loading ? <ActivityIndicator color={c.accent} size="large" /> : <><Notice text={error} error /><Button title="Reintentar" onPress={load} /><Button secondary title="Salir" onPress={onLogout} /></>}</View>;
  const isBusy = !!saving || loading;
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={loading} enabled={!dirty && !isBusy} onRefresh={() => { if (!dirty && !isBusy) load(); }} tintColor={c.accent} />}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <Text style={styles.eyebrow}>AIMHARDER</Text><Button secondary title="Salir" disabled={isBusy} onPress={onLogout} />
      </View>
      <View style={{ gap: 6 }}><Text style={[styles.heading, { color: c.text }]}>Hola, {data.user.full_name || data.user.usuario}</Text>
        <Text style={{ color: c.muted }}>{data.user.usuario} · {data.user.email}</Text></View>
      <Notice text={error} error /><Notice text={message} />
      <View style={[styles.card, { backgroundColor: '#211342', borderColor: '#38265f' }]}>
        <Text style={styles.eyebrow}>TU PRÓXIMO OBJETIVO</Text><Text style={[styles.heading, { color: '#fff' }]}>Una semana a tu ritmo.</Text>
        <Text style={{ color: '#d0c4eb', lineHeight: 23 }}>{bookings.filter(row => row.activo).length} días activos. El servicio de reservas procesa tu planificación según la configuración guardada.</Text>
      </View>
      <View style={[styles.card, { backgroundColor: c.card, borderColor: c.line }]}>
        <Text style={[styles.heading, { color: c.text }]}>Conecta tu gimnasio</Text>
        <Text style={{ color: c.muted }}>Proveedor, credenciales y frecuencia de automatización.</Text>
        <Button secondary title={advanced ? 'Ocultar configuración' : 'Mostrar configuración'} disabled={isBusy} onPress={() => setAdvanced(!advanced)} />
        {advanced && <>
          <Select label="Proveedor" value={config.tipo_app} options={providers} disabled={isBusy} onChange={value => changeConfig('tipo_app', value)} />
          <Field label="Gym (prefijo)" value={config.gym || ''} maxLength={100} autoCapitalize="none" autoCorrect={false} editable={!isBusy} onChangeText={value => changeConfig('gym', value)} />
          <Select label="Periodicidad" value={config.periodicidad} options={frequencies} disabled={isBusy} onChange={value => changeConfig('periodicidad', value)} />
          <Field label="Usuario del proveedor" value={config.aimharder_user || ''} maxLength={200} autoCapitalize="none" autoCorrect={false} editable={!isBusy} onChangeText={value => changeConfig('aimharder_user', value)} />
          <Field label={config.has_password ? 'Nueva contraseña (vacío conserva actual)' : 'Contraseña del proveedor'} value={config.aimharder_pass} secureTextEntry autoCapitalize="none" maxLength={200} editable={!isBusy} onChangeText={value => changeConfig('aimharder_pass', value)} />
          <Button title="Guardar configuración" busy={saving === 'config'} disabled={isBusy} onPress={() => save('config')} />
        </>}
      </View>
      <View style={{ gap: 6 }}><Text style={styles.eyebrow}>PLANIFICACIÓN</Text><Text style={[styles.heading, { color: c.text }]}>Tu semana</Text>
        <Text style={{ color: c.muted }}>Activa días y elige una clase y horario por día.</Text></View>
      {(!data.classes.length || !data.hours.length) && <Notice text="Catálogo pendiente. Configura gimnasio y espera la ejecución del scraper existente antes de activar días." />}
      {bookings.map(row => <View key={row.dia} style={[styles.card, { backgroundColor: c.card, borderColor: row.activo ? c.accent : c.line }]}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ color: c.text, fontSize: 20, fontWeight: '700' }}>{row.dia === 'Miercoles' ? 'Miércoles' : row.dia === 'Sabado' ? 'Sábado' : row.dia}</Text>
          <Switch accessibilityLabel={`Activar ${row.dia}`} value={row.activo} disabled={isBusy} trackColor={{ true: '#7d58de', false: c.line }} onValueChange={value => changeDay(row.dia, 'activo', value)} />
        </View>
        <Select label="Horario" value={row.hora} disabled={!row.activo || isBusy} options={data.hours.map(value => ({ value, label: value }))} onChange={value => changeDay(row.dia, 'hora', value)} />
        <Select label="Clase" value={row.clase} disabled={!row.activo || isBusy} options={data.classes.map(value => ({ value, label: value }))} onChange={value => changeDay(row.dia, 'clase', value)} />
      </View>)}
      <Button title="Guardar horario semanal" busy={saving === 'bookings'} disabled={isBusy} onPress={() => save('bookings')} />
      {dirty && <Text style={{ color: c.muted, lineHeight: 22 }}>Cambios sin guardar. Guarda cada formulario modificado antes de recargar.</Text>}
      <Text style={{ color: c.muted, textAlign: 'center', fontSize: 12 }}>AimHarder · Guardian del faro</Text>
    </ScrollView>
  </KeyboardAvoidingView>;
}
