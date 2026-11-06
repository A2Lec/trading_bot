import Link from "next/link";
import { getMarket } from "@/lib/data";
import { num, pct, tone } from "@/lib/format";

export const dynamic = "force-dynamic";

const CLASSES: Record<string, string> = { equity: "Actions", etf: "ETF indices", bond: "Obligations", commodity: "Matières premières", crypto: "Crypto" };

function Score({ v }: { v: number | null }) {
  if (v == null) return <span className="pill">news –</span>;
  const label = v >= 0.4 ? "positif" : v <= -0.2 ? "négatif" : "neutre";
  return <span className={`pill ${v >= 0.4 ? "buy" : v <= -0.2 ? "sell" : ""}`}>news {v > 0 ? "+" : ""}{v.toFixed(1)} {label}</span>;
}

export default async function Market() {
  const rows = await getMarket();
  const groups = Object.keys(CLASSES).map((k) => ({ k, items: rows.filter((r) => r.asset_class === k) })).filter((g) => g.items.length);
  return (
    <main>
      <h1>Marché</h1>
      <p className="sub">{rows.length} actifs suivis · cours au {rows[0]?.date ?? "–"} · score news analysé par Gemini</p>
      {groups.map((g) => (
        <section key={g.k}>
          <h2>{CLASSES[g.k]}</h2>
          <div className="list">
            {g.items.map((r) => (
              <Link key={r.symbol} href={`/market/${encodeURIComponent(r.symbol)}`}>
                <div className="row">
                  <div style={{ minWidth: 0 }}>
                    <b>{r.symbol}</b> <span className="sub">{r.name}</span>
                    <div style={{ marginTop: 4, display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <span className={`pill ${r.above_sma200 ? "buy" : "sell"}`}>{r.above_sma200 ? "▲ > MM200" : "▼ < MM200"}</span>
                      {r.rsi14 != null && <span className="pill">RSI {r.rsi14.toFixed(0)}</span>}
                      <Score v={r.score} />
                    </div>
                  </div>
                  <div className="num" style={{ textAlign: "right", flex: "none" }}>
                    <div>{num(r.close)} <span className="muted" style={{ fontSize: 11 }}>{r.currency}</span></div>
                    <div className="sub"><span className={tone(r.ret_1d)}>{pct(r.ret_1d)}</span> · <span className={tone(r.ret_1m)}>{pct(r.ret_1m, 0)} 1m</span></div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </main>
  );
}
