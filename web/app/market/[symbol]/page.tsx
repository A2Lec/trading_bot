import Link from "next/link";
import { notFound } from "next/navigation";
import { LineChart } from "@/components/LineChart";
import { getMarket, getPrices } from "@/lib/data";
import { num, pct, tone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function AssetPage({ params }: { params: Promise<{ symbol: string }> }) {
  const symbol = decodeURIComponent((await params).symbol);
  const [market, prices] = await Promise.all([getMarket(), getPrices(symbol)]);
  const a = market.find((m) => m.symbol === symbol);
  if (!a) notFound();
  const headlines: { title: string; source: string; url: string | null }[] = a.headlines ? JSON.parse(a.headlines) : [];
  const stats = [
    ["1 sem.", a.ret_1w], ["1 mois", a.ret_1m], ["3 mois", a.ret_3m], ["6 mois", a.ret_6m],
  ] as const;
  return (
    <main>
      <Link href="/market" className="sub">← Marché</Link>
      <h1>{a.name}</h1>
      <p className="sub">{a.symbol} · {a.region} · {a.currency}</p>
      <div className="card" style={{ marginTop: 16 }}>
        <div className="hero num">{num(a.close)} <span className="muted" style={{ fontSize: 16 }}>{a.currency}</span></div>
        <p className={`num ${tone(a.ret_1d)}`}>{pct(a.ret_1d, 2)} <span className="muted">aujourd&apos;hui</span></p>
        <div style={{ marginTop: 12 }}>
          <LineChart data={prices.map((p) => ({ date: p.date, close: p.close }))} series={[{ key: "close", name: a.name, color: "var(--series-1)" }]} mode="value" unit={a.currency} />
        </div>
      </div>
      <div className="grid2 grid4" style={{ marginTop: 10 }}>
        {stats.map(([l, v]) => (
          <div key={l} className="card kpi"><div className="label">{l}</div><div className={`value num ${tone(v)}`}>{pct(v)}</div></div>
        ))}
        <div className="card kpi"><div className="label">RSI 14</div><div className="value num">{num(a.rsi14, 0)}</div></div>
        <div className="card kpi"><div className="label">Volatilité 60j</div><div className="value num">{pct(a.vol_60d, 0, false)}</div></div>
        <div className="card kpi"><div className="label">Tendance</div><div className={`value ${a.above_sma200 ? "up" : "down"}`}>{a.above_sma200 ? "> MM200" : "< MM200"}</div></div>
        <div className="card kpi"><div className="label">Score news</div><div className={`value num ${tone(a.score)}`}>{a.score != null ? a.score.toFixed(2) : "–"}</div></div>
      </div>
      {a.summary && (
        <>
          <h2>Analyse Gemini</h2>
          <div className="card"><p>{a.summary}</p></div>
        </>
      )}
      {headlines.length > 0 && (
        <>
          <h2>Actualités</h2>
          <div className="list">
            {headlines.map((h, i) => (
              <a key={i} href={h.url ?? "#"} target="_blank" rel="noreferrer">
                <p>{h.title}</p><p className="sub">{h.source}</p>
              </a>
            ))}
          </div>
        </>
      )}
    </main>
  );
}
