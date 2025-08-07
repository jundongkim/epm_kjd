import type { Metadata } from 'next'
import localFont from 'next/font/local'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'

const paperlogy = localFont({
  src: '../../public/fonts/Paperlogy.ttf',
  variable: '--font-paperlogy',
  weight: '100 900',
})

export const metadata: Metadata = {
  title: 'DX-AI Manufacturing Copilot',
  description: 'AI-powered manufacturing optimization platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className={paperlogy.variable}>
      <body className={`${paperlogy.className} antialiased`}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
