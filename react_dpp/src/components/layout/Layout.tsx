'use client';

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Toaster } from "@/components/ui/sonner";
import { useSidebar } from './SidebarProvider';

interface LayoutProps {
  children: ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  const { isExpanded } = useSidebar();

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <main 
        className={`flex-1 overflow-y-auto transition-all duration-300 print:ml-0 ${
          isExpanded ? 'ml-64' : 'ml-16'
        }`}
      >
        {children}
      </main>
      <Toaster />
    </div>
  );
}; 