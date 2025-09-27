import React from "react";
export const metadata = {
  title: "NovaNews",
  description: "Topic-based AI news scraping with Nova Act",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="mask-icon" href="/favicon.svg" color="#7A4CFF" />
      </head>
      <body style={{ margin: 0, background: "#0B0F1A", color: "#E6EAF2", fontFamily: "Inter, system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}


