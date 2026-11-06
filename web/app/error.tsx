"use client";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main>
      <h1>Erreur</h1>
      <div className="card stack" style={{ marginTop: 16 }}>
        <p>Le tableau de bord n&apos;a pas pu charger les données.</p>
        <p className="sub">
          Vérifie que la variable <code>DATABASE_URL</code> est définie sur Vercel (puis redéploie), et que le bot a tourné au moins une fois.
          Le détail est visible dans Vercel → projet → <b>Logs</b>.
        </p>
        {error.digest && <p className="sub">Code : {error.digest}</p>}
        <button className="primary" onClick={reset}>Réessayer</button>
      </div>
    </main>
  );
}
