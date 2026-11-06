import postgres from "postgres";

type Sql = ReturnType<typeof postgres>;

declare global {
  // eslint-disable-next-line no-var
  var _sql: Sql | undefined;
}

function db(): Sql {
  if (globalThis._sql) return globalThis._sql;
  const raw = process.env.DATABASE_URL ?? process.env.POSTGRES_URL;
  if (!raw) throw new Error("DATABASE_URL manquante");
  // Neon ajoute `channel_binding=require`, que postgres.js transmettrait tel quel au serveur
  // (« unrecognized configuration parameter »). On ne garde que les paramètres utiles.
  const u = new URL(raw);
  u.searchParams.delete("channel_binding");
  u.searchParams.delete("sslmode");
  const url = u.toString();
  const local = /localhost|127\.0\.0\.1/.test(u.hostname);
  return (globalThis._sql = postgres(url, { ssl: local ? false : "require", max: 1, prepare: false, idle_timeout: 20 }));
}

// Connexion ouverte à la première requête (pas au build)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const sql = ((strings: TemplateStringsArray, ...values: any[]) => (db() as any)(strings, ...values)) as unknown as Sql;
