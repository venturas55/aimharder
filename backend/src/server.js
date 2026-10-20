import mysql from 'mysql2/promise';
import { createApp } from './app.js';
import { createRepository } from './repository.js';
import { createTokens } from './auth.js';

for (const name of ['DB_HOST', 'DB_USER', 'DB_NAME']) {
  if (!process.env[name]) throw new Error(`Falta ${name}`);
}
const tokens = createTokens(process.env.TOKEN_SECRET, Number(process.env.TOKEN_TTL_SECONDS || 604800));
const pool = mysql.createPool({ host: process.env.DB_HOST, port: Number(process.env.DB_PORT || 3306),
  user: process.env.DB_USER, password: process.env.DB_PASS || '', database: process.env.DB_NAME,
  connectionLimit: 10, waitForConnections: true, queueLimit: 100, charset: 'utf8mb4', dateStrings: true });
// Read-only preflight: never change production schemas automatically.
try {
  await pool.query('SELECT id, usuario, contrasena, email, full_name FROM usuarios LIMIT 0');
  await pool.query('SELECT user_id, gym, periodicidad, tipo_app, aimharder_user, aimharder_pass FROM configs LIMIT 0');
  await pool.query('SELECT user_id, dia, hora, clase, activo, fecha_evento FROM bookings LIMIT 0');
  await pool.query('SELECT user_id, usuario, class_name FROM current_classes LIMIT 0');
  await pool.query('SELECT user_id, usuario, hora FROM current_hours LIMIT 0');
  const [indexes] = await pool.query('SHOW INDEX FROM bookings');
  const uniqueIndexes = Map.groupBy(indexes.filter(row => Number(row.Non_unique) === 0), row => row.Key_name);
  const hasWeeklyKey = [...uniqueIndexes.values()].some(rows => rows.sort((a, b) => a.Seq_in_index - b.Seq_in_index).map(row => row.Column_name).join(',') === 'user_id,dia');
  if (!hasWeeklyKey) throw Object.assign(new Error('Falta índice único bookings(user_id, dia)'), { code: 'MISSING_WEEKLY_UNIQUE_INDEX' });
} catch (error) {
  console.error('Preflight MySQL fallido:', error.code, 'Revisa docs/migration.md.');
  await pool.end();
  process.exit(1);
}
const server = createApp({ repository: createRepository(pool), tokens }).listen(Number(process.env.PORT || 5052), '0.0.0.0', () => console.log('AimHarder API lista'));
function shutdown() { server.close(async () => { await pool.end(); process.exit(0); }); }
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
