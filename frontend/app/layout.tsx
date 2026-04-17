import type { ReactNode } from "react";

export const metadata = {
  title: "DSGVO Copilot",
  description: "AI Compliance Agent for German SMEs"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="de">
      <body style={{ fontFamily: "Inter, Arial, sans-serif", margin: 0, background: "#f8fafc", color: "#0f172a" }}>
        {children}
      </body>
    </html>
  );
}
