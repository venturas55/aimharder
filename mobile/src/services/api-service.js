const baseUrl = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '');

export async function request(path, { token, method = 'GET', body } = {}) {
  if (!baseUrl || !/^https?:\/\//.test(baseUrl)) throw new Error('Configura EXPO_PUBLIC_API_URL en mobile/.env');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${baseUrl}${path}`, { method, signal: controller.signal,
      headers: { Accept: 'application/json', ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}) });
    const data = await response.json().catch(() => null);
    if (!response.ok || !data?.success) throw Object.assign(new Error(data?.error?.message || 'Respuesta inesperada del servidor'), { status: response.status });
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Tiempo de espera agotado. Comprueba conexión.');
    if (error instanceof TypeError) throw new Error('No se puede conectar. Comprueba red y dirección de la API.');
    throw error;
  } finally { clearTimeout(timeout); }
}
