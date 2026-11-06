"use client";
import { useState } from "react";
import { THEME_BG, THEME_COOKIE, THEMES, type Theme } from "@/lib/theme";

const META: Record<Theme, { label: string; d: string }> = {
  system: { label: "Auto", d: "M12 3a9 9 0 1 0 0 18V3zM12 3a9 9 0 0 1 0 18" },
  light: { label: "Clair", d: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" },
  dark: { label: "Sombre", d: "M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" },
};

function apply(theme: Theme) {
  const root = document.documentElement;
  if (theme === "system") delete root.dataset.theme;
  else root.dataset.theme = theme;
  document.cookie = `${THEME_COOKIE}=${theme}; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`;
  // Couleur de la barre d'état du navigateur mobile
  const resolved = theme === "system" ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : theme;
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => {
    const media = m.getAttribute("data-media") ?? m.getAttribute("media");
    if (media) m.setAttribute("data-media", media);
    if (theme === "system") { if (media) m.setAttribute("media", media); }
    else m.removeAttribute("media");
    m.setAttribute("content", theme === "system" && media ? (media.includes("dark") ? THEME_BG.dark : THEME_BG.light) : THEME_BG[resolved]);
  });
}

export function ThemeToggle({ initial }: { initial: Theme }) {
  const [theme, setTheme] = useState<Theme>(initial);
  const next = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => { setTheme(next); apply(next); }}
      aria-label={`Thème : ${META[theme].label}. Passer en ${META[next].label.toLowerCase()}`}
      title={`Thème : ${META[theme].label}`}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d={META[theme].d} />
      </svg>
      {META[theme].label}
    </button>
  );
}
