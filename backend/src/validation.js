export const DAYS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo'];
export function fail(message, status = 400) { throw Object.assign(new Error(message), { status }); }
export function field(value, name, max, min = 1) {
  if (typeof value !== 'string' || value.length < min || value.length > max || value.includes('\0')) fail(`${name}: longitud permitida ${min}-${max}`);
  return value;
}
export function trimmed(value, name, max) { return field(typeof value === 'string' ? value.trim() : value, name, max); }
export function registration(body) {
  const usuario = trimmed(body.usuario, 'Usuario', 50);
  const contrasena = field(body.contrasena, 'Contraseña', 256, 8);
  const email = trimmed(body.email, 'Email', 200);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) fail('Email inválido');
  return { usuario, contrasena, email, full_name: trimmed(body.full_name, 'Nombre', 150) };
}
export function configuration(body) {
  if (!['aimharder', 'trainingmyapp', 'resamania'].includes(body.tipo_app)) fail('Proveedor inválido');
  if (!['hourly', 'daily', 'weekly'].includes(body.periodicidad)) fail('Periodicidad inválida');
  return { tipo_app: body.tipo_app, periodicidad: body.periodicidad,
    gym: trimmed(body.gym, 'Gym', 100),
    aimharder_user: trimmed(body.aimharder_user, 'Usuario del proveedor', 200),
    aimharder_pass: body.aimharder_pass === undefined || body.aimharder_pass === '' ? null : field(body.aimharder_pass, 'Contraseña del proveedor', 200) };
}
export function schedule(rows, classes, hours, previous = []) {
  if (!Array.isArray(rows) || rows.length !== 7 || new Set(rows.map(row => row?.dia)).size !== 7) fail('Se requieren siete días distintos');
  return rows.map(row => {
    if (!DAYS.includes(row?.dia) || typeof row?.activo !== 'boolean') fail('Día o activación inválidos');
    const hora = field(row.hora, 'Hora', 255, 0);
    const clase = field(row.clase, 'Clase', 100, 0);
    const old = previous.find(item => item.dia === row.dia);
    // Preserve stale selections on inactive days; active days use the current catalog.
    if ((hora && !hours.includes(hora) && !(old?.hora === hora && !row.activo)) || (clase && !classes.includes(clase) && !(old?.clase === clase && !row.activo))) fail('Clase u horario no disponible');
    if (row.activo && (!hora || !clase || !/^([01]\d|2[0-3]):[0-5]\d/.test(hora))) fail('Día activo requiere clase y hora válidas');
    return { dia: row.dia, hora, clase, activo: row.activo };
  });
}
