import { sql } from "./db";

export type Strategy = { id: string; name: string; description: string; initial_capital: number; cash_eur: number };
export type EquityPoint = { strategy_id: string; date: string; equity_eur: number; cash_eur: number; invested_eur: number };
export type Position = { strategy_id: string; symbol: string; name: string | null; quantity: number; avg_cost_eur: number; opened_at: string; last_price_eur: number | null; value_eur: number | null };
export type Order = { id: number; strategy_id: string; symbol: string; side: string; quantity: number; created_at: string; status: string; filled_at: string | null; price_local: number | null; price_eur: number | null; fees_eur: number | null; realized_pnl_eur: number | null; reason: string | null };
export type JournalEntry = { strategy_id: string; date: string; note: string };
export type MarketRow = { symbol: string; name: string; currency: string; asset_class: string; region: string; date: string; close: number; close_eur: number; ret_1d: number | null; ret_1w: number | null; ret_1m: number | null; ret_3m: number | null; ret_6m: number | null; rsi14: number | null; above_sma200: boolean | null; vol_60d: number | null; score: number | null; summary: string | null; headlines: string | null };
export type Run = { id: number; started_at: string; finished_at: string | null; status: string; message: string | null };


export async function getStrategies() {
  return sql<Strategy[]>`select id, name, description, initial_capital, cash_eur from strategies order by created_at, id`;
}

export async function getStrategy(id: string) {
  const rows = await sql<Strategy[]>`select id, name, description, initial_capital, cash_eur from strategies where id = ${id}`;
  return rows[0] ?? null;
}

export async function getEquity(id?: string) {
  return id
    ? sql<EquityPoint[]>`select strategy_id, to_char(date, 'YYYY-MM-DD') as date, equity_eur, cash_eur, invested_eur from equity where strategy_id = ${id} order by date`
    : sql<EquityPoint[]>`select strategy_id, to_char(date, 'YYYY-MM-DD') as date, equity_eur, cash_eur, invested_eur from equity order by date`;
}

export async function getPositions(id: string) {
  return sql<Position[]>`
    select p.strategy_id, p.symbol, m.name, p.quantity, p.avg_cost_eur, to_char(p.opened_at, 'YYYY-MM-DD') as opened_at, p.last_price_eur, p.value_eur
    from positions p left join market m on m.symbol = p.symbol
    where p.strategy_id = ${id} order by p.value_eur desc nulls last`;
}

export async function getOrders(opts: { strategyId?: string; limit?: number } = {}) {
  const limit = opts.limit ?? 50;
  return opts.strategyId
    ? sql<Order[]>`select id, strategy_id, symbol, side, quantity, to_char(created_at, 'YYYY-MM-DD') as created_at, status, to_char(filled_at, 'YYYY-MM-DD') as filled_at, price_local, price_eur, fees_eur, realized_pnl_eur, reason
        from orders where strategy_id = ${opts.strategyId} and status <> 'cancelled' order by id desc limit ${limit}`
    : sql<Order[]>`select id, strategy_id, symbol, side, quantity, to_char(created_at, 'YYYY-MM-DD') as created_at, status, to_char(filled_at, 'YYYY-MM-DD') as filled_at, price_local, price_eur, fees_eur, realized_pnl_eur, reason
        from orders where status <> 'cancelled' order by id desc limit ${limit}`;
}

export async function getJournal(id: string, limit = 20) {
  return sql<JournalEntry[]>`select strategy_id, to_char(date, 'YYYY-MM-DD') as date, note from journal where strategy_id = ${id} order by date desc limit ${limit}`;
}

export async function getMarket() {
  return sql<MarketRow[]>`
    select m.symbol, m.name, m.currency, m.asset_class, m.region, to_char(m.date, 'YYYY-MM-DD') as date, m.close, m.close_eur,
           m.ret_1d, m.ret_1w, m.ret_1m, m.ret_3m, m.ret_6m, m.rsi14, m.above_sma200, m.vol_60d,
           s.score, s.summary, s.headlines
    from market m
    left join lateral (select score, summary, headlines from sentiment where symbol = m.symbol order by date desc limit 1) s on true
    order by m.asset_class, m.region, m.symbol`;
}

export async function getPrices(symbol: string) {
  return sql<{ date: string; close: number }[]>`select to_char(date, 'YYYY-MM-DD') as date, close from prices where symbol = ${symbol} order by date`;
}

export async function getRuns(limit = 15) {
  return sql<Run[]>`select id, started_at::text, finished_at::text, status, message from runs order by id desc limit ${limit}`;
}

// ------------------------------------------------------------------ métriques
export type Metrics = {
  equity: number;
  ret: number; // depuis le début
  ret1d: number | null;
  ret1w: number | null;
  maxDD: number;
  invested: number; // part investie
  days: number;
};

export function computeMetrics(points: EquityPoint[], initial: number): Metrics | null {
  if (!points.length) return null;
  const last = points[points.length - 1];
  const at = (back: number) => (points.length > back ? points[points.length - 1 - back].equity_eur : null);
  let peak = initial, maxDD = 0;
  for (const p of points) {
    peak = Math.max(peak, p.equity_eur);
    maxDD = Math.min(maxDD, p.equity_eur / peak - 1);
  }
  const d1 = at(1), d7 = at(5);
  return {
    equity: last.equity_eur,
    ret: last.equity_eur / initial - 1,
    ret1d: d1 ? last.equity_eur / d1 - 1 : null,
    ret1w: d7 ? last.equity_eur / d7 - 1 : null,
    maxDD,
    invested: last.equity_eur > 0 ? last.invested_eur / last.equity_eur : 0,
    days: points.length,
  };
}
