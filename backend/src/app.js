import express from 'express';
import helmet from 'helmet';
import { rateLimit } from 'express-rate-limit';
import { hashPassword, verifyPassword } from './password.js';
import { field, trimmed, fail, registration, configuration, schedule, DAYS } from './validation.js';

export function createApp({ repository, tokens }) {
  const app = express();
  app.disable('x-powered-by');
  app.use(helmet());
  app.use(express.json({ limit: '24kb' }));
  app.use('/api', (_request, response, next) => { response.set('Cache-Control', 'no-store'); next(); });
  const authLimit = rateLimit({ windowMs: 15 * 60 * 1000, limit: 30, standardHeaders: 'draft-8', legacyHeaders: false,
    handler: (_request, response) => response.status(429).json({ success: false, error: { message: 'Demasiados intentos. Reintenta más tarde.' } }) });
  app.get('/api/health', (_request, response) => {
    console.log('GET /api/health');
    response.json({ success: true });
  });
  app.post('/api/auth/register', authLimit, async (request, response) => {
    console.log('POST /api/auth/register', request.body);
    const data = registration(request.body || {});
    await repository.register(data, await hashPassword(data.contrasena));
    response.status(201).json({ success: true, message: 'Cuenta creada. Inicia sesión.' });
  });
  app.post('/api/auth/login', authLimit, async (request, response) => {
    console.log('POST /api/auth/login', request.body);
    const usuario = trimmed(request.body?.usuario, 'Usuario', 50);
    const password = field(request.body?.contrasena, 'Contraseña', 256);
    const user = await repository.findUser(usuario);
    // Perform expensive verification even for unknown users.
    const hash = user?.contrasena || await hashPassword('dummy-password');
    const valid = await verifyPassword(password, hash);
    if (!user || !valid) fail('Usuario o contraseña incorrectos', 401);
    response.json({ success: true, data: { token: tokens.issue(user.id) } });
  });
  app.use('/api', async (request, _response, next) => {
    const token = request.headers.authorization?.match(/^Bearer ([A-Za-z0-9_.-]{1,2048})$/)?.[1];
    const id = token && tokens.verify(token);
    if (!id) fail('Sesión caducada. Inicia sesión.', 401);
    request.user = await repository.user(id);
    if (!request.user) fail('Sesión inválida', 401);
    next();
  });
  app.get('/api/dashboard', async (request, response) => {
    const data = await repository.dashboard(request.user.id, request.user.usuario);
    data.bookings = DAYS.map(dia => data.bookings.find(row => row.dia === dia) || { dia, hora: '', clase: '', activo: false });
    response.json({ success: true, data: { user: request.user, ...data } });
  });
  app.put('/api/config', async (request, response) => {
    await repository.saveConfig(request.user.id, configuration(request.body || {}));
    response.json({ success: true, message: 'Configuración guardada' });
  });
  app.put('/api/bookings', async (request, response) => {
    const data = await repository.dashboard(request.user.id, request.user.usuario);
    await repository.saveBookings(request.user.id, schedule(request.body?.bookings, data.classes, data.hours, data.bookings));
    response.json({ success: true, message: 'Horario guardado' });
  });
  app.use((_request, _response, next) => next(Object.assign(new Error('Ruta no encontrada'), { status: 404 })));
  app.use((error, _request, response, _next) => {
    const status = error.type === 'entity.parse.failed' ? 400 : error.type === 'entity.too.large' ? 413 : error.status || (error.code === 'ER_DUP_ENTRY' ? 409 : 500);
    if (status >= 500) console.error('API error:', error.code || error.name);
    response.status(status).json({ success: false, error: { message: status >= 500 ? 'Servicio no disponible' : status === 409 ? 'El usuario ya existe' : status === 400 && error.type ? 'JSON inválido' : error.message } });
  });
  return app;
}
