import Link from "next/link";
import { LineChart, type Series } from "@/components/LineChart";
import { Logo } from "@/components/Logo";
import { RunStatus } from "@/components/RunStatus";
import { BENCHMARK_ID, colorMap } from "@/lib/colors";
import { computeMetrics, getEquity, getRuns, getStrategies } from "@/lib/data";
import { eur, pct, tone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [strategies, equity, runs] = await Promise.all([getStrategies(), getEquity(), getRuns(1)]);
  if (!strategies.length) {
    return (
      <main>
        <h1 className="brand"><Logo />Stratégies</h1>
        <div className="card empty">Aucune donnée pour l&apos;instant. Lance le workflow GitHub « Daily run » pour initialiser le bot.</div>
      </main>
    );
  }
  const colors = colorMap(strategies);
  const byId = Object.fromEntries(strategies.map((s) => [s.id, equity.filter((e) => e.strategy_id === s.id)]));
  const rows = strategies
    .map((s) => ({ s, m: computeMetrics(byId[s.id], s.initial_capital) }))
    .sort((a, b) => (b.m?.ret ?? -1) - (a.m?.ret ?? -1));
  const bench = rows.find((r) => r.s.id === BENCHMARK_ID)?.m;

  // Données du graphique : une ligne par date, une colonne par stratégie (valeur en €), indexée à la création
  const dates = [...new Set(equity.map((e) => e.date))].sort();
  const table = dates.map((date) => {
    const r: { date: string; [k: string]: string | number | null } = { date };
    for (const s of strategies) r[s.id] = null;
    return r;
  });
  const idx = Object.fromEntries(dates.map((d, i) => [d, i]));
  for (const e of equity) table[idx[e.date]][e.strategy_id] = e.equity_eur;
  const series: Series[] = strategies.map((s) => ({ key: s.id, name: s.name, color: colors[s.id], dashed: s.id === BENCHMARK_ID }));

  const totalCapital = strategies.reduce((a, s) => a + s.initial_capital, 0);
  const totalEquity = rows.reduce((a, r) => a + (r.m?.equity ?? r.s.initial_capital), 0);

  return (
    <main>
      <h1 className="brand"><Logo />Stratégies</h1>
      <RunStatus run={runs[0]} />

      <div className="card" style={{ marginTop: 16 }}>
        <p className="sub">Valeur cumulée des {strategies.length} portefeuilles fictifs</p>
        <div className="hero num">{eur(totalEquity)}</div>
        <p className={`num ${tone(totalEquity / totalCapital - 1)}`}>{pct(totalEquity / totalCapital - 1, 2)} <span className="muted">sur {eur(totalCapital)} investis</span></p>
      </div>

      <div className="split">
      <section>
      <h2>Performance comparée</h2>
      <div className="card">
        <LineChart data={table} series={series} mode="pct" />
      </div>
      </section>

      <section>
      <h2>Classement</h2>
      <div className="list">
        {rows.map(({ s, m }, i) => (
          <Link key={s.id} href={`/s/${s.id}`} className="strat">
            <span className={`swatch ${s.id === BENCHMARK_ID ? "ref" : ""}`} style={{ background: s.id === BENCHMARK_ID ? undefined : colors[s.id] }} />
            <div style={{ minWidth: 0 }}>
              <div className="name ellip"><span className="rank">{i + 1}</span>{s.name}</div>
              <div className="sub num">
                {eur(m?.equity ?? s.initial_capital)} · investi {pct(m?.invested ?? 0, 0, false)}
                {bench && s.id !== BENCHMARK_ID && m ? <> · <span className={tone(m.ret - bench.ret)}>{pct(m.ret - bench.ret)} vs bench.</span></> : null}
              </div>
            </div>
            <div className="right num">
              <div className={`big ${tone(m?.ret)}`}>{pct(m?.ret ?? 0)}</div>
              <div className={`sub ${tone(m?.ret1d)}`}>{m?.ret1d != null ? `${pct(m.ret1d)} 1j` : "–"}</div>
            </div>
          </Link>
        ))}
      </div>
      </section>
      </div>
    </main>
  );
}
