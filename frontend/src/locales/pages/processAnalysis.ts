export const processAnalysisTranslations = {
  ko: {
    processAnalysis: {
      title: '공정분석',
      subtitle: '실시간 Lot 추적, 설비 모니터링 및 이상탐지 시스템',
      refresh: '새로고침',
      realtimeMode: '실시간 모드',
      realtimeModeActive: '실시간 모드 활성화 - 30초마다 자동 새로고침',
      searchConditions: '조회 조건',
      
      // Date filters
      dateFilters: {
        today: '오늘',
        yesterday: '어제',
        last3Days: '최근 3일',
        lastWeek: '최근 1주',
        lastMonth: '최근 1개월',
        all: '전체',
        custom: '사용자 정의',
        startDate: '시작 날짜',
        endDate: '종료 날짜',
      },

      // Status cards
      statusCards: {
        activeLots: '활성 Lot',
        completedLots: '완료 Lot',
        waitingLots: '대기 Lot',
        anomalyCount: '이상 건수',
      },

      // Tabs
      tabs: {
        lotTracking: 'Lot 추적',
        equipmentMonitoring: '설비 모니터링',
        anomalyDetection: '이상탐지',
      },

      // Lot Tracking
      lotTracking: {
        title: 'Lot 추적 대시보드',
        searchAndBasicFilter: '검색 및 기본 필터',
        advancedFilter: '고급 필터',
        lotList: 'Lot 목록',
        lotIdSearch: 'Lot ID 검색',
        lotIdSearchPlaceholder: 'Lot ID 검색...',
        statusFilter: '상태 필터',
        equipmentFilter: '설비 필터',
        purityRange: '순도 범위',
        yieldRange: '수율 범위',
        status: '상태',
        equipment: '설비',
        startTime: '시작시간',
        workDate: '작업일자',
        progress: '진행률',
        purity: '순도',
        yield: '수율',
        expectedCompletion: '예상완료',
        noDataMessage: 'Lot 추적 데이터가 없습니다.',
        noFilteredDataMessage: '조건에 맞는 Lot이 없습니다.',
        
        // Status values
        statuses: {
          all: '전체',
          active: '활성',
          completed: '완료',
          waiting: '대기',
        },
      },

      // Equipment Monitoring
      equipmentMonitoring: {
        title: '설비 모니터링',
        filterAndSort: '필터 및 정렬',
        equipmentStatsSummary: '설비 통계 요약',
        equipmentStatus: '설비 현황',
        sortBy: '정렬 기준',
        sortOrder: '정렬 순서',
        utilizationRange: '가동률 범위',
        totalEquipment: '총 설비 수',
        running: '가동 중',
        averageUtilization: '평균 가동률',
        totalLots: '총 Lot 수',
        totalLotsLabel: '총 Lot',
        lastInspection: '마지막 점검',
        utilization: '가동률',
        averagePurity: '평균 순도',
        averageYield: '평균 수율',
        completionRate: '완료율',
        totalWork: '총 작업',
        noEquipmentData: '설비 현황 데이터가 없습니다.',
        noFilteredEquipmentData: '조건에 맞는 설비가 없습니다.',
        
        // Equipment statuses
        statuses: {
          all: '전체',
          running: '가동 중',
          waiting: '대기',
          maintenanceRequired: '점검 필요',
          noStatus: '상태 없음',
        },

        // Sort options
        sortOptions: {
          utilization: '가동률',
          lotCount: 'Lot 수',
          id: 'ID',
        },

        sortOrders: {
          descending: '내림차순',
          ascending: '오름차순',
        },
      },

      // Anomaly Detection
      anomalyDetection: {
        title: '이상탐지 대시보드',
        thresholdSettings: '임계값 설정',
        alertsAndAnalysis: '알림 및 분석',
        realtimeAlerts: '실시간 알림',
        temperatureThreshold: '온도 임계값',
        pressureThreshold: '압력 임계값',
        purityThreshold: '순도 임계값',
        yieldThreshold: '수율 임계값',
        alertSummary: '알림 요약',
        totalAlerts: '총 알림',
        criticalAlerts: '위험 알림',
        warningAlerts: '주의 알림',
        normalAlerts: '정상 알림',
        lot: 'Lot',
        equipment: '설비',
        status: '상태',
        content: '내용',
        time: '시간',
        noAnomalyData: '모든 시스템이 정상 작동 중입니다',
        noFilteredAnomalyData: '현재 설정된 임계값 내에서 이상이 탐지되지 않았습니다.',

        // Alert statuses
        statuses: {
          normal: '정상',
          warning: '주의',
          critical: '위험',
        },
      },

      // Common terms
      common: {
        all: '전체',
        select: '선택하세요',
        loading: '로딩 중...',
        noData: '데이터가 없습니다',
        unknown: 'Unknown',
        percentage: '%',
        celsius: '°C',
        bar: 'bar',
        count: '개',
      },
    }
  },
  en: {
    processAnalysis: {
      title: 'Process Analysis',
      subtitle: 'Real-time Lot tracking, Equipment monitoring and Anomaly detection system',
      refresh: 'Refresh',
      realtimeMode: 'Real-time Mode',
      realtimeModeActive: 'Real-time mode activated - Auto refresh every 30 seconds',
      searchConditions: 'Search Conditions',
      
      // Date filters
      dateFilters: {
        today: 'Today',
        yesterday: 'Yesterday',
        last3Days: 'Last 3 Days',
        lastWeek: 'Last Week',
        lastMonth: 'Last Month',
        all: 'All',
        custom: 'Custom',
        startDate: 'Start Date',
        endDate: 'End Date',
      },

      // Status cards
      statusCards: {
        activeLots: 'Active Lots',
        completedLots: 'Completed Lots',
        waitingLots: 'Waiting Lots',
        anomalyCount: 'Anomaly Count',
      },

      // Tabs
      tabs: {
        lotTracking: 'Lot Tracking',
        equipmentMonitoring: 'Equipment Monitoring',
        anomalyDetection: 'Anomaly Detection',
      },

      // Lot Tracking
      lotTracking: {
        title: 'Lot Tracking Dashboard',
        searchAndBasicFilter: 'Search & Basic Filter',
        advancedFilter: 'Advanced Filter',
        lotList: 'Lot List',
        lotIdSearch: 'Lot ID Search',
        lotIdSearchPlaceholder: 'Search Lot ID...',
        statusFilter: 'Status Filter',
        equipmentFilter: 'Equipment Filter',
        purityRange: 'Purity Range',
        yieldRange: 'Yield Range',
        status: 'Status',
        equipment: 'Equipment',
        startTime: 'Start Time',
        workDate: 'Work Date',
        progress: 'Progress',
        purity: 'Purity',
        yield: 'Yield',
        expectedCompletion: 'Expected Completion',
        noDataMessage: 'No lot tracking data available.',
        noFilteredDataMessage: 'No lots match the criteria.',
        
        // Status values
        statuses: {
          all: 'All',
          active: 'Active',
          completed: 'Completed',
          waiting: 'Waiting',
        },
      },

      // Equipment Monitoring
      equipmentMonitoring: {
        title: 'Equipment Monitoring',
        filterAndSort: 'Filter & Sort',
        equipmentStatsSummary: 'Equipment Statistics Summary',
        equipmentStatus: 'Equipment Status',
        sortBy: 'Sort By',
        sortOrder: 'Sort Order',
        utilizationRange: 'Utilization Range',
        totalEquipment: 'Total Equipment',
        running: 'Running',
        averageUtilization: 'Average Utilization',
        totalLots: 'Total Lots',
        totalLotsLabel: 'Total Lots',
        lastInspection: 'Last Inspection',
        utilization: 'Utilization',
        averagePurity: 'Average Purity',
        averageYield: 'Average Yield',
        completionRate: 'Completion Rate',
        totalWork: 'Total Work',
        noEquipmentData: 'No equipment status data available.',
        noFilteredEquipmentData: 'No equipment matches the criteria.',
        
        // Equipment statuses
        statuses: {
          all: 'All',
          running: 'Running',
          waiting: 'Waiting',
          maintenanceRequired: 'Maintenance Required',
          noStatus: 'No Status',
        },

        // Sort options
        sortOptions: {
          utilization: 'Utilization',
          lotCount: 'Lot Count',
          id: 'ID',
        },

        sortOrders: {
          descending: 'Descending',
          ascending: 'Ascending',
        },
      },

      // Anomaly Detection
      anomalyDetection: {
        title: 'Anomaly Detection Dashboard',
        thresholdSettings: 'Threshold Settings',
        alertsAndAnalysis: 'Alerts & Analysis',
        realtimeAlerts: 'Real-time Alerts',
        temperatureThreshold: 'Temperature Threshold',
        pressureThreshold: 'Pressure Threshold',
        purityThreshold: 'Purity Threshold',
        yieldThreshold: 'Yield Threshold',
        alertSummary: 'Alert Summary',
        totalAlerts: 'Total Alerts',
        criticalAlerts: 'Critical Alerts',
        warningAlerts: 'Warning Alerts',
        normalAlerts: 'Normal Alerts',
        lot: 'Lot',
        equipment: 'Equipment',
        status: 'Status',
        content: 'Content',
        time: 'Time',
        noAnomalyData: 'All systems are operating normally',
        noFilteredAnomalyData: 'No anomalies detected within current threshold settings.',

        // Alert statuses
        statuses: {
          normal: 'Normal',
          warning: 'Warning',
          critical: 'Critical',
        },
      },

      // Common terms
      common: {
        all: 'All',
        select: 'Select',
        loading: 'Loading...',
        noData: 'No data available',
        unknown: 'Unknown',
        percentage: '%',
        celsius: '°C',
        bar: 'bar',
        count: '',
      },
    }
  }
} as const 