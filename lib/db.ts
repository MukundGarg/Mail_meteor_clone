import { Pool } from 'pg';

const globalForDb = globalThis as unknown as { pool?: Pool };
export const db = globalForDb.pool ?? new Pool({ connectionString: process.env.DATABASE_URL });
if (process.env.NODE_ENV !== 'production') globalForDb.pool = db;

export async function one<T = any>(text: string, params: any[] = []): Promise<T | null> {
  const result = await db.query(text, params);
  return (result.rows[0] as T) ?? null;
}

export async function many<T = any>(text: string, params: any[] = []): Promise<T[]> {
  const result = await db.query(text, params);
  return result.rows as T[];
}
