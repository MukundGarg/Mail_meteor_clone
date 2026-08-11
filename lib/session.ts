import crypto from 'crypto';
import { cookies } from 'next/headers';

const COOKIE = 'mm_session';
function secret() {
  const s = process.env.SESSION_SECRET;
  if (!s) throw new Error('SESSION_SECRET is required');
  return s;
}
function sign(value: string) {
  return crypto.createHmac('sha256', secret()).update(value).digest('hex');
}
export async function setSession(userId: string) {
  const payload = Buffer.from(JSON.stringify({ userId, exp: Date.now() + 30 * 24 * 3600_000 })).toString('base64url');
  const store = await cookies();
  store.set(COOKIE, `${payload}.${sign(payload)}`, { httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/', maxAge: 30 * 24 * 3600 });
}
export async function clearSession() {
  const store = await cookies();
  store.delete(COOKIE);
}
export async function getSessionUserId(): Promise<string | null> {
  const store = await cookies();
  const raw = store.get(COOKIE)?.value;
  if (!raw) return null;
  const [payload, sig] = raw.split('.');
  if (!payload || !sig || !crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(sign(payload)))) return null;
  try {
    const parsed = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'));
    if (!parsed.userId || parsed.exp < Date.now()) return null;
    return parsed.userId;
  } catch { return null; }
}
