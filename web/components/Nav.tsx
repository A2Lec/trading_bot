"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Theme } from "@/lib/theme";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

const items = [
  { href: "/", label: "Stratégies", d: "M3 17l6-6 4 4 8-8M15 7h6v6" },
  { href: "/market", label: "Marché", d: "M4 20V10M10 20V4M16 20v-7M22 20H2" },
  { href: "/activity", label: "Activité", d: "M12 8v4l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" },
];

export function Nav({ theme }: { theme: Theme }) {
  const path = usePathname();
  if (path === "/login") return null;
  return (
    <nav className="nav">
      {/* Visible uniquement sur grand écran (barre du haut) */}
      <Link href="/" className="brand"><Logo size={26} />Paper Trading</Link>
      {items.map((it) => {
        const active = it.href === "/" ? path === "/" || path.startsWith("/s/") : path.startsWith(it.href);
        return (
          <Link key={it.href} href={it.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={it.d} /></svg>
            {it.label}
          </Link>
        );
      })}
      <ThemeToggle initial={theme} />
    </nav>
  );
}
