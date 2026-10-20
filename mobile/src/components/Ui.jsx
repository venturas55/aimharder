import React, { useState } from 'react';
import { ActivityIndicator, FlatList, Modal, Pressable, StyleSheet, Text, TextInput, View, useColorScheme } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';

export function usePalette() {
  return useColorScheme() === 'dark'
    ? { bg: '#0b1220', card: '#131f33', text: '#f3f5fa', muted: '#a8b5ca', line: '#304057', accent: '#b9a7ff', input: '#19283e' }
    : { bg: '#f3f4fa', card: '#ffffff', text: '#172138', muted: '#617089', line: '#dce1ed', accent: '#5a36c8', input: '#f7f8fc' };
}
export function Button({ title, onPress, busy, disabled, secondary = false }) {
  const c = usePalette();
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled: disabled || busy, busy: !!busy }} disabled={disabled || busy} onPress={onPress}
    style={({ pressed }) => [styles.button, { backgroundColor: secondary ? c.input : '#5a36c8', opacity: disabled || busy || pressed ? 0.55 : 1 }]}>
    {busy ? <ActivityIndicator color={secondary ? c.accent : '#fff'} /> : <Text style={{ color: secondary ? c.accent : '#fff', fontWeight: '700', textAlign: 'center' }}>{title}</Text>}
  </Pressable>;
}
export function Field({ label, secureTextEntry = false, ...props }) {
  const c = usePalette();
  const [visible, setVisible] = useState(false);
  return <View style={styles.field}><Text style={{ color: c.muted, fontWeight: '600' }}>{label}</Text>
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
      <TextInput {...props} accessibilityLabel={label} secureTextEntry={secureTextEntry && !visible} placeholderTextColor={c.muted}
        style={[styles.input, { flex: 1, color: c.text, backgroundColor: c.input, borderColor: c.line }]} />
      {secureTextEntry && <Pressable onPress={() => setVisible(!visible)} accessibilityRole="button" accessibilityLabel={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'} style={{ padding: 12 }}><Ionicons name={visible ? 'eye-off-outline' : 'eye-outline'} size={24} color={c.accent} accessible={false} /></Pressable>}
    </View>
  </View>;
}
export function Select({ label, value, options, onChange, disabled, compact = false }) {
  const c = usePalette();
  const [open, setOpen] = useState(false);
  return <View style={compact ? { minWidth: 0 } : styles.field}>{!compact && <Text style={{ color: c.muted, fontWeight: '600' }}>{label}</Text>}
    <Pressable disabled={disabled} accessibilityRole="button" accessibilityLabel={`${label}: ${value || 'Sin seleccionar'}`} accessibilityState={{ disabled: !!disabled }}
      onPress={() => setOpen(true)} style={[styles.input, compact && { minHeight: 44, paddingHorizontal: 10, paddingVertical: 10 }, { backgroundColor: c.input, borderColor: c.line, opacity: disabled ? 0.45 : 1 }]}>
      <Text style={{ color: value ? c.text : c.muted }}>{options.find(option => option.value === value)?.label || value || (compact ? `${label}…` : 'Seleccionar…')} ▾</Text>
    </Pressable>
    <Modal visible={open} animationType="slide" onRequestClose={() => setOpen(false)}>
      <SafeAreaView style={{ flex: 1, backgroundColor: c.bg }}><View style={{ padding: 24, flex: 1, gap: 16 }}>
        <Text style={[styles.heading, { color: c.text }]}>{label}</Text>
        <FlatList data={options} keyExtractor={item => item.value} ListEmptyComponent={<Text style={{ color: c.muted }}>Sin opciones. Catálogo pendiente de sincronización.</Text>}
          renderItem={({ item }) => <Pressable accessibilityRole="button" accessibilityState={{ selected: item.value === value }} onPress={() => { onChange(item.value); setOpen(false); }}
            style={{ padding: 18, borderBottomWidth: 1, borderColor: c.line }}><Text style={{ color: item.value === value ? c.accent : c.text, fontSize: 17 }}>{item.label}</Text></Pressable>} />
        <Button title="Cerrar" secondary onPress={() => setOpen(false)} />
      </View></SafeAreaView>
    </Modal>
  </View>;
}
export function Notice({ text, error = false }) {
  const c = usePalette();
  return text ? <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={[styles.notice, { color: error ? '#b4233a' : c.accent, backgroundColor: error ? '#ffedf0' : c.input }]}>{text}</Text> : null;
}
export const styles = StyleSheet.create({
  content: { padding: 22, paddingBottom: 48, width: '100%', maxWidth: 760, alignSelf: 'center', gap: 20 },
  card: { padding: 22, borderRadius: 24, gap: 12, borderWidth: 1 },
  heading: { fontSize: 26, fontWeight: '800', letterSpacing: -0.7 },
  eyebrow: { fontSize: 12, fontWeight: '800', letterSpacing: 2, color: '#977bea' },
  input: { borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 14, minHeight: 50, fontSize: 16 },
  button: { padding: 16, minHeight: 50, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  field: { gap: 8, marginBottom: 6 },
  notice: { padding: 16, borderRadius: 12, lineHeight: 22 },
});
