
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Media Cleanup Studio',
  description: 'Clean background static from audio and isolate image backgrounds effortlessly.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}