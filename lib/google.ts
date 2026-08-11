import { google } from 'googleapis';
import { decrypt } from './crypto';
import { one } from './db';

export function oauthClient() {
  return new google.auth.OAuth2(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET, process.env.GOOGLE_REDIRECT_URI);
}

export function googleAuthUrl(state: string) {
  return oauthClient().generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent',
    state,
    scope: [
      'openid', 'email', 'profile',
      'https://www.googleapis.com/auth/gmail.send',
      'https://www.googleapis.com/auth/spreadsheets'
    ]
  });
}

export async function clientForUser(userId: string) {
  const user = await one<{ google_refresh_token: string }>('SELECT google_refresh_token FROM users WHERE id=$1', [userId]);
  if (!user) throw new Error('User not found');
  const client = oauthClient();
  client.setCredentials({ refresh_token: decrypt(user.google_refresh_token) });
  return client;
}

export async function readSheet(userId: string, spreadsheetId: string, sheetName: string) {
  const auth = await clientForUser(userId);
  const sheets = google.sheets({ version: 'v4', auth });
  const res = await sheets.spreadsheets.values.get({ spreadsheetId, range: `'${sheetName.replaceAll("'", "''")}'` });
  return res.data.values ?? [];
}

export async function getSheetNames(userId: string, spreadsheetId: string) {
  const auth = await clientForUser(userId);
  const sheets = google.sheets({ version: 'v4', auth });
  const res = await sheets.spreadsheets.get({ spreadsheetId, fields: 'sheets.properties.title' });
  return (res.data.sheets ?? []).map(s => s.properties?.title).filter(Boolean) as string[];
}

export async function ensureStatusColumns(userId: string, spreadsheetId: string, sheetName: string, headers: string[]) {
  const required = ['Status', 'Sent At', 'Error'];
  const missing = required.filter(h => !headers.includes(h));
  if (!missing.length) return [...headers];
  const auth = await clientForUser(userId);
  const sheets = google.sheets({ version: 'v4', auth });
  const next = [...headers, ...missing];
  await sheets.spreadsheets.values.update({ spreadsheetId, range: `'${sheetName.replaceAll("'", "''")}'!1:1`, valueInputOption: 'RAW', requestBody: { values: [next] } });
  return next;
}

function colLetter(index: number) {
  let n = index + 1, s = '';
  while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

export async function updateRecipientRow(userId: string, spreadsheetId: string, sheetName: string, rowNumber: number, headers: string[], status: string, sentAt: string, error: string) {
  const auth = await clientForUser(userId);
  const sheets = google.sheets({ version: 'v4', auth });
  const indices = ['Status', 'Sent At', 'Error'].map(h => headers.indexOf(h));
  const start = Math.min(...indices), end = Math.max(...indices);
  const vals = Array(end - start + 1).fill('');
  vals[indices[0] - start] = status;
  vals[indices[1] - start] = sentAt;
  vals[indices[2] - start] = error;
  await sheets.spreadsheets.values.update({ spreadsheetId, range: `'${sheetName.replaceAll("'", "''")}'!${colLetter(start)}${rowNumber}:${colLetter(end)}${rowNumber}`, valueInputOption: 'RAW', requestBody: { values: [vals] } });
}

export async function sendGmail(userId: string, to: string, subject: string, html: string) {
  const auth = await clientForUser(userId);
  const gmail = google.gmail({ version: 'v1', auth });
  const mime = [
    `To: ${to}`,
    `Subject: ${subject.replace(/[\r\n]+/g, ' ')}`,
    'MIME-Version: 1.0',
    'Content-Type: text/html; charset=UTF-8',
    '',
    html
  ].join('\r\n');
  const raw = Buffer.from(mime).toString('base64url');
  return gmail.users.messages.send({ userId: 'me', requestBody: { raw } });
}
