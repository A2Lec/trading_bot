import type { Run } from "@/lib/data";

const LABEL: Record<string, string> = { success: "OK", partial: "Partiel", error: "Erreur", running: "En cours" };

export function RunStatus({ run }: { run: Run | undefined }) {
  if (!run) return <p className="sub">Le bot n&apos;a pas encore tourné.</p>;
  const when = new Date(run.started_at).toLocaleString("fr-FR", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const cls = run.status === "success" ? "up" : run.status === "running" ? "" : "down";
  return (
    <p className="sub">
      Dernier run : {when} · <span className={cls}>{run.status === "success" ? "✓" : "⚠"} {LABEL[run.status] ?? run.status}</span>
    </p>
  );
}
