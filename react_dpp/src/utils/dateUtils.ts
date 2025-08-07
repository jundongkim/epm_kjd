/**
 * 날짜 관련 유틸리티 함수들
 */

/**
 * 지정된 기간만큼 날짜 범위를 생성
 */
export const generateDateRange = (startDate: string, weeks: number = 1): string[] => {
  const dates: string[] = [];
  const start = new Date(startDate);
  const totalDays = weeks * 7;
  
  for (let i = 0; i < totalDays; i++) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    dates.push(date.toISOString().split('T')[0]);
  }
  
  return dates;
};

/**
 * 공정표 UI 이미지에 맞는 특정 날짜들 (7일 고정)
 */
export const generateWeeklyDateRange = (startDate: string): string[] => {
  // 2025-05-21부터 시작하는 특정 날짜들 (공정표_UI.png 참조)
  if (startDate === '2025-05-21') {
    return [
      '2025-05-21', '2025-05-22', '2025-05-23', '2025-05-24', 
      '2025-05-25', '2025-05-30', '2025-05-31'
    ];
  }
  
  // 기본적으로 연속된 7일 생성
  return generateDateRange(startDate, 1);
};

/**
 * 뷰모드에 따른 날짜 범위 생성
 */
export const generateDateRangeByViewMode = (
  startDate: string, 
  viewMode: 'week' | '2weeks' | '3weeks' | '4weeks'
): string[] => {
  const weekCount = {
    'week': 1,
    '2weeks': 2,
    '3weeks': 3,
    '4weeks': 4
  }[viewMode];
  
  return generateDateRange(startDate, weekCount);
};

/**
 * 날짜를 한국어 형식으로 포맷 (예: 5/21)
 */
export const formatDateKorean = (dateString: string): string => {
  const date = new Date(dateString);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${month}/${day}`;
};

/**
 * 일반 날짜 포맷
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

/**
 * 2시간 단위 시간 슬롯 생성 (24시간)
 */
export const getTimeSlots = (): string[] => {
  const slots: string[] = [];
  for (let hour = 0; hour < 24; hour += 2) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`);
  }
  return slots;
};

/**
 * 스케줄 막대의 너비 계산 (시간 기반)
 */
export const calculateBarWidth = (durationHours: number, cellWidth: number): number => {
  return (durationHours / 2) * cellWidth; // 2시간 = 1셀
};

/**
 * 스케줄 막대의 위치 계산
 */
export const calculateBarPosition = (startTime: string, cellWidth: number): number => {
  const date = new Date(startTime);
  const hours = date.getHours();
  const minutes = date.getMinutes();
  
  // 시간을 2시간 단위로 변환
  const timeSlotPosition = Math.floor(hours / 2);
  const minuteOffset = ((hours % 2) * 60 + minutes) / 120; // 2시간을 1로 정규화
  
  return (timeSlotPosition + minuteOffset) * cellWidth;
};

/**
 * 시간을 시간:분 형식으로 포맷
 */
export const formatTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

/**
 * 현재 주의 월요일 날짜 반환
 */
export const getCurrentWeekStart = (): string => {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // 일요일인 경우 조정
  const monday = new Date(today.setDate(diff));
  return monday.toISOString().split('T')[0];
};

/**
 * 날짜 문자열에 일수 추가
 */
export const addDays = (dateString: string, days: number): string => {
  const date = new Date(dateString);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
};

/**
 * 두 날짜 사이의 일수 계산
 */
export const getDaysBetween = (startDate: string, endDate: string): number => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffTime = Math.abs(end.getTime() - start.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

/**
 * 날짜가 주말인지 확인
 */
export const isWeekend = (dateString: string): boolean => {
  const date = new Date(dateString);
  const dayOfWeek = date.getDay();
  return dayOfWeek === 0 || dayOfWeek === 6; // 일요일(0) 또는 토요일(6)
};

/**
 * 기간 범위의 시작/끝 날짜 계산
 */
export const getPeriodRange = (startDate: string, viewMode: string): { start: string; end: string } => {
  const weekCounts: Record<string, number> = {
    'week': 1,
    '2weeks': 2,
    '3weeks': 3,
    '4weeks': 4
  };
  
  const weekCount = weekCounts[viewMode] || 1;
  
  const start = startDate;
  const end = addDays(startDate, (weekCount * 7) - 1);
  return { start, end };
};

export const getWeekStartDate = (date: string): string => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day;
  d.setDate(diff);
  return d.toISOString().split('T')[0];
};

export const addHoursToDate = (date: string, hours: number): string => {
  const d = new Date(date);
  d.setHours(d.getHours() + hours);
  return d.toISOString();
}; 