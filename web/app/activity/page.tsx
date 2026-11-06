import { OrderItem } from "@/components/OrderItem";
import { getOrders, getRuns, getStrategies } from "@/lib/data";

export const dynamic = "force-dynamic";

const STATUS: Record<string, string> = { success: "✓ OK", partial: "⚠ Partiel", error: "✕ Erreur", running: "… En cours" };

export default async function Activity() {
  const [orders, runs, strategies] = await Promise.all([getOrders({ limit: 60 }), getRuns(15), getStrategies()]);
  const names = Object.fromEntries(strategies.map((s) => [s.id, s.name]));
  return (
    <main>
      <h1>Activité</h1>
      <p className="sub">Derniers ordres de toutes les stratégies</p>

      <div className="split">
      <section>
      <h2>Ordres</h2>
      {orders.length ? (
        <div className="list">{orders.map((o) => <OrderItem key={o.id} o={o} strategyName={names[o.strategy_id]} />)}</div>
      ) : <div className="card sub">Aucun ordre.</div>}

      </section>
      <section>
      <h2>Exécutions du bot</h2>
      <div className="list">
        {runs.map((r) => {
          const start = new Date(r.started_at);
          const dur = r.finished_at ? Math.round((new Date(r.finished_at).getTime() - start.getTime()) / 1000) : null;
          return (
            <details key={r.id}>
              <summary className="row">
                <span>{start.toLocaleString("fr-FR", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                <span className={`sub ${r.status === "success" ? "up" : r.status === "running" ? "" : "down"}`}>
                  {STATUS[r.status] ?? r.status}{dur != null ? ` · ${dur} s` : ""}
                </span>
              </summary>
              {r.message && <pre className="log">{r.message}</pre>}
            </details>
          );
        })}
      </div>
      </section>
      </div>
    </main>
  );
}
