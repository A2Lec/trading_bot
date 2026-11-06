import type { Strategy } from "./data";
import { seriesVar } from "./format";

export const BENCHMARK_ID = "buy_hold";

/** Couleur stable par stratégie, basée sur l'ordre de création (pas sur le classement). */
export function colorMap(strategies: Strategy[]): Record<string, string> {
  const out: Record<string, string> = {};
  let i = 0;
  for (const s of strategies) out[s.id] = s.id === BENCHMARK_ID ? seriesVar(0, true) : seriesVar(i++, false);
  return out;
}
