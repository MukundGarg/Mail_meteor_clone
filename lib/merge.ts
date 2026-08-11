export function mergeText(input: string, data: Record<string, unknown>) {
  return input.replace(/{{\s*([^{}]+?)\s*}}/g, (_, key) => String(data[key] ?? ''));
}
export function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c] as string));
}
export function textToHtml(s: string) { return escapeHtml(s).replace(/\n/g, '<br>'); }
export function spreadsheetIdFrom(input: string) {
  const m = input.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
  return m?.[1] ?? input.trim();
}
