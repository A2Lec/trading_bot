export function IconArt({ size }: { size: number }) {
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", background: "#111110", alignItems: "center", justifyContent: "center" }}>
      <svg width={size * 0.7} height={size * 0.7} viewBox="0 0 100 100">
        <polyline points="8,78 30,56 46,66 70,32 92,18" fill="none" stroke="#3987e5" strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="92" cy="18" r="7" fill="#3fbf74" />
      </svg>
    </div>
  );
}
