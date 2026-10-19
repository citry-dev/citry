import "./globals.css";

export const metadata = {title: "Project board benchmark"};

export default function RootLayout({children}) {
  return <html lang="en"><head><link rel="stylesheet" href="/assets/board.css"/></head><body><div id="root">{children}</div></body></html>;
}
