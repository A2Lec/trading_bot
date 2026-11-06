export const THEME_COOKIE = "tb_theme";
export type Theme = "system" | "light" | "dark";
export const THEMES: Theme[] = ["system", "light", "dark"];
export const parseTheme = (v: string | undefined): Theme => (v === "light" || v === "dark" ? v : "system");
export const THEME_BG = { light: "#f4f4f2", dark: "#111110" } as const;
