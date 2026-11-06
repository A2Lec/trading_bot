export const COOKIE = "tb_auth";

export async function tokenFor(password: string): Promise<string> {
  const data = new TextEncoder().encode(`trading-bot:${password}`);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map((b) => b.toString(16).padStart(2, "0")).join("");
}
