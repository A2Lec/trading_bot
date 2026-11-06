import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { COOKIE, tokenFor } from "@/lib/auth";

async function login(formData: FormData) {
  "use server";
  const expected = process.env.DASHBOARD_PASSWORD;
  if (!expected || formData.get("password") !== expected) redirect("/login?error=1");
  (await cookies()).set(COOKIE, await tokenFor(expected), {
    httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 60 * 60 * 24 * 180,
  });
  redirect("/");
}

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return (
    <div className="login">
      <form action={login}>
        <h1>Paper Trading</h1>
        <p className="sub">Accès au tableau de bord</p>
        <input type="password" name="password" placeholder="Mot de passe" autoFocus required autoComplete="current-password" />
        {error && <p className="down" style={{ fontSize: 13 }}>Mot de passe incorrect</p>}
        <button className="primary" type="submit">Entrer</button>
      </form>
    </div>
  );
}
