'use client';

import { useState, useEffect, useCallback } from 'react';
import { useScheduleStore } from '@/stores/scheduleStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { ScheduleBar } from './ScheduleBar';

export const SchedulePage = () => {
  const { 
    currentStartDate, 
    setCurrentStartDate, 
    moveToNextPeriod, 
    moveToPrevPeriod,
    viewMode,
    setViewMode
  } = useScheduleStore();

  const {
    getColorByName,
    getLabelByName
  } = useSettingsStore();

  // 편집 가능한 하단 섹션 상태 - 날짜별 데이터 구조로 변경
  const [productionData, setProductionData] = useState<{ [key: string]: any }>({});
  const [scheduleData, setScheduleData] = useState<any[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [hasScheduleChanges, setHasScheduleChanges] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 선택된 아이템 상태 추가
  const [selectedItem, setSelectedItem] = useState<{
    id: string;
    date: string;
    processLine: string;
  } | null>(null);

  // 초기 데이터 상태 저장
  const [initialScheduleData, setInitialScheduleData] = useState<any[]>([]);

  // viewMode에 따른 날짜 범위 생성
  const generateDates = () => {
    // 모든 viewMode에서 연속된 날짜 생성
    const dates = [];
    const start = new Date(currentStartDate);
    const weekMultiplier = {
      'week': 1,
      '2weeks': 2,
      '3weeks': 3,
      '4weeks': 4
    }[viewMode];
    
    const totalDays = weekMultiplier * 7;
    for (let i = 0; i < totalDays; i++) {
      const date = new Date(start);
      date.setDate(start.getDate() + i);
      dates.push(date.toISOString().split('T')[0]);
    }
    return dates;
  };

  const dates = generateDates();

  // API에서 데이터 로드
  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      // 생산 정보 데이터 로드
      const productionResponse = await fetch('/api/production-data');
      if (productionResponse.ok) {
        const productionInfo = await productionResponse.json();
        
        // 날짜별 구조로 변환
        const dateBasedData: { [key: string]: any } = {};
        dates.forEach((date) => {
          dateBasedData[date] = {
            rolling: productionInfo[date]?.rolling || '',
            uncorrected: productionInfo[date]?.uncorrected || '',
            transfer: productionInfo[date]?.transfer || '',
            billet: productionInfo[date]?.billet || ''
          };
        });
        
        setProductionData(dateBasedData);
      }

      // 스케줄 데이터 로드 (정적 데이터이므로 fetch로 로드)
      const scheduleResponse = await fetch('/api/schedule-data');
      if (scheduleResponse.ok) {
        const scheduleInfo = await scheduleResponse.json();
        setScheduleData(scheduleInfo);
        setInitialScheduleData(JSON.parse(JSON.stringify(scheduleInfo))); // 깊은 복사로 초기 데이터 저장
      }
      
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setIsSaving(false);
      setIsLoading(false);
    }
  }, [dates.join(',')]); // dates 배열을 문자열로 변환하여 의존성 관리

  // 날짜가 변경될 때마다 데이터 다시 로드
  useEffect(() => {
    loadData();
    setHasChanges(false);
    setHasScheduleChanges(false);
    setSelectedItem(null); // 선택 해제
  }, [loadData]);

  // 저장 함수
  const saveProductionData = useCallback(async () => {
    if (!hasChanges) return;
    
    setIsSaving(true);
    try {
      const response = await fetch('/api/production-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(productionData),
      });

      if (response.ok) {
        setLastSaved(new Date());
        setHasChanges(false);
        console.log('Production data saved successfully');
      } else {
        console.error('Failed to save production data');
      }
    } catch (error) {
      console.error('Error saving production data:', error);
    } finally {
      setIsSaving(false);
    }
  }, [productionData, hasChanges]);

  // 스케줄 데이터 저장 함수
  const saveScheduleData = useCallback(async () => {
    if (!hasScheduleChanges) return;
    
    setIsSaving(true);
    try {
      const response = await fetch('/api/schedule-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scheduleData),
      });

      if (response.ok) {
        setLastSaved(new Date());
        setHasScheduleChanges(false);
        console.log('Schedule data saved successfully');
      } else {
        console.error('Failed to save schedule data');
      }
    } catch (error) {
      console.error('Error saving schedule data:', error);
    } finally {
      setIsSaving(false);
    }
  }, [scheduleData, hasScheduleChanges]);

  // 통합 저장 함수
  const saveAllData = useCallback(async () => {
    if (hasChanges) {
      await saveProductionData();
    }
    if (hasScheduleChanges) {
      await saveScheduleData();
    }
  }, [hasChanges, hasScheduleChanges, saveProductionData, saveScheduleData]);

  // 데이터 변경 핸들러
  const handleDataChange = useCallback((date: string, section: string, value: string) => {
    setProductionData(prev => ({
      ...prev,
      [date]: { 
        ...prev[date], 
        [section]: value 
      }
    }));
    setHasChanges(true);
  }, []);

  // 아이템 선택 핸들러
  const handleItemSelect = useCallback((itemId: string, date: string, processLine: string) => {
    setSelectedItem({ id: itemId, date, processLine });
  }, []);

  // 선택 해제 핸들러
  const handleItemDeselect = useCallback(() => {
    setSelectedItem(null);
  }, []);

  // 키보드 이벤트 핸들러
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!selectedItem) return;

    // ESC: 선택 해제
    if (e.key === 'Escape') {
      handleItemDeselect();
      return;
    }

    const currentItem = scheduleData
      .find(dayData => dayData.date === selectedItem.date)
      ?.items.find((item: any) => item.id === selectedItem.id);

    if (!currentItem) return;

    // Shift + 좌우 화살표: startTime 조정
    if (e.shiftKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
      e.preventDefault();
      
      const direction = e.key === 'ArrowLeft' ? -1 : 1;
      
      // 현재 시간 추출 (단순한 문자열 파싱)
      const currentTimeStr = currentItem.startTime; // "2025-05-21T12:00:00"
      const dateStr = currentTimeStr.split('T')[0]; // "2025-05-21"
      const timeStr = currentTimeStr.split('T')[1].split(':')[0]; // "12"
      const currentHour = parseInt(timeStr);
      
      // 새로운 시간 계산
      const newHour = currentHour + direction;
      
      // 날짜 경계 처리 - 더 안전한 방식
      let newDateStr = dateStr;
      let finalHour = newHour;
      let dateChanged = false;
      
      if (newHour < 0) {
        // 이전 날로 이동 (0시에서 -1시간 = 전날 23시)
        const currentDate = new Date(dateStr + 'T12:00:00'); // 정오로 설정하여 시간대 문제 방지
        currentDate.setDate(currentDate.getDate() - 1);
        newDateStr = currentDate.toISOString().split('T')[0];
        finalHour = 23;
        dateChanged = true;
      } else if (newHour > 23) {
        // 다음 날로 이동 (23시에서 +1시간 = 다음날 0시)
        const currentDate = new Date(dateStr + 'T12:00:00'); // 정오로 설정하여 시간대 문제 방지
        currentDate.setDate(currentDate.getDate() + 1);
        newDateStr = currentDate.toISOString().split('T')[0];
        finalHour = 0;
        dateChanged = true;
      }
      
      // 날짜 범위 체크
      if (!dates.includes(newDateStr)) {
        console.log('Cannot move outside date range:', newDateStr);
        return;
      }
      
      // 새로운 startTime 문자열 생성
      const newStartTimeString = `${newDateStr}T${finalHour.toString().padStart(2, '0')}:00:00`;
      
      console.log('Moving startTime:', {
        from: currentTimeStr,
        to: newStartTimeString,
        dateChanged: dateChanged
      });
      
      // 아이템 업데이트 로직
      if (!dateChanged) {
        // 같은 날짜 내에서 시간만 변경 - 단순 업데이트
        setScheduleData(prev => {
          return prev.map(dayData => ({
            ...dayData,
            items: dayData.items.map((item: any) => 
              item.id === selectedItem.id 
                ? { ...item, startTime: newStartTimeString }
                : item
            )
          }));
        });
      } else {
        // 날짜가 바뀐 경우 - 아이템 이동
        setScheduleData(prev => {
          const updated = prev.map(dayData => {
            // 기존 위치에서 아이템 제거
            if (dayData.date === selectedItem.date) {
              return {
                ...dayData,
                items: dayData.items.filter((item: any) => item.id !== selectedItem.id)
              };
            }
            // 새로운 위치에 아이템 추가
            else if (dayData.date === newDateStr) {
              return {
                ...dayData,
                items: [...dayData.items, { ...currentItem, startTime: newStartTimeString }]
              };
            }
            // 변경 없는 날짜
            else {
              return dayData;
            }
          });
          
          return updated;
        });
        
        // 선택된 아이템의 날짜 정보 업데이트
        setSelectedItem(prev => prev ? { ...prev, date: newDateStr } : null);
      }
      
      setHasScheduleChanges(true);
    }

    // Shift + 상하 화살표: 공정라인 이동
    else if (e.shiftKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
      e.preventDefault();
      
      const currentProcessLine = selectedItem.processLine;
      const targetProcessLine = currentProcessLine === 'No.1' ? 'No.2' : 'No.1';
      
      console.log('Moving process line:', {
        from: currentProcessLine,
        to: targetProcessLine
      });
      
      // 아이템 데이터에서 공정라인 변경
      setScheduleData(prev => {
        return prev.map(dayData => ({
          ...dayData,
          items: dayData.items.map((item: any) => 
            item.id === selectedItem.id 
              ? { ...item, processLine: targetProcessLine }
              : item
          )
        }));
      });
      setHasScheduleChanges(true);
      
      // 선택된 아이템 정보 업데이트
      setSelectedItem(prev => prev ? { ...prev, processLine: targetProcessLine } : null);
    }

    // Shift 없이 좌우 화살표: durationHours 조정
    else if (!e.shiftKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
      e.preventDefault();
      
      const direction = e.key === 'ArrowLeft' ? -1 : 1;
      const newDurationHours = Math.max(1, currentItem.durationHours + direction); // 최소 1시간
      
      console.log('Changing duration:', {
        from: currentItem.durationHours,
        to: newDurationHours,
        direction: direction > 0 ? 'increase' : 'decrease'
      });
      
      // durationHours 업데이트
      setScheduleData(prev => {
        return prev.map(dayData => ({
          ...dayData,
          items: dayData.items.map((item: any) => 
            item.id === selectedItem.id 
              ? { ...item, durationHours: newDurationHours }
              : item
          )
        }));
      });
      setHasScheduleChanges(true);
    }
  }, [selectedItem, scheduleData, dates, handleItemDeselect]);

  // 키보드 이벤트 리스너 등록
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // HTML5 Drag and Drop 핸들러들 - 제거됨

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentStartDate(e.target.value);
  };

  const handleViewModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setViewMode(e.target.value as 'week' | '2weeks' | '3weeks' | '4weeks');
  };

  const handlePrint = () => {
    window.print();
  };

  const viewModeLabels = {
    'week': '1주',
    '2weeks': '2주', 
    '3weeks': '3주',
    '4weeks': '4주'
  };

  // 시간 슬롯 (2시간 단위)
  const timeSlots = Array.from({length: 12}, (_, i) => `${(i * 2).toString().padStart(2, '0')}:00`);

  // 요일 한글 표시
  const getDayOfWeek = (dateString: string) => {
    const days = ['일', '월', '화', '수', '목', '금', '토'];
    const date = new Date(dateString + 'T00:00:00'); // 시간대 문제 방지
    return days[date.getDay()];
  };

  // 날짜 포맷팅 헬퍼
  const formatDate = (dateString: string) => {
    const date = new Date(dateString + 'T00:00:00');
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  // 주말 여부 판별
  const isWeekend = (dateString: string) => {
    const date = new Date(dateString + 'T00:00:00'); // 시간대 문제 방지
    const day = date.getDay();
    return day === 0 || day === 6; // 일요일(0) 또는 토요일(6)
  };

  // 주말 배경색 가져오기
  const getWeekendBgColor = useCallback(() => {
    return getColorByName('weekendBackground');
  }, [getColorByName]);

  // 비가동 배경색 가져오기
  const getIdleBgColor = useCallback(() => {
    return getColorByName('idleBackground');
  }, [getColorByName]);

  // 화면 크기에 따른 cellWidth 계산 - 개선된 버전
  const [screenWidth, setScreenWidth] = useState(1400);
  const [isPrinting, setIsPrinting] = useState(false);
  
  useEffect(() => {
    // 초기 화면 크기 설정
    if (typeof window !== 'undefined') {
      setScreenWidth(window.innerWidth);
    }
    
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };
    
    // 인쇄 감지
    const handleBeforePrint = () => {
      setIsPrinting(true);
    };
    
    const handleAfterPrint = () => {
      setIsPrinting(false);
    };
    
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', handleResize);
      window.addEventListener('beforeprint', handleBeforePrint);
      window.addEventListener('afterprint', handleAfterPrint);
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('beforeprint', handleBeforePrint);
        window.removeEventListener('afterprint', handleAfterPrint);
      };
    }
  }, []);

  // 좌측 컬럼(120px) + 여백 및 패딩(100px) 제외한 사용 가능한 너비
  const availableWidth = isPrinting 
    ? 1100 // A4 가로 인쇄 시 고정 너비 (약 1100px)
    : Math.max(500, screenWidth - 250); // 화면 표시 시
  const totalTimeSlots = dates.length * 12;
  
  // viewMode에 따라 최적화된 cellWidth 계산 - 더 적극적인 스케일링
  const calculateCellWidth = () => {
    // 인쇄 시에는 간단하게 계산
    if (isPrinting) {
      return Math.floor(availableWidth / totalTimeSlots);
    }
    
    // 기본 계산: 사용 가능한 너비를 타임슬롯 수로 나누기
    const baseWidth = Math.floor(availableWidth / totalTimeSlots);
    
    // viewMode별로 더 적극적인 제한 적용 - 1주의 최대값을 줄임
    const limits = {
      'week': { min: 20, max: 38 },     // 1주 최대값을 45에서 38로 줄임
      '2weeks': { min: 12, max: 20 },
      '3weeks': { min: 10, max: 16 },
      '4weeks': { min: 8, max: 12 }
    };
    
    const { min, max } = limits[viewMode];
    
    // 기본 계산값이 최대값을 초과하면 최대값으로, 최소값보다 작으면 최소값으로
    let finalWidth = Math.max(min, Math.min(max, baseWidth));
    
    // 전체 너비가 사용 가능한 너비를 초과하는지 재확인
    const totalCalculatedWidth = finalWidth * totalTimeSlots;
    if (totalCalculatedWidth > availableWidth) {
      finalWidth = Math.floor(availableWidth / totalTimeSlots);
      finalWidth = Math.max(min, finalWidth); // 최소값 보장
    }
    
    // 추가 안전 장치: 계산된 전체 너비가 화면을 벗어나지 않도록
    const safeTableWidth = 120 + (finalWidth * totalTimeSlots);
    const maxSafeWidth = screenWidth - 100; // 양쪽에 50px씩 여유
    if (safeTableWidth > maxSafeWidth) {
      finalWidth = Math.floor((maxSafeWidth - 120) / totalTimeSlots);
      finalWidth = Math.max(min, finalWidth);
    }
    
    return finalWidth;
  };
  
  const cellWidth = calculateCellWidth();

  // 실제 테이블 너비 계산 - 여백을 고려하여 더 보수적으로
  const tableWidth = isPrinting 
    ? Math.min(1100, 120 + (cellWidth * totalTimeSlots)) // 인쇄 시 최대 1100px로 제한
    : 120 + (cellWidth * totalTimeSlots);
  const maxAllowedWidth = isPrinting ? 1100 : screenWidth - 100; // 좌우 여백 50px씩으로 늘림

  // 날짜별 스케줄 데이터 가져오기
  const getScheduleForDate = (date: string) => {
    return scheduleData.find(d => d.date === date);
  };

  // 공정라인별 아이템 필터링
  const getItemsForProcessLine = (date: string, processLine: string) => {
    const schedule = getScheduleForDate(date);
    return schedule?.items.filter((item: any) => item.processLine === processLine) || [];
  };

  // 스케줄 막대 렌더링
  const renderScheduleBars = (items: any[], date: string) => {
    return items.map((item: any) => (
      <ScheduleBar
        key={item.id}
        item={item}
        cellWidth={cellWidth}
        onSelect={handleItemSelect}
        isSelected={selectedItem?.id === item.id}
        date={date}
      />
    ));
  };

  // 헤더 배경색 가져오기
  const getHeaderBgColor = useCallback(() => {
    return getColorByName('headerBackground');
  }, [getColorByName]);

  // 세부 헤더 배경색 가져오기 (상세, 압연일정 등)
  const getDetailHeaderBgColor = useCallback(() => {
    const headerColor = getColorByName('headerBackground');
    // 헤더 색상을 조금 더 밝게 만들어서 구분
    const rgb = parseInt(headerColor.slice(1), 16);
    const r = Math.min(255, ((rgb >> 16) & 255) + 30);
    const g = Math.min(255, ((rgb >> 8) & 255) + 30);
    const b = Math.min(255, (rgb & 255) + 30);
    return `rgb(${r}, ${g}, ${b})`;
  }, [getColorByName]);

  // 초기화 함수 추가
  const handleReset = useCallback(() => {
    if (window.confirm('모든 변경사항을 초기 상태로 되돌리시겠습니까?')) {
      setScheduleData(JSON.parse(JSON.stringify(initialScheduleData)));
      setHasScheduleChanges(false);
      setSelectedItem(null);
      console.log('Data reset to initial state');
    }
  }, [initialScheduleData]);

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <div className="min-h-screen bg-white p-4 flex items-center justify-center">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-4"></div>
          <span className="text-lg">데이터 로딩 중...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-4 print:p-2">
      {/* 상단 헤더 */}
      <div className="flex items-center justify-between mb-4 print:mb-2">
        <h1 className="text-2xl font-bold print:text-lg">
          2025.05.21 ~ 2025.05.31 공정표
          </h1>
          
        <div className="flex items-center space-x-4 no-print">
          {/* 저장 상태 표시 */}
          <div className="flex items-center space-x-2">
            {isSaving && (
              <div className="flex items-center text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                <span className="text-sm">저장 중...</span>
              </div>
            )}
            {hasChanges && !isSaving && (
              <div className="text-orange-600 text-sm">
                • 변경사항 있음
              </div>
            )}
            {hasScheduleChanges && !isSaving && (
              <div className="text-orange-600 text-sm">
                • 스케줄 변경사항 있음
              </div>
            )}
            {lastSaved && !hasChanges && !hasScheduleChanges && !isSaving && (
              <div className="text-green-600 text-sm">
                ✓ 저장됨 ({lastSaved.toLocaleTimeString()})
              </div>
            )}
            </div>

          {/* 수동 저장 버튼 */}
          <button
            onClick={saveAllData}
            disabled={(!hasChanges && !hasScheduleChanges) || isSaving}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              (hasChanges || hasScheduleChanges) && !isSaving
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            저장
          </button>

          {/* 초기화 버튼 */}
          <button
            onClick={handleReset}
            disabled={!hasScheduleChanges || isSaving}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              hasScheduleChanges && !isSaving
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            초기화
          </button>

          {/* 뷰모드 선택 */}
          <select 
            value={viewMode} 
            onChange={handleViewModeChange}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="week">1주 단위</option>
            <option value="2weeks">2주 단위</option>
            <option value="3weeks">3주 단위</option>
            <option value="4weeks">4주 단위</option>
          </select>
            
            {/* 날짜 선택 */}
            <input
              type="date"
              value={currentStartDate}
              onChange={handleDateChange}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
            />
            
            {/* 네비게이션 버튼 */}
            <div className="flex space-x-2">
              <button
              onClick={moveToPrevPeriod}
              className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
              >
              ← 이전 {viewModeLabels[viewMode]}
              </button>
              <button
              onClick={moveToNextPeriod}
              className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
              >
              다음 {viewModeLabels[viewMode]} →
              </button>
            </div>
            
            {/* 인쇄 버튼 */}
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              인쇄
            </button>
          </div>
        </div>

      {/* 디버그 정보 (개발 시에만 표시) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mb-2 text-xs text-gray-500 no-print">
          화면: {screenWidth}px | 사용가능: {availableWidth}px | 셀크기: {cellWidth}px | 테이블너비: {tableWidth}px | 최대허용: {maxAllowedWidth}px | 날짜수: {dates.length} | 인쇄중: {isPrinting ? 'Yes' : 'No'}
        </div>
      )}

      {/* 전체 테이블 구조 */}
      <div className="border-2 border-gray-800 bg-white schedule-table-container" style={{ maxWidth: '100%', overflow: 'hidden' }}>
        <table className="table-fixed" style={{ width: `${Math.min(tableWidth, maxAllowedWidth)}px` }}>
          {/* 헤더 섹션 */}
          <thead>
            {/* 날짜 헤더 */}
            <tr>
              <th 
                className="w-20 border-r border-gray-400"
                style={{ backgroundColor: getHeaderBgColor() }}
              ></th>
              {dates.map((date) => (
                <th 
                  key={date} 
                  className="border-r border-gray-400 p-2"
                  style={{ 
                    width: `${cellWidth * 12}px`,
                    backgroundColor: getHeaderBgColor()
                  }}
                >
                  <div className="font-bold text-lg text-white">
                    {formatDate(date)}
                  </div>
                  <div className="text-sm text-blue-100">
                    {getDayOfWeek(date)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {/* No.1 공정라인 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-bold text-sm p-2"
                style={{ backgroundColor: getHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('no1Label')}
              </td>
              {dates.map((date) => {
                const schedule = getScheduleForDate(date);
                const items = getItemsForProcessLine(date, 'No.1');
                return (
                  <td 
                    key={date} 
                    className="border-r border-gray-400 relative p-0"
                    style={{ 
                      width: `${cellWidth * 12}px`, 
                      height: '80px',
                      backgroundColor: isWeekend(date) ? getWeekendBgColor() : 'transparent'
                    }}
                  >
                    <div className="flex h-full">
                      {timeSlots.map((time) => (
                        <div
                          key={time}
                          style={{ 
                            width: `${cellWidth}px`,
                            backgroundColor: isWeekend(date) 
                              ? getWeekendBgColor() 
                              : (schedule?.isIdle ? getIdleBgColor() : 'white')
                          }}
                          className="border-r border-gray-200"
                        >
                        </div>
                      ))}
                    </div>
                    {/* 스케줄 막대들 */}
                    {renderScheduleBars(items, date)}
                  </td>
                );
              })}
            </tr>

            {/* No.1 상세 정보 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-bold text-xs p-1"
                style={{ backgroundColor: getDetailHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('no1Label')}<br/>{getLabelByName('detailLabel')}
              </td>
              {dates.map((date) => {
                const items = getItemsForProcessLine(date, 'No.1');
                return (
                  <td 
                    key={date} 
                    className="border-r border-gray-400 bg-blue-50 p-1"
                    style={{ 
                      width: `${cellWidth * 12}px`, 
                      minHeight: '100px',
                      backgroundColor: isWeekend(date) ? getWeekendBgColor() : '#EFF6FF'
                    }}
                  >
                    {items.length > 0 && (
                      <div className="text-xs space-y-1">
                        {items.map((item: any, index: number) => (
                          <div 
                            key={item.id} 
                            className={`border rounded p-1 ${
                              selectedItem?.id === item.id 
                                ? 'bg-blue-200 border-blue-400 shadow-md' 
                                : 'bg-blue-100 border-blue-300'
                            }`}
                          >
                            <div className={`font-bold ${
                              selectedItem?.id === item.id ? 'text-blue-900' : 'text-blue-800'
                            }`}>
                              {item.processNo}
                            </div>
                            <div className={`space-y-0.5 ${
                              selectedItem?.id === item.id ? 'text-blue-800' : 'text-blue-700'
                            }`}>
                              {item.specifications && item.specifications.map((spec: any, specIndex: number) => (
                                <div key={specIndex}>{spec.period} {spec.grade} {spec.quantity}T</div>
                              ))}
                              <div className="font-semibold">계: {item.quantityTon}T</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>

            {/* No.2 공정라인 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-bold text-sm p-2"
                style={{ backgroundColor: getHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('no2Label')}
              </td>
              {dates.map((date) => {
                const schedule = getScheduleForDate(date);
                const items = getItemsForProcessLine(date, 'No.2');
                return (
                  <td 
                    key={date} 
                    className="border-r border-gray-400 relative p-0"
                    style={{ 
                      width: `${cellWidth * 12}px`, 
                      height: '80px',
                      backgroundColor: isWeekend(date) ? getWeekendBgColor() : 'transparent'
                    }}
                  >
                    <div className="flex h-full">
                      {timeSlots.map((time) => (
                        <div
                          key={time}
                          style={{ 
                            width: `${cellWidth}px`,
                            backgroundColor: isWeekend(date) 
                              ? getWeekendBgColor() 
                              : (schedule?.isIdle ? getIdleBgColor() : 'white')
                          }}
                          className="border-r border-gray-200"
                        >
                        </div>
                      ))}
                    </div>
                    {/* 스케줄 막대들 */}
                    {renderScheduleBars(items, date)}
                  </td>
                );
              })}
            </tr>

            {/* No.2 상세 정보 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-bold text-xs p-1"
                style={{ backgroundColor: getDetailHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('no2Label')}<br/>{getLabelByName('detailLabel')}
              </td>
              {dates.map((date) => {
                const items = getItemsForProcessLine(date, 'No.2');
                return (
                  <td 
                    key={date} 
                    className="border-r border-gray-400 bg-blue-50 p-1"
                    style={{ 
                      width: `${cellWidth * 12}px`, 
                      minHeight: '100px',
                      backgroundColor: isWeekend(date) ? getWeekendBgColor() : '#EFF6FF'
                    }}
                  >
                    {items.length > 0 && (
                      <div className="text-xs space-y-1">
                        {items.map((item: any, index: number) => (
                          <div 
                            key={item.id} 
                            className={`border rounded p-1 ${
                              selectedItem?.id === item.id 
                                ? 'bg-blue-200 border-blue-400 shadow-md' 
                                : 'bg-blue-100 border-blue-300'
                            }`}
                          >
                            <div className={`font-bold ${
                              selectedItem?.id === item.id ? 'text-blue-900' : 'text-blue-800'
                            }`}>
                              {item.processNo}
                            </div>
                            <div className={`space-y-0.5 ${
                              selectedItem?.id === item.id ? 'text-blue-800' : 'text-blue-700'
                            }`}>
                              {item.specifications && item.specifications.map((spec: any, specIndex: number) => (
                                <div key={specIndex}>{spec.period} {spec.grade} {spec.quantity}T</div>
                              ))}
                              <div className="font-semibold">계: {item.quantityTon}T</div>
                            </div>
                          </div>
                        ))}
      </div>
                    )}
                  </td>
                );
              })}
            </tr>

            {/* 하단 정보 섹션들 - 날짜별 개별 셀 */}
            {/* 압연일정 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-semibold text-sm p-2"
                style={{ backgroundColor: getDetailHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('rollingLabel').split('').map((char, i) => (
                  <div key={i}>{char}</div>
                ))}
              </td>
              {dates.map((date, index) => (
                <td 
                  key={date} 
                  className="border-r border-gray-400 bg-blue-50 p-2"
                  style={{ width: `${cellWidth * 12}px` }}
                >
                  <textarea
                    value={productionData[date]?.rolling || ''}
                    onChange={(e) => {
                      handleDataChange(date, 'rolling', e.target.value);
                    }}
                    className="w-full h-16 text-xs bg-transparent border border-gray-300 rounded p-1 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder={`${getLabelByName('rollingLabel')} 입력...`}
                  />
                </td>
              ))}
            </tr>

            {/* 미교정 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-semibold text-sm p-2"
                style={{ backgroundColor: getDetailHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('uncorrectedLabel')}
              </td>
              {dates.map((date, index) => (
                <td 
                  key={date} 
                  className="border-r border-gray-400 bg-blue-50 p-2"
                  style={{ width: `${cellWidth * 12}px` }}
                >
                  <textarea
                    value={productionData[date]?.uncorrected || ''}
                    onChange={(e) => {
                      handleDataChange(date, 'uncorrected', e.target.value);
                    }}
                    className="w-full h-16 text-xs bg-transparent border border-gray-300 rounded p-1 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder={`${getLabelByName('uncorrectedLabel')} 입력...`}
                  />
                </td>
              ))}
            </tr>

            {/* 당진이관재 */}
            <tr className="border-b border-gray-400">
              <td 
                className="w-20 border-r border-gray-400 text-center font-semibold text-sm p-2"
                style={{ backgroundColor: getDetailHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('transferLabel').split('').map((char, i) => (
                  <div key={i}>{char}</div>
                ))}
              </td>
              {dates.map((date, index) => (
                <td 
                  key={date} 
                  className="border-r border-gray-400 bg-blue-50 p-2"
                  style={{ width: `${cellWidth * 12}px` }}
                >
                  <textarea
                    value={productionData[date]?.transfer || ''}
                    onChange={(e) => {
                      handleDataChange(date, 'transfer', e.target.value);
                    }}
                    className="w-full h-16 text-xs bg-transparent border border-gray-300 rounded p-1 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder={`${getLabelByName('transferLabel')} 입력...`}
                  />
                </td>
              ))}
            </tr>

            {/* 빌렛 */}
            <tr>
              <td 
                className="w-20 border-r border-gray-400 text-center font-semibold text-sm p-2"
                style={{ backgroundColor: getDetailHeaderBgColor(), color: 'white' }}
              >
                {getLabelByName('billetLabel')}
              </td>
              {dates.map((date, index) => (
                <td 
                  key={date} 
                  className="border-r border-gray-400 bg-blue-50 p-2"
                  style={{ width: `${cellWidth * 12}px` }}
                >
                  <textarea
                    value={productionData[date]?.billet || ''}
                    onChange={(e) => {
                      handleDataChange(date, 'billet', e.target.value);
                    }}
                    className="w-full h-16 text-xs bg-transparent border border-gray-300 rounded p-1 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder={`${getLabelByName('billetLabel')} 입력...`}
                  />
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}; 