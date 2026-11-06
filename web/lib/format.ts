export const eur = (v: number | null | undefined, digits = 0) =>
  v == null ? "–" : v.toLocaleString("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: digits, minimumFractionDigits: digits });

export const pct = (v: number | null | undefined, digits = 1, sign = true) =>
  v == null ? "–" : `${sign && v > 0 ? "+" : ""}${(v * 100).toLocaleString("fr-FR", { maximumFractionDigits: digits, minimumFractionDigits: digits })} %`;

export const num = (v: number | null | undefined, digits = 2) =>
  v == null ? "–" : v.toLocaleString("fr-FR", { maximumFractionDigits: digits });

export const tone = (v: number | null | undefined) => (v == null || Math.abs(v) < 1e-9 ? "" : v > 0 ? "up" : "down");

export const dateFr = (d: string | null) =>
  d ? new Date(d + (d.length === 10 ? "T12:00:00" : "")).toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) : "–";

// Couleur fixe par stratégie (suit l'entité, jamais le rang). Le benchmark est une ligne de référence grise en pointillés.
export const seriesVar = (index: number, isBenchmark: boolean) => (isBenchmark ? "var(--series-ref)" : `var(--series-${(index % 8) + 1})`);
