'use client'

import Sidebar from '@/components/Sidebar'

export default function AITestLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="h-screen bg-background overflow-hidden">
      <div className="flex h-full">
        {/* Sidebar */}
        <Sidebar />
        
        {/* Main Content */}
        <main className="flex-1 lg:ml-0 overflow-auto">
          <div className="lg:hidden h-16" />
          {children}
        </main>
      </div>
    </div>
  )
} 