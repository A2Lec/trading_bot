import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Paper Trading Bot",
    short_name: "Trading",
    description: "Suivi des stratégies de paper trading",
    start_url: "/",
    display: "standalone",
    background_color: "#111110",
    theme_color: "#111110",
    icons: [
      { src: "/icon", sizes: "512x512", type: "image/png" },
      { src: "/apple-icon", sizes: "180x180", type: "image/png" },
    ],
  };
}
