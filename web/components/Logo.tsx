/* eslint-disable @next/next/no-img-element */
export function Logo({ size = 28 }: { size?: number }) {
  return <img src="/icons/logo.svg" alt="" width={size} height={size} style={{ borderRadius: size * 0.227, flex: "none" }} />;
}
