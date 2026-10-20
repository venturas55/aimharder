import { randomBytes, scrypt, pbkdf2, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';

const deriveScrypt = promisify(scrypt);
const derivePbkdf2 = promisify(pbkdf2);

// Werkzeug-compatible hashes allow Flask and Node to share existing accounts.
export async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const key = await deriveScrypt(password, salt, 64, { N: 32768, r: 8, p: 1, maxmem: 64 * 1024 * 1024 });
  return `scrypt:32768:8:1$${salt}$${key.toString('hex')}`;
}

export async function verifyPassword(password, stored) {
  try {
    const [method, salt, hex, extra] = String(stored).split('$');
    if (extra || !salt || !/^[a-f0-9]+$/i.test(hex) || hex.length % 2) return false;
    const expected = Buffer.from(hex, 'hex');
    const parts = method.split(':');
    let actual;
    if (parts[0] === 'scrypt' && parts.length === 4 && expected.length === 64) {
      const [N, r, p] = parts.slice(1).map(Number);
      if (![16384, 32768, 65536].includes(N) || r !== 8 || p < 1 || p > 4) return false;
      actual = await deriveScrypt(password, salt, 64, { N, r, p, maxmem: 128 * 1024 * 1024 });
    } else if (parts[0] === 'pbkdf2' && parts.length === 3) {
      const iterations = Number(parts[2]);
      if (!['sha256', 'sha512', 'sha1'].includes(parts[1]) || !Number.isInteger(iterations) || iterations < 1 || iterations > 2000000) return false;
      actual = await derivePbkdf2(password, salt, iterations, expected.length, parts[1]);
    } else return false;
    return actual.length === expected.length && timingSafeEqual(actual, expected);
  } catch { return false; }
}
