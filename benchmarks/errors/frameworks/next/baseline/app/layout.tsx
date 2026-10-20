import type { Metadata } from "next";
import "./globals.css";

// The starter also loads the Geist fonts through next/font/google. They are
// left out because next/font fetches them from Google when the app compiles,
// and every benchmark case starts without a cache, so every build and dev
// start would depend on Google's servers. No checking tool depends on them.

export const metadata: Metadata = {
  title: "Projects",
  description: "Error-prevention benchmark reference page",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
