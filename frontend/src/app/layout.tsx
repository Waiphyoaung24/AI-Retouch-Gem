import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retouch Gem - AI Gem Preview",
  description: "Preview loose gemstones in custom jewelry settings with AI-powered visualization",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
