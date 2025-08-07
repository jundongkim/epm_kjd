'use client';

import { useCallback, useRef } from 'react';
import { ScheduleItem } from '@/types/schedule';
import { useSettingsStore } from '@/stores/settingsStore';

interface ScheduleBarProps {
  item: ScheduleItem;
  cellWidth: number;
  onSelect: (itemId: string, date: string, processLine: string) => void;
  isSelected: boolean;
  date: string;
}

export const ScheduleBar = ({ 
  item, 
  cellWidth, 
  onSelect,
  isSelected, 
  date
}: ScheduleBarProps) => {
  const barRef = useRef<HTMLDivElement>(null);
  const { getColorByName } = useSettingsStore();

  // 시간 관련 유틸리티 함수
  const getHourFromTime = (timeString: string) => {
    return new Date(timeString).getHours();
  };

  // 현재 아이템의 기본 정보
  const baseHour = getHourFromTime(item.startTime);

  // 공정라인에 따른 색상 가져오기
  const getProcessColor = useCallback(() => {
    if (item.processLine === 'No.1') {
      return getColorByName('no1ProcessColor');
    } else if (item.processLine === 'No.2') {
      return getColorByName('no2ProcessColor');
    }
    return '#EF4444';
  }, [item.processLine, getColorByName]);

  // 클릭 선택 핸들러
  const handleClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    onSelect(item.id, date, item.processLine || 'No.1');
    console.log('Item selected:', { id: item.id, date, processLine: item.processLine });
  }, [item.id, date, item.processLine, onSelect]);

  // 바 스타일 계산
  const relativePosition = baseHour * (cellWidth / 2);
  const width = item.durationHours * (cellWidth / 2);

  const barStyle = {
    left: `${relativePosition}px`,
    width: `${width}px`,
    height: '60px',
    zIndex: isSelected ? 1000 : 10,
    pointerEvents: 'auto' as const,
    backgroundColor: getProcessColor(),
    opacity: 1,
    transition: 'all 0.2s ease',
    // 선택된 아이템은 highlight
    boxShadow: isSelected ? '0 0 0 3px rgba(59, 130, 246, 0.6)' : 'none',
    transform: isSelected ? 'scale(1.02)' : 'scale(1)'
  };

  return (
    <div
      ref={barRef}
      className="absolute top-1"
      style={barStyle}
      onClick={handleClick}
    >
      <div
        className="text-white text-xs font-bold flex items-center justify-center border border-gray-700 rounded-sm cursor-pointer hover:shadow-md"
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: getProcessColor(),
          userSelect: 'none',
          // 선택된 아이템은 border 강조
          borderColor: isSelected ? '#3B82F6' : '#374151',
          borderWidth: isSelected ? '2px' : '1px'
        }}
      >
        <div className="text-center leading-tight pointer-events-none select-none">
          <div>{item.processNo}</div>
          <div>{item.description}</div>
        </div>
      </div>
    </div>
  );
}; 