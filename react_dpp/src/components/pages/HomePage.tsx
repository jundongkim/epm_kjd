'use client';

import Link from 'next/link';
import { 
  CalendarDaysIcon, 
  ChartBarIcon, 
  Cog6ToothIcon,
  ClockIcon,
  UserGroupIcon,
  DocumentChartBarIcon
} from '@heroicons/react/24/outline';

export const HomePage = () => {
  const quickActions = [
    {
      title: '공정표 보기',
      description: '현재 진행 중인 공정 스케줄을 확인하세요',
      href: '/schedule',
      icon: CalendarDaysIcon,
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      title: '설정 관리',
      description: '색상 및 레이블 설정을 변경하세요',
      href: '/settings',
      icon: Cog6ToothIcon,
      color: 'bg-green-500 hover:bg-green-600'
    }
  ];

  const statistics = [
    {
      title: '진행 중인 작업',
      value: '12',
      unit: '건',
      icon: ClockIcon,
      color: 'text-blue-600 bg-blue-50'
    },
    {
      title: '완료된 작업',
      value: '248',
      unit: '건',
      icon: DocumentChartBarIcon,
      color: 'text-green-600 bg-green-50'
    },
    {
      title: '생산량',
      value: '15,420',
      unit: 'T',
      icon: ChartBarIcon,
      color: 'text-purple-600 bg-purple-50'
    },
    {
      title: '활성 라인',
      value: '2',
      unit: '개',
      icon: UserGroupIcon,
      color: 'text-orange-600 bg-orange-50'
    }
  ];

  return (
    <div className="p-8">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          현대제철 DPP 공정 스케줄 시스템
        </h1>
        <p className="text-lg text-gray-600">
          효율적인 철강 생산 공정 관리를 위한 통합 스케줄링 시스템
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statistics.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stat.value}
                    <span className="text-sm font-normal text-gray-500 ml-1">{stat.unit}</span>
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 빠른 작업 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">빠른 작업</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            return (
              <Link key={index} href={action.href}>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-start">
                    <div className={`p-3 rounded-lg ${action.color} text-white`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {action.title}
                      </h3>
                      <p className="text-gray-600">
                        {action.description}
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* 시스템 정보 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">시스템 정보</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">현재 시간</h3>
            <p className="text-lg font-semibold text-gray-900">
              {new Date().toLocaleString('ko-KR')}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">시스템 상태</h3>
            <p className="text-lg font-semibold text-green-600">정상 가동</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">마지막 업데이트</h3>
            <p className="text-lg font-semibold text-gray-900">
              {new Date().toLocaleTimeString('ko-KR')}
            </p>
          </div>
        </div>
      </div>

      {/* 주요 기능 소개 */}
      <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">주요 기능</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">키보드 조작</h3>
            <p className="text-sm text-gray-600">Shift+화살표로 시간/라인 이동</p>
            <p className="text-sm text-gray-600">Shift + ← / →: 시간 이동</p>
            <p className="text-sm text-gray-600">Shift + ↑ / ↓: 공정라인 이동</p>
            <p className="text-sm text-gray-600">← / →: 지속시간 조정</p>
            <p className="text-sm text-gray-600">ESC: 선택 해제</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">실시간 저장</h3>
            <p className="text-sm text-gray-600">자동 백업 및 동기화</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">다양한 뷰</h3>
            <p className="text-sm text-gray-600">1주~4주 단위 표시</p>
          </div>
        </div>
      </div>
    </div>
  );
}; 