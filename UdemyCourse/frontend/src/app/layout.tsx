import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocTalk",
  description: "Drop any document. Ask anything. Instant answers.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-zinc-50 text-zinc-900">
        {children}
      </body>
    </html>
  );
}
