import { config } from 'dotenv';

config({ path: '.env.local' });
const base = process.env.APP_URL || 'http://localhost:3000';
const secret = process.env.CRON_SECRET;
if (!secret) throw new Error('CRON_SECRET is required');

async function tick() {
  try {
    const res = await fetch(`${base}/api/cron/process`, { headers: { authorization: `Bearer ${secret}` } });
    const text = await res.text();
    console.log(new Date().toISOString(), res.status, text);
  } catch (err) {
    console.error(err);
  }
}
await tick();
setInterval(tick, 15000);
