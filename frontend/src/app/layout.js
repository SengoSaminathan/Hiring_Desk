import "./globals.css";
import { QueryProvider } from "./providers";
import ClerkAuthProvider from "./components/ClerkAuthProvider";

export const metadata = {
  title: "Hiring Desk",
  description: "Autonomous Candidate Sourcing & Evaluation Assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <ClerkAuthProvider>
            {children}
          </ClerkAuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}

