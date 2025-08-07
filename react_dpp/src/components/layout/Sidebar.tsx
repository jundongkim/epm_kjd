'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  HomeIcon, 
  NewspaperIcon,
  CalendarDaysIcon, 
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { useSidebar } from './SidebarProvider';

export const Sidebar = () => {
  const { isExpanded, setIsExpanded } = useSidebar();
  const pathname = usePathname();

  const menuItems = [
    {
      name: 'Home',
      href: '/',
      icon: HomeIcon,
      label: '홈'
    },
    {
      name: 'Orders',
      href: '/orders',
      icon: NewspaperIcon,
      label: '주문 관리'
    },
    {
      name: 'Schedule',
      href: '/schedule',
      icon: CalendarDaysIcon,
      label: '공정표'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
      label: '설정'
    }
  ];

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <div 
      className={`
        fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-50 print:hidden
        ${isExpanded ? 'w-64' : 'w-16'}
      `}
    >
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          {isExpanded && (
            <div>
              <h1 className="text-xl font-bold text-white">현대제철 DPP</h1>
              <p className="text-sm text-gray-300">공정 스케줄 시스템</p>
            </div>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            {isExpanded ? (
              <ChevronLeftIcon className="w-5 h-5" />
            ) : (
              <ChevronRightIcon className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* 메뉴 리스트 */}
      <nav className="p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`
                    flex items-center p-3 rounded-lg transition-colors
                    ${isActive(item.href) 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }
                    ${!isExpanded ? 'justify-center' : ''}
                  `}
                  title={!isExpanded ? item.label : undefined}
                >
                  <Icon className="w-6 h-6 flex-shrink-0" />
                  {isExpanded && (
                    <span className="ml-3 font-medium">{item.label}</span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 푸터 */}
      {isExpanded && (
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400">
            <p>버전 1.0.0</p>
            <p>© 2025 현대제철</p>
          </div>
        </div>
      )}
    </div>
  );
}; 