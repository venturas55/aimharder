import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

export function createTokens(secret, ttl = 604800) {
  if (!secret || secret.length < 32) throw new Error('TOKEN_SECRET debe tener al menos 32 caracteres');
  if (!Number.isInteger(ttl) || ttl < 60 || ttl > 2592000) throw new Error('TOKEN_TTL_SECONDS inválido');
  function sign(value) { return createHmac('sha256', secret).update(value).digest('base64url'); }
  return {
    issue(id) {
      const payload = Buffer.from(JSON.stringify({ sub: id, exp: Math.floor(Date.now() / 1000) + ttl, nonce: randomBytes(16).toString('hex') })).toString('base64url');
      return `${payload}.${sign(payload)}`;
    },
    verify(token) {
      try {
        const [payload, signature, extra] = token.split('.');
        if (extra || !signature || signature.length !== 43) return null;
        if (!timingSafeEqual(Buffer.from(signature), Buffer.from(sign(payload)))) return null;
        const data = JSON.parse(Buffer.from(payload, 'base64url').toString());
        return Number.isSafeInteger(data.sub) && data.sub > 0 && data.exp > Date.now() / 1000 ? data.sub : null;
      } catch { return null; }
    },
  };
}
