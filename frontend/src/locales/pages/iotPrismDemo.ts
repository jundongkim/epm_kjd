export const iotPrismDemo = {
    ko: {
    title: 'IoT Prism',
    subtitle: '시계열 데이터 분석 및 형태 비교 도구',
    upload: {
      title: '파일 업로드',
      description: 'CSV 파일을 업로드하여 시계열 데이터를 분석하세요',
      dragDrop: '파일을 여기에 끌어다 놓거나 클릭하여 선택하세요',
      supportedFormats: '지원 형식: CSV',
      maxSize: '최대 크기: 10MB',
      uploadButton: '파일 선택',
      processing: '파일 처리 중...',
      success: '파일이 성공적으로 업로드되었습니다'
    },
    configuration: {
      title: '데이터 설정',
      timestampColumn: '타임스탬프 컬럼 선택',
      timestampColumnPlaceholder: '시간 기준 컬럼을 선택하세요',
      visualizationColumns: '시각화 대상 컬럼',
      visualizationColumnsPlaceholder: '시각화할 컬럼들을 선택하세요',
      excludeColumns: '시각화 제외 컬럼',
      excludeColumnsPlaceholder: '제외할 컬럼들을 선택하세요'
    },
    chartSettings: {
      title: '차트 설정',
      chartType: '차트 유형',
      lineChart: '라인차트',
      boxPlot: '박스플롯',
      scatterPlot: '산점도',
      viewMode: '보기 설정',
      individual: '개별',
      overlay: '겹침',
      timeUnit: '기간 단위',
      hourly: '1시간 단위',
      daily: '1일 단위',
      weekly: '1주 단위',
      monthly: '1개월 단위',
      timeUnits: {
        hour: '시간별',
        day: '일별',
        week: '주별',
        month: '월별',
        hourLabel: '시간',
        dayLabel: '날짜',
        weekLabel: '주',
        monthLabel: '월',
        groupSuffix: '개 그룹'
      },
      performance: {
        pointsDisplayed: '개 포인트 표시',
        totalPoints: '전체',
        pointsSuffix: '개'
      }
    },
    shapeComparison: {
      title: '형태 비교',
      enable: '형태 비교 활성화',
      description: '차트에서 드래그하여 시간 범위를 선택하고 형태를 비교하세요',
      instructions: '차트 영역을 드래그하여 비교할 구간을 선택하세요',
      clear: '비교 데이터 지우기',
      move: '이동',
      remove: '제거',
      selectedTarget: '비교 대상',
      disabled: '비활성화',
      selectedGraph: '선택된 그래프',
      dragging: '드래그 중',
      keyboardInstructions: '📌 키보드: ← → 방향키로 이동 (Shift+방향키: 10칸씩) | 마우스 휠: 미세조정 | Ctrl+R: 리셋',
      positionAdjust: '위치 조정',
      reset: '리셋',
      relativeTime: '상대적 시간',
      comparisonVisualization: '형태 비교 시각화',
      targetColumn: '비교 대상 컬럼',
      dragInstruction: '선택된 컬럼에서 드래그하여 시간 범위를 선택하세요',
      resetTarget: '비교 대상 초기화',
      selectedTimeRanges: '선택된 시간 범위',
      removeTimeRange: '시간 범위 제거'
    },
    visualization: {
      title: '시계열 시각화',
      noData: '시각화할 데이터가 없습니다',
      loading: '차트를 생성하는 중...',
      xAxis: '시간',
      yAxis: '값'
    },
    stats: {
      totalRows: '총 데이터 행',
      totalColumns: '총 컬럼 수',
      timeRange: '시간 범위',
      selectedColumns: '선택된 컬럼'
    },
    errors: {
      fileNotSupported: '지원되지 않는 파일 형식입니다',
      fileTooLarge: '파일 크기가 너무 큽니다',
      parseError: '파일 파싱에 실패했습니다',
      noTimestampColumn: '타임스탬프 컬럼을 선택해주세요',
      noVisualizationColumns: '시각화할 컬럼을 선택해주세요',
      invalidTimestamp: '유효하지 않은 타임스탬프 형식입니다'
    },
    aiAnalysis: {
      title: 'AI 분석',
      description: '차트를 분석하려면 \'AI 분석\' 버튼을 클릭하세요. AI가 데이터 패턴, 트렌드, 이상치 등을 자동으로 분석해드립니다.'
    }
    },
    en: {
    title: 'IoT Prism',
    subtitle: 'Time Series Data Analysis and Pattern Comparison Tool',
    upload: {
      title: 'File Upload',
      description: 'Upload CSV files to analyze time series data',
      dragDrop: 'Drag and drop files here or click to select',
      supportedFormats: 'Supported formats: CSV',
      maxSize: 'Max size: 10MB',
      uploadButton: 'Select File',
      processing: 'Processing file...',
      success: 'File uploaded successfully'
    },
    configuration: {
      title: 'Data Configuration',
      timestampColumn: 'Select Timestamp Column',
      timestampColumnPlaceholder: 'Choose time reference column',
      visualizationColumns: 'Visualization Target Columns',
      visualizationColumnsPlaceholder: 'Select columns to visualize',
      excludeColumns: 'Exclude Columns',
      excludeColumnsPlaceholder: 'Select columns to exclude'
    },
    chartSettings: {
      title: 'Chart Settings',
      chartType: 'Chart Type',
      lineChart: 'Line Chart',
      boxPlot: 'Box Plot',
      scatterPlot: 'Scatter Plot',
      viewMode: 'View Mode',
      individual: 'Individual',
      overlay: 'Overlay',
      timeUnit: 'Time Unit',
      hourly: 'Hourly',
      daily: 'Daily',
      weekly: 'Weekly',
      monthly: 'Monthly',
      timeUnits: {
        hour: 'Hourly',
        day: 'Daily',
        week: 'Weekly',
        month: 'Monthly',
        hourLabel: 'Hour',
        dayLabel: 'Date',
        weekLabel: 'Week',
        monthLabel: 'Month',
        groupSuffix: 'groups'
      },
      performance: {
        pointsDisplayed: 'points displayed',
        totalPoints: 'total',
        pointsSuffix: 'points'
      }
    },
    shapeComparison: {
      title: 'Pattern Comparison',
      enable: 'Enable Pattern Comparison',
      description: 'Drag on charts to select time ranges and compare patterns',
      instructions: 'Drag on chart area to select comparison segments',
      clear: 'Clear Comparison Data',
      move: 'Move',
      remove: 'Remove',
      selectedTarget: 'Selected Target',
      disabled: 'Disabled',
      selectedGraph: 'Selected Graph',
      dragging: 'Dragging',
      keyboardInstructions: '📌 Keyboard: ← → arrow keys to move (Shift+arrow: 10 steps) | Mouse wheel: fine adjustment | Ctrl+R: reset',
      positionAdjust: 'Position Adjust',
      reset: 'Reset',
      relativeTime: 'Relative Time',
      comparisonVisualization: 'Pattern Comparison Visualization',
      targetColumn: 'Target Column',
      dragInstruction: 'Drag on selected column to select time range',
      resetTarget: 'Reset Target',
      selectedTimeRanges: 'Selected Time Ranges',
      removeTimeRange: 'Remove Time Range'
    },
    visualization: {
      title: 'Time Series Visualization',
      noData: 'No data to visualize',
      loading: 'Creating charts...',
      xAxis: 'Time',
      yAxis: 'Value'
    },
    stats: {
      totalRows: 'Total Rows',
      totalColumns: 'Total Columns',
      timeRange: 'Time Range',
      selectedColumns: 'Selected Columns'
    },
    errors: {
      fileNotSupported: 'File format not supported',
      fileTooLarge: 'File size too large',
      parseError: 'Failed to parse file',
      noTimestampColumn: 'Please select a timestamp column',
      noVisualizationColumns: 'Please select columns to visualize',
      invalidTimestamp: 'Invalid timestamp format'
    },
    aiAnalysis: {
      title: 'AI Analysis',
      description: 'Click the \'AI Analysis\' button to analyze the chart. AI will automatically analyze data patterns, trends, outliers, and more.'
    }
    }
}