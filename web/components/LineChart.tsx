"use client";
import { useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart as RLineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export type Series = { key: string; name: string; color: string; dashed?: boolean };
type Row = { date: string } & Record<string, number | string | null>;

const RANGES = [
  { label: "1S", days: 7 },
  { label: "1M", days: 31 },
  { label: "3M", days: 92 },
  { label: "1A", days: 366 },
  { label: "Tout", days: 0 },
];

const fmtDate = (d: string) => new Date(d + "T12:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" });

/**
 * Courbe(s) dans le temps. mode "pct" : chaque série est ré-indexée à 0 % au début de la période affichée.
 */
export function LineChart({ data, series, mode = "pct", unit = "€" }: { data: Row[]; series: Series[]; mode?: "pct" | "value"; unit?: string }) {
  const [range, setRange] = useState(RANGES[RANGES.length - 1].label);

  const rows = useMemo(() => {
    const days = RANGES.find((r) => r.label === range)!.days;
    let slice = data;
    if (days && data.length) {
      const end = new Date(data[data.length - 1].date + "T12:00:00").getTime();
      slice = data.filter((r) => end - new Date(r.date + "T12:00:00").getTime() <= days * 86400000);
    }
    if (mode !== "pct") return slice;
    const base: Record<string, number> = {};
    return slice.map((r) => {
      const out: Row = { date: r.date };
      for (const s of series) {
        const v = r[s.key];
        if (typeof v !== "number") { out[s.key] = null; continue; }
        base[s.key] ??= v;
        out[s.key] = base[s.key] ? (v / base[s.key] - 1) * 100 : null;
      }
      return out;
    });
  }, [data, series, range, mode]);

  const fmt = (v: number) =>
    mode === "pct"
      ? `${v > 0 ? "+" : ""}${v.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`
      : `${v.toLocaleString("fr-FR", { maximumFractionDigits: 2 })} ${unit}`;

  if (data.length < 2) {
    return <p className="sub" style={{ padding: "24px 0", textAlign: "center" }}>La courbe apparaîtra après quelques jours de fonctionnement.</p>;
  }

  return (
    <div>
      <div className="tabs" role="tablist">
        {RANGES.map((r) => (
          <button key={r.label} className={r.label === range ? "active" : ""} onClick={() => setRange(r.label)} role="tab" aria-selected={r.label === range}>
            {r.label}
          </button>
        ))}
      </div>
      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <RLineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} minTickGap={40} />
            <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} width={mode === "pct" ? 52 : 64} domain={["auto", "auto"]} />
            {mode === "pct" && <ReferenceLine y={0} stroke="var(--text-muted)" strokeOpacity={0.5} />}
            <Tooltip
              cursor={{ stroke: "var(--text-muted)", strokeDasharray: "3 3" }}
              content={({ active, payload, label }) =>
                active && payload?.length ? (
                  <div className="tooltip">
                    <div className="t">{fmtDate(String(label))}</div>
                    {[...payload]
                      .filter((p) => typeof p.value === "number")
                      .sort((a, b) => Number(b.value) - Number(a.value))
                      .map((p) => {
                        const s = series.find((x) => x.key === p.dataKey);
                        return (
                          <div className="l num" key={String(p.dataKey)}>
                            <span><i style={{ ["--c" as string]: s?.color }} />{s?.name}</span>
                            <b>{fmt(Number(p.value))}</b>
                          </div>
                        );
                      })}
                  </div>
                ) : null
              }
            />
            {series.map((s) => (
              <Line key={s.key} type="monotone" dataKey={s.key} name={s.name} stroke={s.color} strokeWidth={2}
                strokeDasharray={s.dashed ? "5 4" : undefined} dot={false} activeDot={{ r: 4, stroke: "var(--surface-1)", strokeWidth: 2 }}
                connectNulls isAnimationActive={false} />
            ))}
          </RLineChart>
        </ResponsiveContainer>
      </div>
      {series.length > 1 && (
        <div className="legend">
          {series.map((s) => (
            <span key={s.key} className={s.dashed ? "ref" : ""} style={{ ["--c" as string]: s.color }}>{s.name}</span>
          ))}
        </div>
      )}
    </div>
  );
}
