export const dataAnalysisWorkflowTranslations = {
  ko: {
    dataAnalysisWorkflow: {
      title: '데이터 분석 워크플로우',
      subtitle: '5단계 데이터 분석 프로세스를 통한 체계적인 데이터 인사이트 도출',
      
      // 상태 카드
      statusCards: {
        totalSteps: '전체 단계',
        completedSteps: '완료된 단계',
        progress: '진행률',
        selectedData: '선택된 데이터'
      },
      
      // 워크플로우 단계
      workflow: {
        title: '분석 워크플로우 단계',
        reset: '초기화',
        previousStep: '이전 단계',
        runStep: '단계 실행',
        running: '실행 중...'
      },
      
      // 5단계 분석 프로세스
      steps: {
        objectives: {
          name: '분석 목표 및 가설 정의',
          description: '분석 목표와 가설을 정의합니다',
          title: '분석 목표 및 가설 정의',
          subtitle: '데이터 분석의 목적과 검증하고자 하는 가설을 명확히 정의합니다.'
        },
        dataAcquisition: {
          name: '데이터 수집 및 수집',
          description: '분석할 데이터를 선택하고 수집합니다',
          title: '데이터 수집 및 선택',
          subtitle: '분석에 사용할 데이터를 선택합니다. 관련 IoT 데이터와 관련 데이터를 포함합니다.'
        },
        dataCleaning: {
          name: '데이터 정제 및 피처 엔지니어링',
          description: '데이터 정제 및 피처 엔지니어링을 수행합니다',
          title: '데이터 정제 및 피처 엔지니어링',
          subtitle: '전처리 엔진을 사용하여 데이터 정제, 피처 생성, 메타데이터 태깅을 수행합니다.'
        },
        eda: {
          name: '탐색적 데이터 분석 (EDA)',
          description: '탐색적 데이터 분석을 실행합니다',
          title: '탐색적 데이터 분석 (EDA)',
          subtitle: 'EDA 엔진을 통해 자동화된 리포트 생성 및 시각화를 수행합니다.'
        },
        hypothesis: {
          name: '가설 검정 및 알림',
          description: '가설 검정 및 알림 시스템을 구성합니다',
          title: '가설 검정 및 알림',
          subtitle: '가설 엔진을 사용하여 통계적 검정, 알림 규칙, 알림 시스템을 구성합니다.'
        }
      },
      
      // 목표 정의 패널
      objectives: {
        analysisGoals: '분석 목표 설정',
        hypothesisDefinition: '가설 정의',
        analysisTheme: '분석 테마',
        analysisGoal: '분석 목표',
        hypothesisToTest: '검증할 가설',
        placeholder: '예: 온도와 압력이 제품 순도에 유의미한 영향을 미칠 것이다...',
        themes: {
          manufacturingQuality: '제조 품질 분석',
          equipmentPerformance: '설비 성능 분석',
          processOptimization: '공정 최적화',
          predictiveMaintenance: '예측 정비'
        },
        goals: {
          nonConformance: '부적합 (이상)',
          equipmentInspection: '설비 점검',
          qualityIssues: '품질 이상',
          costOptimization: '비용 최적화',
          yieldImprovement: '수율 향상'
        }
      },
      
      // 데이터 수집 패널
      dataAcquisition: {
        availableData: '사용 가능한 데이터',
        dataTypes: {
          production: '생산 데이터',
          sensor: '센서 데이터',
          quality: '품질 데이터',
          experimental: '실험 데이터',
          cost: '비용 데이터'
        },
        selectedData: '선택된 데이터',
        filesCount: '개 파일',
        preview: '미리보기',
        selectDataPlaceholder: '분석 목표를 선택하세요'
      },
      
      // 데이터 정제 패널
      dataCleaning: {
        engineSettings: '전처리 엔진 설정',
        enableEngine: '전처리 엔진 활성화',
        cleaningRules: '정제 규칙',
        featureEngineering: '피처 엔지니어링',
        metadataTagging: '메타데이터 태깅',
        cleaningOptions: {
          removeDuplicates: '중복 제거',
          handleMissingValues: '결측값 처리',
          outlierDetection: '이상값 탐지',
          dataValidation: '데이터 검증',
          formatStandardization: '형식 표준화'
        },
        featureOptions: {
          normalize: '정규화',
          featureSelection: '피처 선택',
          dimensionalityReduction: '차원 축소',
          interactionFeatures: '상호작용 피처',
          temporalFeatures: '시계열 피처'
        },
        placeholders: {
          cleaningRules: '정제 규칙 선택',
          featureEngineering: '피처 엔지니어링 방법 선택'
        }
      },
      
      // EDA 패널
      eda: {
        engineSettings: 'EDA 엔진 설정',
        enableEngine: 'EDA 엔진 활성화',
        autoReports: '자동 리포트 생성',
        pandasProfiling: 'Pandas Profiling',
        sweetviz: 'Sweetviz',
        customCharts: '커스텀 차트',
        chartTypes: {
          correlationMatrix: '상관관계 매트릭스',
          distributionPlots: '분포 플롯',
          boxPlots: '박스 플롯',
          scatterMatrix: '산점도 매트릭스',
          timeSeries: '시계열 플롯'
        },
        placeholders: {
          chartTypes: '차트 유형 선택'
        }
      },
      
      // 가설 검정 패널
      hypothesis: {
        engineSettings: '가설 엔진 설정',
        enableEngine: '가설 엔진 활성화',
        statisticalTests: '통계적 검정',
        alertRules: '알림 규칙',
        notificationSystem: '알림 시스템',
        testTypes: {
          tTest: 'T-검정',
          chiSquare: '카이제곱 검정',
          anova: 'ANOVA',
          mannWhitney: 'Mann-Whitney U 검정',
          kruskalWallis: 'Kruskal-Wallis 검정'
        },
        alertTypes: {
          outlierDetection: '이상값 탐지',
          trendAnalysis: '트렌드 분석',
          thresholdMonitoring: '임계값 모니터링',
          patternRecognition: '패턴 인식',
          statisticalSignificance: '통계적 유의성'
        },
        placeholders: {
          statisticalTests: '통계적 검정 방법 선택',
          alertRules: '알림 규칙 선택'
        }
      },
      
      // 엔진 상태 패널
      engineStatus: {
        title: '엔진 상태',
        engines: {
          preprocessing: 'Preprocessing Engine',
          eda: 'EDA Engine',
          hypothesis: 'Hypothesis Engine'
        },
        status: {
          active: '활성화',
          inactive: '비활성화'
        }
      },
      
      // 분석 결과 패널
      analysisResults: {
        title: '분석 결과',
        noResults: '아직 실행된 단계가 없습니다.',
        step: '단계',
        executionTime: '실행 시간',
        seconds: '초'
      },
      
      // 메시지
      messages: {
        success: {
          objectivesDefined: '분석 목표 및 가설이 성공적으로 정의되었습니다.',
          dataAcquired: '개 데이터 소스가 성공적으로 수집되었습니다.',
          dataProcessed: '데이터 정제 및 피처 엔지니어링이 성공적으로 완료되었습니다.',
          edaCompleted: 'EDA가 성공적으로 완료되었습니다. 주요 인사이트가 발견되었습니다.',
          hypothesisCompleted: '가설 검정 및 알림 시스템이 성공적으로 구성되었습니다.'
        },
        error: {
          stepFailed: '단계 실행 중 오류가 발생했습니다:',
          dataLoadFailed: '데이터 목록 로드 실패:',
          engineConfigFailed: '엔진 설정 로드 실패:'
        },
        validation: {
          selectDataFirst: '먼저 분석할 데이터를 선택해주세요.',
          defineObjectives: '분석 목표를 설정해주세요.'
        }
      }
    }
  },
  
  en: {
    dataAnalysisWorkflow: {
      title: 'Data Analysis Workflow',
      subtitle: 'Systematic data insight extraction through a 5-step data analysis process',
      
      // Status Cards
      statusCards: {
        totalSteps: 'Total Steps',
        completedSteps: 'Completed Steps',
        progress: 'Progress',
        selectedData: 'Selected Data'
      },
      
      // Workflow
      workflow: {
        title: 'Analysis Workflow Steps',
        reset: 'Reset',
        previousStep: 'Previous Step',
        runStep: 'Run Step',
        running: 'Running...'
      },
      
      // 5-Step Analysis Process
      steps: {
        objectives: {
          name: 'Define Objectives & Hypotheses',
          description: 'Define analysis goals and hypotheses',
          title: 'Define Objectives & Hypotheses',
          subtitle: 'Clearly define the purpose of data analysis and hypotheses to be tested.'
        },
        dataAcquisition: {
          name: 'Data Acquisition & Ingestion',
          description: 'Select and collect data for analysis',
          title: 'Data Acquisition & Selection',
          subtitle: 'Select data to be used for analysis. Include relevant IoT data and related datasets.'
        },
        dataCleaning: {
          name: 'Data Cleaning & Feature Engineering',
          description: 'Perform data cleaning and feature engineering',
          title: 'Data Cleaning & Feature Engineering',
          subtitle: 'Use preprocessing engine to perform data cleaning, feature generation, and metadata tagging.'
        },
        eda: {
          name: 'Exploratory Data Analysis (EDA)',
          description: 'Execute exploratory data analysis',
          title: 'Exploratory Data Analysis (EDA)',
          subtitle: 'Perform automated report generation and visualization through EDA engine.'
        },
        hypothesis: {
          name: 'Hypothesis Testing & Alerting',
          description: 'Configure hypothesis testing and alert systems',
          title: 'Hypothesis Testing & Alerting',
          subtitle: 'Use hypothesis engine to configure statistical tests, alert rules, and notification systems.'
        }
      },
      
      // Objectives Panel
      objectives: {
        analysisGoals: 'Analysis Goals Setting',
        hypothesisDefinition: 'Hypothesis Definition',
        analysisTheme: 'Analysis Theme',
        analysisGoal: 'Analysis Goals',
        hypothesisToTest: 'Hypothesis to Test',
        placeholder: 'e.g., Temperature and pressure will have a significant impact on product purity...',
        themes: {
          manufacturingQuality: 'Manufacturing Quality Analysis',
          equipmentPerformance: 'Equipment Performance Analysis',
          processOptimization: 'Process Optimization',
          predictiveMaintenance: 'Predictive Maintenance'
        },
        goals: {
          nonConformance: 'Non-conformance (Anomaly)',
          equipmentInspection: 'Equipment Inspection',
          qualityIssues: 'Quality Issues',
          costOptimization: 'Cost Optimization',
          yieldImprovement: 'Yield Improvement'
        }
      },
      
      // Data Acquisition Panel
      dataAcquisition: {
        availableData: 'Available Data',
        dataTypes: {
          production: 'Production Data',
          sensor: 'Sensor Data',
          quality: 'Quality Data',
          experimental: 'Experimental Data',
          cost: 'Cost Data'
        },
        selectedData: 'Selected Data',
        filesCount: 'files',
        preview: 'Preview',
        selectDataPlaceholder: 'Select analysis goals'
      },
      
      // Data Cleaning Panel
      dataCleaning: {
        engineSettings: 'Preprocessing Engine Settings',
        enableEngine: 'Enable Preprocessing Engine',
        cleaningRules: 'Cleaning Rules',
        featureEngineering: 'Feature Engineering',
        metadataTagging: 'Metadata Tagging',
        cleaningOptions: {
          removeDuplicates: 'Remove Duplicates',
          handleMissingValues: 'Handle Missing Values',
          outlierDetection: 'Outlier Detection',
          dataValidation: 'Data Validation',
          formatStandardization: 'Format Standardization'
        },
        featureOptions: {
          normalize: 'Normalize',
          featureSelection: 'Feature Selection',
          dimensionalityReduction: 'Dimensionality Reduction',
          interactionFeatures: 'Interaction Features',
          temporalFeatures: 'Temporal Features'
        },
        placeholders: {
          cleaningRules: 'Select cleaning rules',
          featureEngineering: 'Select feature engineering methods'
        }
      },
      
      // EDA Panel
      eda: {
        engineSettings: 'EDA Engine Settings',
        enableEngine: 'Enable EDA Engine',
        autoReports: 'Auto Report Generation',
        pandasProfiling: 'Pandas Profiling',
        sweetviz: 'Sweetviz',
        customCharts: 'Custom Charts',
        chartTypes: {
          correlationMatrix: 'Correlation Matrix',
          distributionPlots: 'Distribution Plots',
          boxPlots: 'Box Plots',
          scatterMatrix: 'Scatter Matrix',
          timeSeries: 'Time Series Plots'
        },
        placeholders: {
          chartTypes: 'Select chart types'
        }
      },
      
      // Hypothesis Testing Panel
      hypothesis: {
        engineSettings: 'Hypothesis Engine Settings',
        enableEngine: 'Enable Hypothesis Engine',
        statisticalTests: 'Statistical Tests',
        alertRules: 'Alert Rules',
        notificationSystem: 'Notification System',
        testTypes: {
          tTest: 'T-test',
          chiSquare: 'Chi-square test',
          anova: 'ANOVA',
          mannWhitney: 'Mann-Whitney U test',
          kruskalWallis: 'Kruskal-Wallis test'
        },
        alertTypes: {
          outlierDetection: 'Outlier Detection',
          trendAnalysis: 'Trend Analysis',
          thresholdMonitoring: 'Threshold Monitoring',
          patternRecognition: 'Pattern Recognition',
          statisticalSignificance: 'Statistical Significance'
        },
        placeholders: {
          statisticalTests: 'Select statistical test methods',
          alertRules: 'Select alert rules'
        }
      },
      
      // Engine Status Panel
      engineStatus: {
        title: 'Engine Status',
        engines: {
          preprocessing: 'Preprocessing Engine',
          eda: 'EDA Engine',
          hypothesis: 'Hypothesis Engine'
        },
        status: {
          active: 'Active',
          inactive: 'Inactive'
        }
      },
      
      // Analysis Results Panel
      analysisResults: {
        title: 'Analysis Results',
        noResults: 'No steps have been executed yet.',
        step: 'Step',
        executionTime: 'Execution Time',
        seconds: 'sec'
      },
      
      // Messages
      messages: {
        success: {
          objectivesDefined: 'Analysis objectives and hypotheses have been successfully defined.',
          dataAcquired: 'data sources have been successfully acquired.',
          dataProcessed: 'Data cleaning and feature engineering have been successfully completed.',
          edaCompleted: 'EDA has been successfully completed. Key insights have been discovered.',
          hypothesisCompleted: 'Hypothesis testing and alert system have been successfully configured.'
        },
        error: {
          stepFailed: 'An error occurred while executing the step:',
          dataLoadFailed: 'Failed to load data list:',
          engineConfigFailed: 'Failed to load engine configuration:'
        },
        validation: {
          selectDataFirst: 'Please select data for analysis first.',
          defineObjectives: 'Please set analysis objectives.'
        }
      }
    }
  }
} as const