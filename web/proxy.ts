import { NextResponse, type NextRequest } from "next/server";
import { COOKIE, tokenFor } from "@/lib/auth";

export async function proxy(req: NextRequest) {
  const password = process.env.DASHBOARD_PASSWORD;
  if (!password) return NextResponse.next();
  const cookie = req.cookies.get(COOKIE)?.value;
  if (cookie && cookie === (await tokenFor(password))) return NextResponse.next();
  const url = req.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!login|_next|manifest.webmanifest|icons/|icon|apple-icon|favicon.ico).*)"],
};
