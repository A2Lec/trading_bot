import type { Order } from "@/lib/data";
import { dateFr, eur, num, tone } from "@/lib/format";

export function OrderItem({ o, strategyName }: { o: Order; strategyName?: string }) {
  const pending = o.status === "pending";
  return (
    <div className="order">
      <div className="row">
        <div className="ellip">
          <span className={`pill ${pending ? "pending" : o.side}`}>{pending ? "En attente" : o.side === "buy" ? "Achat" : "Vente"}</span>{" "}
          <b className="nowrap">{o.symbol}</b>
        </div>
        <div className="sub num">{pending ? `décidé le ${dateFr(o.created_at)}` : dateFr(o.filled_at)}</div>
      </div>
      <div className="row sub num">
        <div className="ellip">× {num(o.quantity, 4)}{strategyName ? ` · ${strategyName}` : ""}</div>
        <div>
          {o.realized_pnl_eur != null && <span className={tone(o.realized_pnl_eur)}>{eur(o.realized_pnl_eur, 2)} · </span>}
          {!pending && eur((o.price_eur ?? 0) * o.quantity)}
        </div>
      </div>
      {o.reason && <p className="reason">{o.reason}</p>}
    </div>
  );
}
