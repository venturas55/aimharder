import test from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../src/app.js';
import { createTokens } from '../src/auth.js';
import { hashPassword, verifyPassword } from '../src/password.js';
import { DAYS, registration, configuration, schedule } from '../src/validation.js';
import { createRepository } from '../src/repository.js';

test('Werkzeug-compatible scrypt hashes roundtrip and reject invalid passwords', async () => {
  const hash = await hashPassword('contraseña segura');
  assert.match(hash, /^scrypt:32768:8:1\$/);
  assert.equal(await verifyPassword('contraseña segura', hash), true);
  assert.equal(await verifyPassword('otra contraseña', hash), false);
  assert.equal(await verifyPassword('foo', 'scrypt:1073741824:8:1$salt$ff'), false);
  assert.equal(await verifyPassword('foo', 'malformed'), false);
});

test('tokens reject tampering and expiration', () => {
  const tokens = createTokens('x'.repeat(40));
  const token = tokens.issue(4);
  assert.equal(tokens.verify(token), 4);
  assert.equal(tokens.verify(`x${token}`), null);
  assert.equal(tokens.verify(`${token}.extra`), null);
  assert.equal(createTokens('y'.repeat(40)).verify(token), null);
  assert.throws(() => createTokens('short'));
  const original = Date.now;
  try { Date.now = () => original() + 8 * 24 * 3600 * 1000; assert.equal(tokens.verify(token), null); }
  finally { Date.now = original; }
});

test('verifies legacy fixtures generated independently with Python hashlib', async () => {
  const fixtures = [
    'scrypt:32768:8:1$fixturesalt$aab02924e37a634faecd756799b88923727dc1c056a5cfe29d385a600f0847ae8f0c0362f6e8bc5484bdba46b4f81e06bea59013dc50adeea297a92d59cda509',
    'pbkdf2:sha256:1000000$fixturesalt$6089fd02be2d4670a1daf2eebcf3daad601c0fbfca8720ed8d534d290ed6750f',
  ];
  for (const hash of fixtures) {
    assert.equal(await verifyPassword('legacy-password', hash), true);
    assert.equal(await verifyPassword('wrong-password', hash), false);
  }
});

test('validation rejects invalid input and stale active catalog selections', () => {
  assert.throws(() => registration({ usuario: 42 }), { status: 400 });
  assert.throws(() => configuration({ tipo_app: 'other' }), { status: 400 });
  const rows = DAYS.map(dia => ({ dia, hora: '', clase: '', activo: false }));
  assert.equal(schedule(rows, [], []).length, 7);
  assert.throws(() => schedule([...rows.slice(1), rows[1]], [], []), { status: 400 });
  assert.throws(() => schedule([null, ...rows.slice(1)], [], []), { status: 400 });
  rows[0] = { ...rows[0], hora: '08:00 - 09:00', clase: 'BJJ', activo: true };
  assert.throws(() => schedule(rows, [], []), { status: 400 });
  assert.equal(schedule(rows, ['BJJ'], ['08:00 - 09:00'])[0].activo, true);
  rows[0].activo = false;
  assert.equal(schedule(rows, [], [], rows)[0].clase, 'BJJ');
});

test('API authenticates, scopes owner, excludes credentials and validates writes', async t => {
  const password = await hashPassword('password123');
  const tokens = createTokens('s'.repeat(40));
  const calls = [];
  const repository = {
    async findUser(usuario) { return usuario === 'ana' ? { id: 7, usuario, contrasena: password } : undefined; },
    async user(id) { return { id, usuario: 'ana', email: 'a@example.com', full_name: 'Ana' }; },
    async register(data, hash) { calls.push(['register', data.usuario, await verifyPassword(data.contrasena, hash)]); },
    async dashboard(id, usuario) { calls.push(['read', id, usuario]); return { config: { has_password: true }, bookings: [], classes: ['BJJ'], hours: ['08:00 - 09:00'] }; },
    async saveBookings(id, rows) { calls.push(['bookings', id, rows]); },
    async saveConfig(id, data) { calls.push(['config', id, data]); },
  };
  const server = createApp({ repository, tokens }).listen(0, '127.0.0.1');
  await new Promise(resolve => server.once('listening', resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  async function send(path, method = 'GET', body, token) {
    const response = await fetch(`http://127.0.0.1:${server.address().port}/api${path}`, {
      method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    return { status: response.status, body: await response.json() };
  }
  assert.equal((await send('/dashboard')).status, 401);
  assert.equal((await send('/bookings', 'PUT', { bookings: [] })).status, 401);
  assert.equal((await send('/config', 'PUT', {})).status, 401);
  assert.equal((await send('/auth/login', 'POST', { usuario: 9, contrasena: 'foo' })).status, 400);
  assert.equal((await send('/auth/login', 'POST', { usuario: 'ana', contrasena: 'wrong' })).status, 401);
  const login = await send('/auth/login', 'POST', { usuario: 'ana', contrasena: 'password123' });
  assert.equal(login.status, 200);
  const token = login.body.data.token;
  const dashboard = await send('/dashboard', 'GET', undefined, token);
  assert.equal(dashboard.body.data.bookings.length, 7);
  assert.equal(JSON.stringify(dashboard.body).includes(password), false);
  assert.deepEqual(calls.at(-1), ['read', 7, 'ana']);
  const rows = DAYS.map(dia => ({ dia, hora: '08:00 - 09:00', clase: 'BJJ', activo: true }));
  assert.equal((await send('/bookings', 'PUT', { user_id: 999, bookings: rows }, token)).status, 200);
  assert.equal(calls.at(-1)[1], 7);
  assert.equal((await send('/bookings', 'PUT', { bookings: rows.slice(1) }, token)).status, 400);
  assert.equal((await send('/config', 'PUT', { user_id: 999, tipo_app: 'resamania', gym: 'enjoy', periodicidad: 'daily', aimharder_user: 'test' }, token)).status, 200);
  assert.equal(calls.at(-1)[1], 7);
  assert.equal(calls.at(-1)[2].aimharder_pass, null);
  assert.equal((await send('/auth/register', 'POST', { usuario: 'new', contrasena: 'password123', email: 'n@example.com', full_name: 'New' })).status, 201);
  assert.deepEqual(calls.at(-1), ['register', 'new', true]);
});

test('bookings transaction rolls back partial writes and releases connection', async () => {
  const events = [];
  const connection = {
    async beginTransaction() { events.push('begin'); },
    async execute(sql, values) { events.push(['sql', sql, values]); if (values?.[1] === 'Martes') throw new Error('simulated failure'); return [[]]; },
    async commit() { events.push('commit'); },
    async rollback() { events.push('rollback'); },
    release() { events.push('release'); },
  };
  const repository = createRepository({ async getConnection() { return connection; } });
  await assert.rejects(repository.saveBookings(7, DAYS.map(dia => ({ dia, hora: '', clase: '', activo: false }))));
  assert.equal(events.includes('commit'), false);
  assert.deepEqual(events.slice(-2), ['rollback', 'release']);
  assert.ok(events.filter(event => Array.isArray(event)).every(event => event[2][0] === 7));
});
