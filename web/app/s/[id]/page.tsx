import Link from "next/link";
import { notFound } from "next/navigation";
import { LineChart } from "@/components/LineChart";
import { OrderItem } from "@/components/OrderItem";
import { BENCHMARK_ID, colorMap } from "@/lib/colors";
import { computeMetrics, getEquity, getJournal, getOrders, getPositions, getStrategies, getStrategy } from "@/lib/data";
import { dateFr, eur, num, pct, tone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function StrategyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = await getStrategy(id);
  if (!s) notFound();
  const [all, equity, bench, positions, orders, journal] = await Promise.all([
    getStrategies(), getEquity(id), id === BENCHMARK_ID ? Promise.resolve([]) : getEquity(BENCHMARK_ID),
    getPositions(id), getOrders({ strategyId: id, limit: 40 }), getJournal(id, 10),
  ]);
  const color = colorMap(all)[id];
  const m = computeMetrics(equity, s.initial_capital);
  const benchMap = Object.fromEntries(bench.map((b) => [b.date, b.equity_eur]));
  const data = equity.map((e) => ({ date: e.date, [id]: e.equity_eur, ...(bench.length ? { bench: benchMap[e.date] ?? null } : {}) }));
  const series = [
    { key: id, name: s.name, color, dashed: id === BENCHMARK_ID },
    ...(bench.length ? [{ key: "bench", name: "Benchmark", color: "var(--series-ref)", dashed: true }] : []),
  ];
  const pending = orders.filter((o) => o.status === "pending");
  const filled = orders.filter((o) => o.status === "filled");
  const invested = positions.reduce((a, p) => a + (p.value_eur ?? 0), 0);

  return (
    <main>
      <Link href="/" className="sub">← Stratégies</Link>
      <h1>{s.name}</h1>
      <p className="sub">{s.description}</p>

      <div className="split">
      <section>
      <div className="card" style={{ marginTop: 16 }}>
        <div className="hero num">{eur(m?.equity ?? s.initial_capital)}</div>
        <p className={`num ${tone(m?.ret)}`}>{pct(m?.ret ?? 0, 2)} <span className="muted">depuis le début ({m?.days ?? 0} j)</span></p>
        <div style={{ marginTop: 12 }}>
          <LineChart data={data} series={series} mode="pct" />
        </div>
      </div>

      <div className="grid2 grid4" style={{ marginTop: 10 }}>
        <div className="card kpi"><div className="label">1 jour</div><div className={`value num ${tone(m?.ret1d)}`}>{pct(m?.ret1d)}</div></div>
        <div className="card kpi"><div className="label">1 semaine</div><div className={`value num ${tone(m?.ret1w)}`}>{pct(m?.ret1w)}</div></div>
        <div className="card kpi"><div className="label">Drawdown max</div><div className="value num">{pct(m?.maxDD ?? 0, 1, false)}</div></div>
        <div className="card kpi"><div className="label">Cash</div><div className="value num">{eur(s.cash_eur)}</div></div>
      </div>
      </section>

      <section>
      <h2>Positions ({positions.length})</h2>
      {positions.length ? (
        <div className="list">
          {positions.map((p) => {
            const pnl = p.last_price_eur != null ? p.last_price_eur / p.avg_cost_eur - 1 : null;
            const w = m?.equity ? (p.value_eur ?? 0) / m.equity : 0;
            return (
              <div key={p.symbol} className="row">
                <div>
                  <div className="ellip"><b>{p.symbol}</b> <span className="sub">{p.name}</span></div>
                  <div className="sub num">{num(p.quantity, 4)} · PRU {eur(p.avg_cost_eur, 2)} · depuis le {dateFr(p.opened_at)}</div>
                </div>
                <div className="num" style={{ textAlign: "right" }}>
                  <div>{eur(p.value_eur)}</div>
                  <div className="sub"><span className={tone(pnl)}>{pct(pnl)}</span> · {pct(w, 0, false)}</div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="card sub">Aucune position{invested === 0 ? " : portefeuille 100 % cash." : "."}</div>
      )}
      </section>
      </div>

      <div className={pending.length || journal.length ? "split even" : ""}>
      <section>

      {pending.length > 0 && (
        <>
          <h2>Ordres en attente ({pending.length})</h2>
          <p className="sub" style={{ marginTop: -4, marginBottom: 10 }}>Exécutés à l&apos;ouverture de la prochaine séance.</p>
          <div className="list">{pending.map((o) => <OrderItem key={o.id} o={o} />)}</div>
        </>
      )}

      {journal.length > 0 && (
        <>
          <h2>Journal</h2>
          <div className="list">
            {journal.map((j) => (
              <div key={j.date}><div className="sub">{dateFr(j.date)}</div><p>{j.note}</p></div>
            ))}
          </div>
        </>
      )}

      </section>

      <section>
      <h2>Transactions</h2>
      {filled.length ? <div className="list">{filled.map((o) => <OrderItem key={o.id} o={o} />)}</div> : <div className="card sub">Aucune transaction pour l&apos;instant.</div>}
      </section>
      </div>
    </main>
  );
}
