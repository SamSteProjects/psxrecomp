import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

const title = "Legaia Trace — Read-only scene inspector";
const description =
  "Inspect deterministic town01 actor, transform, model-reference, and provenance metadata locally.";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "https";
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost";
  const image = new URL("/og.png", `${protocol}://${host}`).toString();
  return {
    title,
    description,
    openGraph: { title, description, type: "website", images: [{ url: image, width: 1792, height: 922 }] },
    twitter: { card: "summary_large_image", title, description, images: [image] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
