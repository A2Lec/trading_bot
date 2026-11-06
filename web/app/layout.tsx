import type { Metadata, Viewport } from "next";
import { cookies } from "next/headers";
import { Nav } from "@/components/Nav";
import { THEME_BG, THEME_COOKIE, parseTheme } from "@/lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  title: "Paper Trading",
  description: "Suivi des stratégies de paper trading",
  appleWebApp: { capable: true, title: "Trading", statusBarStyle: "black-translucent" },
};

// Couleur de la barre d'état : suit le thème choisi (cookie), sinon celui du téléphone
export async function generateViewport(): Promise<Viewport> {
  const theme = parseTheme((await cookies()).get(THEME_COOKIE)?.value);
  return {
    width: "device-width",
    initialScale: 1,
    viewportFit: "cover",
    themeColor: theme === "system"
      ? [
          { media: "(prefers-color-scheme: light)", color: THEME_BG.light },
          { media: "(prefers-color-scheme: dark)", color: THEME_BG.dark },
        ]
      : THEME_BG[theme],
  };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const theme = parseTheme((await cookies()).get(THEME_COOKIE)?.value);
  return (
    <html lang="fr" data-theme={theme === "system" ? undefined : theme}>
      <body>
        <Nav theme={theme} />
        {children}
      </body>
    </html>
  );
}
