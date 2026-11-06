import type { Order } from "@/lib/data";
import { dateFr, eur, num, tone } from "@/lib/format";

export function OrderItem({ o, strategyName }: { o: Order; strategyName?: string }) {
  const pending = o.status === "pending";
  return (
    <div>
      <div className="row">
        <div>
          <span className={`pill ${pending ? "pending" : o.side}`}>{pending ? "En attente" : o.side === "buy" ? "Achat" : "Vente"}</span>{" "}
          <b>{o.symbol}</b> <span className="sub num">× {num(o.quantity, 4)}</span>
        </div>
        <div className="sub num" style={{ textAlign: "right" }}>
          {pending ? `décidé le ${dateFr(o.created_at)}` : `${dateFr(o.filled_at)} · ${eur((o.price_eur ?? 0) * o.quantity)}`}
        </div>
      </div>
      {(strategyName || o.realized_pnl_eur != null) && (
        <div className="sub num" style={{ marginTop: 2 }}>
          {strategyName}
          {o.realized_pnl_eur != null && (
            <>{strategyName ? " · " : ""}P&amp;L réalisé <span className={tone(o.realized_pnl_eur)}>{eur(o.realized_pnl_eur, 2)}</span></>
          )}
        </div>
      )}
      {o.reason && <p className="reason">{o.reason}</p>}
    </div>
  );
}
