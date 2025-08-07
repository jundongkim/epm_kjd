'use client'

import Sidebar from '@/components/Sidebar'

export default function AIAdvisorLayout({
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
          <div className="lg:hidden h-16" /> {/* Mobile spacing for fixed button */}
          {children}
        </main>
      </div>
    </div>
  )
} 