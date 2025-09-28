import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../src/index.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'rentAI - AI-Powered Apartment Hunting',
  description: 'Find your perfect rental with AI assistance',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}