export const translations = {
  ko: {
    // Navigation
    nav: {
      home: '홈',
      dataGeneration: '데이터 생성',
      processAnalysis: '공정 분석',
      experimentDesign: '실험 설계',
      productDataAnalysis: '데이터 분석',
      costManagement: '비용 관리',
      productModeling: '모델링',
      workflow: '워크플로우',
      aiReport: 'AI 보고서',
      aiAgent: 'AI 에이전트',
      features: '기능',
      techStack: '기술 스택',
      apiDemo: 'API 데모',
      contact: '문의',
      getStarted: '시작하기',
      login: '로그인',
    },
    // Hero Section
    hero: {
      title: 'DX-AI 제조 최적화',
      subtitle: '차세대 스마트 팩토리 솔루션',
      description: '인공지능과 데이터 분석을 통해 제조 공정을 최적화하고 생산성을 혁신적으로 향상시키는 통합 솔루션입니다.',
      systemStatus: '시스템 상태',
      healthy: '정상',
      allEnginesRunning: '모든 엔진이 정상 작동 중',
      activeProcesses: '활성 프로세스',
      optimizationRate: '최적화율',
      tryDemo: '데모 체험',
      learnMore: '자세히 보기',
      engines: {
        'data_engine': '데이터 엔진',
        'ml_engine': 'ML 엔진',
        'process_engine': '공정 엔진',
        'cost_engine': '비용 엔진',
        'report_engine': '보고서 엔진',
        'n8n_workflow': 'n8n 워크플로우',
        'dify_ai_agent': 'Dify AI 에이전트'
      },
      status: {
        online: '온라인',
        offline: '오프라인',
        checking: '확인중'
      },
      features: {
        aiAnalytics: 'AI 기반 분석',
        realtimeMonitoring: '실시간 모니터링',
        predictiveOptimization: '예측 최적화',
        advancedML: '고급 ML 모델',
        workflowAutomation: '워크플로우 자동화',
        aiAgent: 'AI 에이전트 통합'
      }
    },
    // Features
    features: {
      title: '핵심 기능',
      subtitle: '제조업의 미래를 이끄는 AI 기반 솔루션',
      dataGeneration: {
        title: '데이터 생성',
        description: '생산 데이터, 실험 데이터, 비용 이력을 포함한 포괄적인 제조 데이터를 생성합니다.',
        features: ['실시간 생산 데이터 시뮬레이션', '품질 관리 메트릭', '장비 성능 모니터링'],
        benefits: ['실시간 생산 데이터 시뮬레이션', '품질 관리 메트릭', '장비 성능 모니터링'],
        tech: ['Python', 'NumPy', 'Pandas', 'SciPy', '몬테카를로 시뮬레이션']
      },
      processAnalysis: {
        title: '공정 분석',
        description: '실시간 공정 모니터링과 이상 탐지를 통해 생산 효율성을 최적화합니다.',
        features: ['실시간 공정 모니터링', '이상 패턴 감지', '예측 유지보수'],
        benefits: ['실시간 공정 모니터링', '이상 패턴 감지', '예측 유지보수'],
        tech: ['Streamlit', '실시간 대시보드', '이상탐지', '알림 시스템']
      },
      experimentDesign: {
        title: '실험 설계',
        description: '실험 계획법(DOE)을 활용한 체계적인 실험 설계와 최적화를 제공합니다.',
        features: ['다인자 실험 설계', '통계적 분석', '최적 조건 도출'],
        benefits: ['다인자 실험 설계', '통계적 분석', '최적 조건 도출'],
        tech: ['pyDOE2', 'scikit-optimize', '베이지안 최적화', '통계 분석']
      },
      costManagement: {
        title: '비용 관리',
        description: '생산 비용 분석과 예측을 통해 효율적인 비용 관리를 지원합니다.',
        features: ['실시간 비용 분석', '예산 최적화', '비용 예측 모델'],
        benefits: ['실시간 비용 분석', '예산 최적화', '비용 예측 모델'],
        tech: ['SciPy', 'Pyomo', '베이지안 최적화', '수학적 모델링']
      },
      productModeling: {
        title: '모델링',
        description: '머신러닝 기반 제품 품질 예측과 모델링을 제공합니다.',
        features: ['품질 예측 모델', '데이터 전처리', '모델 성능 최적화'],
        benefits: ['품질 예측 모델', '데이터 전처리', '모델 성능 최적화'],
        tech: ['scikit-learn', 'XGBoost', 'CatBoost', 'PyTorch', 'AutoML']
      },
      aiReport: {
        title: 'AI 보고서',
        description: '데이터 분석 결과를 바탕으로 인사이트가 담긴 보고서를 자동 생성합니다.',
        features: ['자동 보고서 생성', '데이터 시각화', '의사결정 지원'],
        benefits: ['자동 보고서 생성', '데이터 시각화', '의사결정 지원'],
        tech: ['LangGraph', 'Streamlit', 'Plotly', '자동화 워크플로우']
      },
      aiAgent: {
        title: 'AI 에이전트',
        description: 'Dify local hosting을 통해 커스텀 AI 서비스를 정의하고 관리합니다.',
        features: ['Local Dify 인스턴스 연결', 'AI 앱 생성 및 관리', '대화형 AI 서비스'],
        benefits: ['프라이빗 AI 서비스', '커스텀 워크플로우', '데이터 보안'],
        tech: ['Dify', 'FastAPI', 'Docker', 'LLM Integration']
      },
      workflow: {
        title: '워크플로우',
        description: 'n8n을 활용한 자동화 워크플로우로 반복 작업을 효율적으로 관리합니다.',
        features: ['드래그앤드롭 워크플로우 빌더', 'API 통합', '스케줄링', '조건부 실행'],
        benefits: ['업무 자동화', '반복 작업 제거', 'API 연동', '실시간 모니터링'],
        tech: ['n8n', 'Docker', 'REST API', '웹훅', '스케줄러']
      }
    },
    // Stats
    stats: {
      title: '실시간 성과 지표',
      subtitle: '데이터 기반 의사결정을 위한 핵심 메트릭',
      processOptimization: '공정 최적화',
      qualityImprovement: '품질 개선',
      costReduction: '비용 절감',
      productionEfficiency: '생산 효율성',
    },
    // Tech Stack
    techStack: {
      title: '고급 기술 파트너십',
      subtitle: '최첨단 AI/ML 프레임워크와 엔터프라이즈급 인프라를 기반으로 구축되어 뛰어난 성능과 안정성을 제공합니다.',
      categories: {
        aiml: {
          title: '🤖 AI/ML 엔진',
          items: [
            'LLM: Ollama Gemma3:4b-it-qat',
            'RAG: LangChain + FAISS Vector Store',
            'Workflow: LangGraph Orchestration',
            'ML: scikit-learn, XGBoost, CatBoost',
            'Deep Learning: PyTorch, Neural Networks'
          ]
        },
        optimization: {
          title: '⚙️ 최적화 & 분석',
          items: [
            '최적화: SciPy, scikit-optimize',
            '수학 모델링: Pyomo, Linear Programming',
            'DoE: pyDOE2, 실험 설계',
            '통계: pandas, NumPy, SciPy',
            '시각화: Plotly, Matplotlib, Seaborn'
          ]
        },
        platform: {
          title: '🖥️ 플랫폼 & 인프라',
          items: [
            'Frontend: Next.js + TypeScript',
            'Backend: FastAPI, Python 3.11+',
            '상태관리: Zustand',
            '스타일링: Tailwind CSS',
            '모니터링: 실시간 대시보드'
          ]
        },
        algorithms: {
          title: '🧠 고급 알고리즘',
          items: [
            '베이지안 최적화: Gaussian Process',
            '진화 알고리즘: Differential Evolution',
            '로버스트 최적화: 불확실성 처리',
            '다목적 최적화: Pareto Optimality',
            '민감도 분석: 고차 미분법'
          ]
        },
        automation: {
          title: '🔄 워크플로우 자동화',
          items: [
            'n8n: 시각적 워크플로우 빌더',
            'API 통합: REST/GraphQL 연동',
            '스케줄링: Cron Jobs, 트리거 기반',
            '웹훅: 실시간 이벤트 처리',
            '조건부 실행: 동적 워크플로우'
          ]
        },
        integration: {
          title: '⚡ AI 에이전트 & 통합',
          items: [
            'Dify: Local LLM 호스팅',
            'Docker: 컨테이너 오케스트레이션',
            'FastAPI: 고성능 API 게이트웨이',
            'LLM Integration: 멀티 모델 지원',
            'Private AI: 데이터 보안 & 프라이버시'
          ]
        }
      }
    },
    // About
    about: {
      title: '솔루션 소개',
      subtitle: '제조업의 디지털 전환을 선도하는 AI 플랫폼',
      description: 'DX-AI 제조 최적화 솔루션은 인공지능과 빅데이터 분석을 통해 제조 공정의 모든 단계를 최적화합니다. 실시간 데이터 분석부터 예측 모델링까지, 스마트 팩토리 구현에 필요한 모든 기능을 제공합니다.',
      features: {
        realTimeMonitoring: '실시간 모니터링',
        realTimeMonitoringDesc: '생산 라인의 모든 데이터를 실시간으로 수집하고 분석합니다.',
        aiOptimization: 'AI 최적화',
        aiOptimizationDesc: '머신러닝 알고리즘을 통해 생산 공정을 지속적으로 최적화합니다.',
        predictiveAnalysis: '예측 분석',
        predictiveAnalysisDesc: '과거 데이터를 바탕으로 미래의 품질과 성능을 예측합니다.',
        comprehensiveReporting: '통합 보고서',
        comprehensiveReportingDesc: '다양한 지표와 분석 결과를 통합한 인사이트를 제공합니다.',
      }
    },
    // Contact
    contact: {
      title: '오늘 시작하세요',
      subtitle: '제조 운영을 혁신할 준비가 되셨나요? 전문가와의 맞춤형 상담을 위해 연락하세요.',
      requestDemo: '데모 요청',
      contactSales: '영업 문의',
      emailSupport: {
        title: '이메일 지원',
        email: 'support@dx-ai.com',
        description: '24/7 기술 지원'
      },
      systemStatus: {
        title: '시스템 상태',
        status: '🟢 모든 시스템 정상 운영',
        description: '99.9% 가동 시간 보장'
      },
      documentation: {
        title: '문서',
        description: '완전한 API 및 설정 가이드',
        subDescription: '개발자 리소스'
      }
    },
    // Footer
    footer: {
      company: '회사 정보',
      about: '회사 소개',
      careers: '채용 정보',
      contact: '연락처',
      support: '지원',
      documentation: '문서',
      apiGuide: 'API 가이드',
      tutorials: '튜토리얼',
      community: '커뮤니티',
      github: 'GitHub',
      forum: '포럼',
      blog: '블로그',
      legal: '법적 고지',
      privacy: '개인정보처리방침',
      terms: '이용약관',
      copyright: '© 2025 DX-AI Manufacturing. 모든 권리 보유.',
    },
    // API Demo
    apiDemo: {
      title: '🚀 API 실시간 데모',
      description: '실제 FastAPI 백엔드와 연동하여 AI 엔진들의 성능을 체험해보세요.',
      systemStatus: {
        title: '시스템 상태 확인',
        description: '전체 시스템의 상태와 AI 엔진들의 작동 상태를 확인합니다.',
      },
      dataGeneration: {
        title: '데이터 생성',
        description: '제조업 데이터를 AI로 생성하고 분석합니다.',
      },
      processAnalysis: {
        title: '공정 분석',
        description: '제조 공정의 성능을 분석하고 최적화 방안을 제안합니다.',
      },
      experimentDesign: {
        title: '실험 설계',
        description: 'DOE(Design of Experiments)와 베이지안 최적화를 통한 실험 설계를 생성합니다.',
      },
      costAnalysis: {
        title: '원가 분석',
        description: '제조 원가를 분석하고 최적화 방안을 제시합니다.',
      },
      execute: '실행',
      executing: '실행 중...',
      success: '실행 성공',
      failed: '실행 실패',
      connectionStatus: '백엔드 연결 상태',
    },
    // Data Generation
    dataGeneration: {
      title: '데이터 생성',
      subtitle: '파라미터 기반 생산·실험·원가 데이터 생성 및 시뮬레이션 UI 페이지입니다.',
      tabs: {
        production: '생산 데이터',
        experimental: '실험 데이터',
        cost: '원가/생산 이력 데이터',
      },
      production: {
        title: '생산 데이터 생성 설정',
        basicParams: '기본 파라미터',
        workSchedule: '작업 일자 설정',
        qualitySettings: '품질 지표 설정',
        simulationOptions: '시뮬레이션 옵션',
        generating: '생산 데이터 생성 중...',
        generate: '생산 데이터 생성',
      },
      experimental: {
        title: '실험 데이터 생성 설정',
        experimentDesign: '실험 설계 (DoE)',
        conditionSettings: '실험 조건 설정',
        scheduleSettings: '실험 일자 설정',
        metadata: '실험 메타데이터',
        scheduleTitle: '실험 수행 일정',
        generating: '실험 계획 생성 중...',
        generate: '실험 계획 생성',
      },
      cost: {
        title: '원가/생산 이력 데이터 생성',
        basicParams: '기본 파라미터',
        productionPeriod: '생산 기간',
        productQuality: '제품 및 품질 설정',
        materials: '원료 및 투입량 설정',
        operations: '운전 조건 설정',
        utilities: '유틸리티 설정',
        marketVolatility: '시장 변동성 설정',
        advancedSettings: '고급 설정',
        generating: '원가/생산 이력 데이터 생성 중...',
        generate: '원가/생산 이력 데이터 생성',
      },
      productionData: {
        title: '생산 데이터 생성',
        description: '제조 공정의 실제 생산 데이터를 AI로 생성합니다.',
        count: '생성할 데이터 수',
        temperature: '온도',
        pressure: '압력',
        flowRate: '유량',
        quality: '품질',
        yield: '수율',
        machineEfficiency: '기계 효율',
        defectRate: '불량률',
        energyConsumption: '에너지 소비',
        productionRate: '생산 속도',
        generate: '생성',
      },
      experimentalData: {
        title: '실험 데이터 생성',
        description: 'DOE 및 최적화 실험을 위한 데이터를 생성합니다.',
        experiments: '실험 수',
        factors: '인자 수',
        responses: '반응 수',
        designType: '설계 유형',
        replicates: '반복 수',
        blocks: '블록 수',
        generate: '생성',
      },
      costData: {
        title: '비용 & 이력 데이터',
        description: '제조 원가 및 이력 데이터를 생성합니다.',
        records: '기록 수',
        timeRange: '시간 범위',
        materialCost: '재료비',
        laborCost: '인건비',
        overheadCost: '간접비',
        energyCost: '에너지 비용',
        maintenanceCost: '유지보수 비용',
        generate: '생성',
      },
      info: {
        production: {
          title: '생산 데이터 정보',
          description: '실제 제조 공정에서 발생하는 다양한 생산 데이터를 AI로 생성합니다.',
          benefit1: '실제 공정과 유사한 데이터 패턴',
          benefit2: '다양한 시나리오 시뮬레이션',
          benefit3: '품질 관리 및 최적화 지원',
          benefit4: '머신러닝 모델 학습 데이터',
        },
        experimental: {
          title: '실험 데이터 정보',
          description: 'DOE(Design of Experiments)와 최적화 실험을 위한 체계적인 데이터를 생성합니다.',
          benefit1: '통계적 실험 설계',
          benefit2: '베이지안 최적화 지원',
          benefit3: '다인자 실험 분석',
          benefit4: '최적 조건 탐색',
        },
        cost: {
          title: '비용 & 이력 데이터 정보',
          description: '제조 원가 분석과 이력 추적을 위한 데이터를 생성합니다.',
          benefit1: '상세한 원가 분석',
          benefit2: '시간별 비용 추적',
          benefit3: '비용 최적화 지원',
          benefit4: '예산 계획 수립',
        },
      },
      generating: '생성 중...',
      generated: '생성됨',
      downloadData: '데이터 다운로드',
      successMessage: '성공적으로 생성되었습니다',
      failureMessage: '생성에 실패했습니다',
    },
    // Dashboard
    dashboard: {
      title: '대시보드',
      welcomeMessage: '안녕하세요, DX-AI 제조 최적화 대시보드입니다.',
      sidebar: {
        collapse: '사이드바 축소',
        expand: '사이드바 확장',
        navigation: '네비게이션',
        backToHome: '홈으로 돌아가기',
        openSettings: '설정 열기',
        closeSettings: '설정 닫기',
      },
      footer: {
        copyright: '© 2025 DX-AI Manufacturing',
        version: '버전',
        status: '상태',
      },
      experimentDesign: {
        subtitle: "DOE 방법론을 사용한 실험 설계 및 최적화",
        designTypes: {
          factorial: {
            name: "팩토리얼 설계",
            description: "완전 팩토리얼 실험 설계"
          },
          responseSurface: {
            name: "반응표면법",
            description: "Box-Behnken 또는 중심합성설계"
          },
          optimal: {
            name: "최적 설계",
            description: "D-최적 또는 I-최적 설계"
          },
          mixture: {
            name: "혼합물 설계", 
            description: "심플렉스 중심점 또는 극단점"
          }
        },
        sections: {
          configuration: "실험 구성",
          factors: "인자",
          responses: "반응변수",
          actions: "작업",
          designSummary: "설계 요약"
        },
        factors: {
          temperature: "온도 (°C)",
          pressure: "압력 (bar)",
          flowRate: "유량 (L/min)"
        },
        responses: {
          yield: "수율 (%)",
          qualityScore: "품질 점수",
          productionCost: "생산 비용"
        },
        buttons: {
          generateDesign: "설계 생성",
          analyzeResults: "결과 분석",
          exportDesign: "설계 내보내기"
        },
        summary: {
          runs: "실행 횟수",
          factors: "인자",
          responses: "반응변수",
          blocks: "블록"
        }
      },
      productModeling: {
        subtitle: "제품 품질 예측을 위한 머신러닝 모델 구축 및 배포",
        modelTypes: {
          neuralNetwork: {
            name: "신경망",
            description: "복잡한 패턴을 위한 딥러닝 모델"
          },
          randomForest: {
            name: "랜덤 포레스트",
            description: "특성 중요도를 위한 앙상블 방법"
          },
          xgboost: {
            name: "XGBoost",
            description: "고성능을 위한 그래디언트 부스팅"
          },
          svm: {
            name: "서포트 벡터 머신",
            description: "분류 및 회귀를 위한 SVM"
          }
        },
        sections: {
          configuration: "모델 구성",
          inputFeatures: "입력 특성",
          modelPerformance: "모델 성능",
          dataTraining: "데이터 및 훈련",
          datasetInfo: "데이터셋 정보",
          predictions: "예측"
        },
        features: {
          temperature: "온도",
          pressure: "압력", 
          flowRate: "유량",
          humidity: "습도",
          phLevel: "pH 수준",
          viscosity: "점도"
        },
        metrics: {
          accuracy: "정확도",
          f1Score: "F1 점수",
          precision: "정밀도"
        },
        buttons: {
          uploadData: "데이터 업로드",
          trainModel: "모델 훈련",
          validateModel: "모델 검증"
        },
        dataInfo: {
          totalSamples: "전체 샘플",
          trainingSet: "훈련 세트",
          validationSet: "검증 세트",
          features: "특성"
        },
        predictions: {
          qualityScore: "품질 점수",
          defectRate: "불량률",
          confidence: "신뢰도"
        }
      },
      costManagement: {
        subtitle: "모든 공정의 제조 비용 모니터링 및 최적화",
        periods: {
          daily: "일별",
          weekly: "주별", 
          monthly: "월별",
          yearly: "연별"
        },
        categories: {
          materialCosts: "원자재 비용",
          laborCosts: "인건비",
          energyCosts: "에너지 비용",
          overhead: "간접비"
        },
        overview: {
          totalCost: "총 비용",
          costPerUnit: "단위당 비용",
          budgetRemaining: "잔여 예산",
          savingsTarget: "절약 목표"
        },
        sections: {
          costBreakdown: "비용 분석",
          costCalculator: "비용 계산기",
          costOptimization: "비용 최적화",
          quickActions: "빠른 작업"
        },
        calculator: {
          productionVolume: "생산량",
          materialCostPerUnit: "단위당 원자재 비용",
          calculateCost: "비용 계산"
        },
        optimization: {
          materialWaste: "원자재 손실",
          energyEfficiency: "에너지 효율성",
          laborUtilization: "인력 활용률"
        },
        buttons: {
          generateReport: "보고서 생성",
          exportData: "데이터 내보내기",
          setBudgetAlert: "예산 알림 설정"
        },
        trends: {
          fromLastMonth: "지난 달 대비"
        }
      },
      aiReport: {
        subtitle: "AI 분석을 사용한 지능형 보고서 및 인사이트 생성",
        reportTypes: {
          productionSummary: "생산 요약",
          qualityAnalysis: "품질 분석",
          costOptimization: "비용 최적화",
          predictiveInsights: "예측 인사이트"
        },
        sections: {
          configuration: "보고서 구성",
          reportLibrary: "보고서 라이브러리",
          recentReports: "최근 보고서",
          aiInsights: "AI 인사이트",
          quickActions: "빠른 작업"
        },
        parameters: {
          dateRange: "날짜 범위",
          reportFormat: "보고서 형식",
          includeSections: "포함 섹션"
        },
        dateRanges: {
          last7Days: "최근 7일",
          last30Days: "최근 30일",
          last90Days: "최근 90일",
          customRange: "사용자 정의 범위"
        },
        formats: {
          pdf: "PDF",
          excel: "Excel",
          powerpoint: "PowerPoint",
          html: "HTML"
        },
        includeSections: {
          executiveSummary: "경영진 요약",
          dataAnalysis: "데이터 분석",
          trendsPatterns: "동향 및 패턴",
          recommendations: "권장사항",
          riskAssessment: "위험 평가",
          appendices: "부록"
        },
        buttons: {
          generateAiReport: "AI 보고서 생성",
          scheduleReport: "보고서 예약",
          templateLibrary: "템플릿 라이브러리",
          exportSettings: "내보내기 설정",
          view: "보기",
          download: "다운로드"
        },
        status: {
          completed: "완료",
          generating: "생성 중",
          failed: "실패"
        },
        insights: [
          "이번 달 생산 효율성이 이전 기간 대비 12% 증가했습니다.",
          "품질 불량률이 감소 추세를 보이며, 공정 제어가 향상되었음을 시사합니다.",
          "원자재 조달 프로세스에서 비용 최적화 기회가 확인되었습니다."
        ]
      }
    },
    // Settings
    settings: {
      title: '설정',
      subtitle: '애플리케이션 설정을 관리합니다',
      language: {
        title: '언어',
        subtitle: '사용할 언어를 선택하세요',
        korean: '한국어',
        english: '영어',
        currentLanguage: '현재 언어',
        changeLanguage: '언어 변경',
      },
      theme: {
        title: '테마',
        subtitle: '화면 테마를 선택하세요',
        light: '라이트 모드',
        dark: '다크 모드',
        system: '시스템 설정',
      },
      notifications: {
        title: '알림',
        subtitle: '알림 설정을 관리합니다',
        enable: '알림 사용',
        disable: '알림 끄기',
        sound: '알림 소리',
        email: '이메일 알림',
        push: '푸시 알림',
      },
      privacy: {
        title: '개인정보',
        subtitle: '개인정보 보호 설정',
        dataCollection: '데이터 수집',
        analytics: '분석 데이터',
        cookies: '쿠키 설정',
      },
      account: {
        title: '계정',
        subtitle: '계정 정보 관리',
        profile: '프로필',
        security: '보안',
        preferences: '환경설정',
      },
      advanced: {
        title: '고급 설정',
        subtitle: '고급 기능 및 개발자 옵션',
        debug: '디버그 모드',
        api: 'API 설정',
        cache: '캐시 설정',
        reset: '설정 초기화',
      },
    },
    // Process Analysis
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
    },

    // Chatbot
    chatbot: {
      title: 'AI 공정 전문가',
      titleWithTopic: 'AI 공정 전문가 (공정 분석)',
      titleGeneral: 'DX-AI Manufacturing Copilot',
      minimizedText: 'AI 공정 전문가',
      minimizedTextGeneral: 'AI Manufacturing 전문가',
      placeholder: '공정 분석에 대해 질문하세요...',
      placeholderGeneral: 'DX-AI Manufacturing Copilot에 대해 질문하세요...',
      greeting: {
        hello: '안녕하세요! 👋',
        description: '공정 분석에 대해 궁금한 것이 있으시면 언제든 질문해주세요.',
        descriptionGeneral: 'DX-AI Manufacturing Copilot에 대해 궁금한 것이 있으시면 언제든 질문해주세요.'
      },
      actions: {
        send: '전송',
        clear: '지우기',
        minimize: '최소화',
        close: '닫기',
        settings: '설정',
        reset: '대화 초기화',
        drag: '드래그하여 이동'
      },
      status: {
        generating: '응답 생성 중...',
        processing: '처리 중...',
        typing: '메시지를 입력하세요...',
        sendWithEnter: 'Enter로 전송'
      },
      resize: {
        diagonal: '대각선 크기 조정',
        horizontal: '좌우 크기 조정',
        vertical: '상하 크기 조정'
      },
      settings: {
        title: '챗봇 설정',
        model: 'LLM 모델',
        temperature: '온도',
        temperatureDesc: '응답 창의성 조절 (0.1-1.0)',
        temperatureMin: '더 일관된 답변 (0.0)',
        temperatureMax: '더 창의적인 답변 (2.0)',
        maxTokens: '최대 토큰 수',
        maxTokensDesc: '더 긴 답변을 생성하지만 속도가 느려집니다.',
        maxTurns: '최대 기억 턴 수',
        maxTurnsDesc: '챗봇이 기억할 최근 대화 턴 수입니다. 높을수록 더 긴 맥락을 기억합니다.',
        ollamaUrl: 'Ollama 기본 URL',
        streaming: '스트리밍 활성화',
        streamingDesc: '실시간으로 답변을 받아볼 수 있습니다.',
        resetDefaults: '기본값으로 재설정',
        loadError: '설정 로드 실패',
        saveError: '설정 저장 실패',
        currentSettings: '현재 설정',
        modelLabel: '모델',
        maxTokensLabel: '최대 토큰',
        maxTurnsLabel: '최대 기억 턴',
        streamingLabel: '스트리밍',
        enabled: '활성화',
        disabled: '비활성화',
        reset: '초기화',
        cancel: '취소',
        save: '저장',
        saving: '저장 중...'
      }
    },

    // Common
    common: {
      loading: '로딩 중...',
      error: '오류가 발생했습니다',
      success: '성공적으로 완료되었습니다',
      cancel: '취소',
      confirm: '확인',
      save: '저장',
      saving: '저장 중...',
      create: '생성',
      creating: '생성 중...',
      update: '업데이트',
      edit: '편집',
      delete: '삭제',
      close: '닫기',
      search: '검색',
      filter: '필터',
      sort: '정렬',
      reset: '재설정',
      apply: '적용',
      export: '내보내기',
      import: '가져오기',
      download: '다운로드',
      upload: '업로드',
      refresh: '새로 고침',
      settings: '설정',
      help: '도움말',
      back: '뒤로',
      next: '다음',
      previous: '이전',
      more: '더 보기',
      less: '간략히',
      view: '보기',
      hide: '숨기기',
      show: '보이기',
    },
    // 실험 설계
    experimentDesign: {
      subtitle: "DOE 방법론을 사용한 실험 설계 및 최적화",
      // 실험 설계 페이지 주요 섹션
      tabs: {
        experiment: "실험 설계",
        optimization: "최적화",
        report: "AI 보고서"
      },
      // 실험 설계 탭
      experimentTab: {
        title: "실험 설계 도구",
        parameterSettings: "실험 파라미터 설정",
        doeSettings: "DoE (Design of Experiments) 설정",
        targetSettings: "목표 설정",
        factorSelection: "실험 인자 선택",
        experimentTypes: {
          fullFactorial: "Full Factorial",
          fractionalFactorial: "Fractional Factorial",
          centralComposite: "Central Composite",
          boxBehnken: "Box-Behnken"
        },
        factors: {
          temperature: "온도",
          pressure: "압력",
          ph: "pH",
          reactionTime: "반응시간",
          catalystConcentration: "촉매농도",
          stirringSpeed: "교반속도"
        },
        parameters: {
          experimentType: "실험 유형",
          numberOfRuns: "실험 횟수",
          replications: "반복 횟수",
          optimizationGoal: "최적화 목표",
          targetPurity: "목표 순도 (%)",
          targetYield: "목표 수율 (%)"
        },
        goals: {
          purityMaximization: "순도 최대화",
          yieldMaximization: "수율 최대화",
          costMinimization: "비용 최소화",
          timeMinimization: "시간 최소화"
        },
        buttons: {
          generateExperimentPlan: "실험 계획 생성",
          generating: "실험 계획 생성 중...",
          showAll: "전체 보기",
          collapse: "축소하기"
        },
        experimentPlanSummary: "실험 계획 요약",
        factorSelectionTitle: "실험 인자 선택",
        targetSettingsTitle: "목표 설정",
        methodologyGuideTitle: "실험 설계 방법론",
        status: {
          planReady: "실험 계획이 준비되었습니다!",
          generateFirst: "실험 계획을 생성하면 여기에 요약이 표시됩니다.",
          totalExperiments: "총 실험 횟수",
          factorsAnalyzed: "분석 인자 수",
          designEfficiency: "설계 효율성",
          statisticalPower: "검정력"
        },
        analysis: {
          title: "실험 계획 분석",
          recommendations: "권장사항"
        },
        methodology: {
          title: "실험 설계 방법론 가이드",
          fullFactorial: {
            title: "Full Factorial (완전요인설계)",
            features: "모든 인자 조합을 다 실험\n완전한 정보 확보 가능\n상호작용 효과 정확 분석",
            applications: "인자 3-4개 이하\n정확한 상호작용 필요\n충분한 실험 자원"
          },
          fractionalFactorial: {
            title: "Fractional Factorial (부분요인설계)",
            features: "실험 횟수 대폭 감소\n효율적 스크리닝\n중요 인자 빠른 선별",
            applications: "인자 5개 이상\n초기 스크리닝 단계\n제한된 실험 자원"
          },
          centralComposite: {
            title: "Central Composite (중심합성설계)",
            features: "2차 곡선 모델링\n응답표면방법론(RSM)\n최적점 탐색 가능",
            applications: "최적화가 목표\n곡선 관계 예상\n품질/수율 최대화"
          },
          boxBehnken: {
            title: "Box-Behnken Design",
            features: "3수준 설계 (-1, 0, +1)\n경계점 없음 (안전)\n적당한 실험 횟수",
            applications: "극단조건 위험\n안전한 실험 범위\n중간 수준 최적화"
          }
        }
      },
      // 최적화 탭
      optimizationTab: {
        title: "실험 최적화",
        bayesianOptimization: "베이지안 최적화",
        settings: "최적화 설정",
        objectives: "목표 함수 설정",
        constraints: "제약 조건",
        algorithmSettings: "알고리즘 설정",
        algorithms: {
          gaussianProcess: "Gaussian Process",
          tpe: "Tree-structured Parzen Estimator",
          randomSearch: "Random Search"
        },
        acquisitionFunctions: {
          expectedImprovement: "Expected Improvement",
          upperConfidenceBound: "Upper Confidence Bound",
          probabilityOfImprovement: "Probability of Improvement"
        },
        parameters: {
          optimizer: "최적화 알고리즘",
          maxIterations: "최대 반복 횟수",
          acquisitionFunction: "획득 함수"
        },
        objectiveFunctionTitle: "목표 함수 설정",
        constraintsTitle: "제약 조건",
        algorithmSettingsTitle: "알고리즘 설정",
        maxIterationsLabel: "최대 반복 횟수",
        optimizationGuideTitle: "최적화 가이드",
        methodologyTitle: "최적화 방법론",
        buttons: {
          runOptimization: "최적화 실행",
          running: "최적화 실행 중..."
        },
        results: {
          title: "최적화 결과",
          optimalConditions: "최적 조건",
          predictedPerformance: "예측 성능",
          convergenceRate: "수렴률",
          iterationsUsed: "사용 반복",
          improvementRate: "개선률",
          ready: "최적화가 완료되었습니다!",
          afterExecution: "최적화 실행 후 결과가 표시됩니다."
        },
        warnings: {
          generateExperimentFirst: "실험 설계 탭에서 먼저 실험 계획을 생성하세요."
        },
        guide: {
          title: "베이지안 최적화 가이드",
          gaussianProcess: {
            title: "Gaussian Process",
            features: "확률적 surrogate 모델\n불확실성 정량화\n연속 함수 최적화",
            applications: "비선형 복잡한 함수\n노이즈가 있는 데이터\n적은 실험 횟수로 최적화"
          },
          tpe: {
            title: "Tree-structured Parzen Estimator",
            features: "히스토그램 기반 모델\n이산/연속 변수 모두 처리\n하이퍼파라미터 최적화",
            applications: "혼합 변수 타입\n조건부 변수 존재\n빠른 수렴 필요"
          },
          acquisitionFunctions: {
            title: "획득 함수",
            expectedImprovement: "기댓값 개선량 최대화\n탐험과 활용의 균형",
            upperConfidenceBound: "신뢰 구간 상한 최대화\n불확실성 고려",
            probabilityOfImprovement: "개선 확률 최대화\n보수적 접근"
          }
        }
      },
      // 보고서 탭
      reportTab: {
        title: "GenAI 보고서 생성",
        settings: "보고서 설정",
        types: {
          experimentSummary: "실험 계획 요약",
          optimizationResults: "최적화 결과",
          doeAnalysis: "DoE 분석",
          comprehensive: "종합 보고서"
        },
        sections: {
          executiveSummary: "실행 요약",
          experimentDesign: "실험 설계",
          optimizationResults: "최적화 결과",
          resultInterpretation: "결과 해석",
          improvementSuggestions: "개선 제안",
          nextSteps: "다음 단계"
        },
        lengths: {
          simple: "간단 (1-2페이지)",
          standard: "표준 (3-5페이지)",
          detailed: "상세 (5-10페이지)"
        },
        buttons: {
          generate: "보고서 생성",
          generating: "보고서 생성 중...",
          download: "보고서 다운로드"
        },
        reportTypeTitle: "보고서 유형",
        includeSectionsTitle: "포함할 섹션",
        reportLengthTitle: "보고서 길이",
        dataInclusionTitle: "포함될 데이터",
        generatedReportTitle: "생성된 보고서",
        reportGuideTitle: "보고서 가이드",
        characteristicsTitle: "보고서 유형별 특징",
        dataStatus: {
          title: "데이터 포함 정보",
          experimentData: "실험 데이터",
          optimizationData: "최적화 데이터",
          included: "포함됨",
          notIncluded: "포함되지 않음"
        },
        metadata: {
          reportType: "보고서 유형",
          generationTime: "생성 시간",
          wordCount: "단어 수",
          estimatedReadingTime: "예상 읽기 시간",
          estimatedPages: "예상 페이지 수"
        },
        guide: {
          title: "보고서 가이드",
          afterGeneration: "보고서 생성 후 가이드가 표시됩니다.",
          characteristics: "보고서 유형별 특징",
          experimentSummary: "실험 설계 개요 및 인자 정보",
          optimizationResults: "최적 조건 및 성능 개선 정도",
          doeAnalysis: "설계 방법론 및 통계적 특성 분석",
          comprehensive: "모든 섹션을 포함한 완전한 보고서"
        }
      },
              // 공통 메시지
        common: {
          loading: "로딩 중...",
          error: "오류가 발생했습니다",
          success: "성공",
          warning: "경고",
          info: "정보",
          range: "범위",
          min: "최소값",
          max: "최대값",
          value: "값",
          unit: "단위",
          enabled: "활성화",
          disabled: "비활성화",
          selected: "선택됨",
          unselected: "선택 안됨",
          running: "진행 중 실험",
          completed: "완료된 실험",
          successful: "성공한 실험",
          selectPlaceholder: "선택하세요",
          times: "회",
          count: "개",
          run: "Run",
          analysisResults: "분석 결과",
          experimentPlanResults: "실험 계획 결과",
          experimentResults: "실험 결과",
          status: {
            excellent: "우수",
            good: "양호",
            needsImprovement: "개선 필요",
            sufficient: "충분",
            moderate: "보통"
          },
          units: {
            celsius: "°C",
            bar: "bar",
            minutes: "분",
            molar: "M",
            rpm: "rpm",
            percent: "%"
          }
        }
    },
    // Dify Service
    difyService: {
      subtitle: "Local Dify 인스턴스를 통한 커스텀 AI 서비스 관리",
      statusCards: {
        totalServices: "등록된 서비스",
        activeServices: "활성 서비스", 
        totalApps: "총 앱 수",
        connectionStatus: "연결 상태",
        connected: "연결됨",
        disconnected: "미연결"
      },
      sections: {
        serviceManagement: "서비스 관리",
        appStore: "앱 스토어",
        activeServices: "활성 서비스",
        configuration: "환경 설정",
        quickActions: "빠른 작업"
      },
      serviceForm: {
        name: "서비스 이름",
        description: "설명",
        apiUrl: "API URL",
        apiKey: "API 키",
        placeholders: {
          name: "My Dify Service",
          description: "로컬 Dify 인스턴스 설명",
          apiUrl: "http://localhost:5001/v1",
          apiKey: "app-xxxxxxxxxx"
        }
      },
      serviceStatus: {
        active: "활성",
        inactive: "비활성",
        testing: "연결 테스트 중",
        error: "오류"
      },
      appTypes: {
        chatbot: "챗봇",
        agent: "에이전트",
        workflow: "워크플로우"
      },
      buttons: {
        addService: "서비스 추가",
        editService: "서비스 편집",
        deleteService: "서비스 삭제",
        testConnection: "연결 테스트",
        createApp: "앱 생성",
        viewApps: "앱 보기",
        activate: "활성화",
        deactivate: "비활성화"
      },
      testResults: {
        success: "연결 성공",
        failed: "연결 실패",
        latency: "응답 시간",
        appsFound: "앱 발견됨"
      },
      messages: {
        serviceCreated: "서비스가 성공적으로 생성되었습니다",
        serviceUpdated: "서비스가 성공적으로 업데이트되었습니다",
        serviceDeleted: "서비스가 삭제되었습니다",
        noServices: "등록된 Dify 서비스가 없습니다",
        noApps: "앱이 없습니다",
        connectionFailed: "서비스 연결에 실패했습니다"
      },
              errors: {
          invalidUrl: "유효하지 않은 URL입니다",
          invalidApiKey: "유효하지 않은 API 키입니다",
          connectionTimeout: "연결 시간 초과",
          serviceNotFound: "서비스를 찾을 수 없습니다"
        },
        emptyStates: {
          noServicesTitle: "등록된 서비스가 없습니다",
          noActiveServiceTitle: "활성 서비스가 없습니다", 
          selectActiveService: "앱을 보려면 활성 서비스를 선택하세요",
          noAppsTitle: "앱을 찾을 수 없습니다",
          createFirstApp: "첫 번째 앱 만들기"
        },
        appForm: {
          name: "앱 이름",
          description: "설명",
          type: "앱 유형",
          placeholders: {
            name: "앱 이름을 입력하세요",
            description: "앱 설명을 입력하세요"
          }
        }
      }
  },
  en: {
    // Navigation
    nav: {
      home: 'Home',
      dataGeneration: 'Data Gen',
      processAnalysis: 'Process Analysis',
      experimentDesign: 'Experiment Design',
      productDataAnalysis: 'Product Data Analysis',
      costManagement: 'Cost Management',
      productModeling: 'Product Modeling',
      workflow: 'Workflow',
      aiReport: 'AI Report',
      aiAgent: 'AI Agent',
      features: 'Features',
      techStack: 'Tech Stack',
      apiDemo: 'API Demo',
      contact: 'Contact',
      getStarted: 'Get Started',
      login: 'Login',
    },
    // Hero Section
    hero: {
      title: 'DX-AI Manufacturing Optimization',
      subtitle: 'Next-Generation Smart Factory Solution',
      description: 'An integrated solution that optimizes manufacturing processes through artificial intelligence and data analysis, revolutionarily improving productivity.',
      systemStatus: 'System Status',
      healthy: 'Healthy',
      allEnginesRunning: 'All engines running normally',
      activeProcesses: 'Active Processes',
      optimizationRate: 'Optimization Rate',
      tryDemo: 'Try Demo',
      learnMore: 'Learn More',
      engines: {
        'data_engine': 'Data Engine',
        'ml_engine': 'ML Engine',
        'process_engine': 'Process Engine',
        'cost_engine': 'Cost Engine',
        'report_engine': 'Report Engine',
        'n8n_workflow': 'n8n Workflow',
        'dify_ai_agent': 'Dify AI Agent'
      },
      status: {
        online: 'Online',
        offline: 'Offline',
        checking: 'Checking'
      },
      features: {
        aiAnalytics: 'AI-Powered Analytics',
        realtimeMonitoring: 'Real-time Monitoring',
        predictiveOptimization: 'Predictive Optimization',
        advancedML: 'Advanced ML Models',
        workflowAutomation: 'Workflow Automation',
        aiAgent: 'AI Agent Integration'
      }
    },
    // Features
    features: {
      title: 'Core Features',
      subtitle: 'AI-powered solutions leading the future of manufacturing',
      dataGeneration: {
        title: 'Data Generation',
        description: 'Generate comprehensive manufacturing data including production data, experimental data, and cost history.',
        features: ['Real-time production data simulation', 'Quality management metrics', 'Equipment performance monitoring'],
        benefits: ['Real-time production data simulation', 'Quality management metrics', 'Equipment performance monitoring'],
        tech: ['Python', 'NumPy', 'Pandas', 'SciPy', 'Monte Carlo']
      },
      processAnalysis: {
        title: 'Process Analysis',
        description: 'Optimize production efficiency through real-time process monitoring and anomaly detection.',
        features: ['Real-time process monitoring', 'Anomaly pattern detection', 'Predictive maintenance'],
        benefits: ['Real-time process monitoring', 'Anomaly pattern detection', 'Predictive maintenance'],
        tech: ['Streamlit', 'Real-time Dashboard', 'Anomaly Detection', 'Alert System']
      },
      experimentDesign: {
        title: 'Experiment Design',
        description: 'Provide systematic experiment design and optimization using Design of Experiments (DOE).',
        features: ['Multi-factor experiment design', 'Statistical analysis', 'Optimal condition derivation'],
        benefits: ['Multi-factor experiment design', 'Statistical analysis', 'Optimal condition derivation'],
        tech: ['pyDOE2', 'scikit-optimize', 'Bayesian Optimization', 'Statistical Analysis']
      },
      costManagement: {
        title: 'Cost Management',
        description: 'Support efficient cost management through production cost analysis and forecasting.',
        features: ['Real-time cost analysis', 'Budget optimization', 'Cost prediction models'],
        benefits: ['Real-time cost analysis', 'Budget optimization', 'Cost prediction models'],
        tech: ['SciPy', 'Pyomo', 'Bayesian Optimization', 'Mathematical Modeling']
      },
      productModeling: {
        title: 'Product Modeling',
        description: 'Provide machine learning-based product quality prediction and modeling.',
        features: ['Quality prediction models', 'Data preprocessing', 'Model performance optimization'],
        benefits: ['Quality prediction models', 'Data preprocessing', 'Model performance optimization'],
        tech: ['scikit-learn', 'XGBoost', 'CatBoost', 'PyTorch', 'AutoML']
      },
      aiReport: {
        title: 'AI Report',
        description: 'Automatically generate insightful reports based on data analysis results.',
        features: ['Automatic report generation', 'Data visualization', 'Decision support'],
        benefits: ['Automatic report generation', 'Data visualization', 'Decision support'],
        tech: ['LangGraph', 'Streamlit', 'Plotly', 'Automated Workflow']
      },
      aiAgent: {
        title: 'AI Agent',
        description: 'Define and manage custom AI services through Dify local hosting.',
        features: ['Local Dify instance connection', 'AI app creation and management', 'Interactive AI services'],
        benefits: ['Private AI services', 'Custom workflows', 'Data security'],
        tech: ['Dify', 'FastAPI', 'Docker', 'LLM Integration']
      },
      workflow: {
        title: 'Workflow',
        description: 'Efficiently manage repetitive tasks with automated workflows using n8n.',
        features: ['Drag-and-drop workflow builder', 'API integration', 'Scheduling', 'Conditional execution'],
        benefits: ['Task automation', 'Remove repetitive work', 'API integration', 'Real-time monitoring'],
        tech: ['n8n', 'Docker', 'REST API', 'Webhooks', 'Scheduler']
      }
    },
    // Stats
    stats: {
      title: 'Real-time Performance Metrics',
      subtitle: 'Key metrics for data-driven decision making',
      processOptimization: 'Process Optimization',
      qualityImprovement: 'Quality Improvement',
      costReduction: 'Cost Reduction',
      productionEfficiency: 'Production Efficiency',
    },
    // Tech Stack
    techStack: {
      title: "Advanced Technology Partnership",
      subtitle: "Built on cutting-edge AI/ML frameworks and enterprise-grade infrastructure, delivering exceptional performance and reliability",
      categories: {
        aiml: {
          title: "🤖 AI/ML Engine",
          items: [
            "LLM: Ollama Gemma3:4b-it-qat",
            "RAG: LangChain + FAISS Vector Store",
            "Workflow: LangGraph Orchestration",
            "ML: scikit-learn, XGBoost, CatBoost",
            "Deep Learning: PyTorch, Neural Networks"
          ]
        },
        optimization: {
          title: "⚙️ Optimization & Analytics",
          items: [
            "Optimization: SciPy, scikit-optimize",
            "Mathematical Modeling: Pyomo, Linear Programming",
            "DoE: pyDOE2, Experimental Design",
            "Statistics: pandas, NumPy, SciPy",
            "Visualization: Plotly, Matplotlib, Seaborn"
          ]
        },
        platform: {
          title: "🖥️ Platform & Infrastructure",
          items: [
            "Frontend: Next.js + TypeScript",
            "Backend: FastAPI, Python 3.11+",
            "State Management: Zustand",
            "Styling: Tailwind CSS",
            "Monitoring: Real-time Dashboard"
          ]
        },
        algorithms: {
          title: "🧠 Advanced Algorithms",
          items: [
            "Bayesian Optimization: Gaussian Process",
            "Evolutionary Algorithms: Differential Evolution",
            "Robust Optimization: Uncertainty Handling",
            "Multi-objective Optimization: Pareto Optimality",
            "Sensitivity Analysis: Higher-order Derivatives"
          ]
        },
        automation: {
          title: "🔄 Workflow Automation",
          items: [
            "n8n: Visual Workflow Builder",
            "API Integration: REST/GraphQL Connectivity",
            "Scheduling: Cron Jobs, Trigger-based",
            "Webhooks: Real-time Event Processing",
            "Conditional Execution: Dynamic Workflows"
          ]
        },
        integration: {
          title: "⚡ AI Agent & Integration",
          items: [
            "Dify: Local LLM Hosting",
            "Docker: Container Orchestration",
            "FastAPI: High-performance API Gateway",
            "LLM Integration: Multi-model Support",
            "Private AI: Data Security & Privacy"
          ]
        }
      }
    },
    // About
    about: {
      title: 'Solution Overview',
      subtitle: 'AI platform leading digital transformation in manufacturing',
      description: 'DX-AI Manufacturing Optimization Solution optimizes every stage of manufacturing processes through artificial intelligence and big data analysis. From real-time data analysis to predictive modeling, it provides all the features needed for smart factory implementation.',
      features: {
        realTimeMonitoring: 'Real-time Monitoring',
        realTimeMonitoringDesc: 'Collect and analyze all production line data in real-time.',
        aiOptimization: 'AI Optimization',
        aiOptimizationDesc: 'Continuously optimize production processes through machine learning algorithms.',
        predictiveAnalysis: 'Predictive Analysis',
        predictiveAnalysisDesc: 'Predict future quality and performance based on historical data.',
        comprehensiveReporting: 'Comprehensive Reporting',
        comprehensiveReportingDesc: 'Provide insights integrating various metrics and analysis results.',
      }
    },
    // Contact
    contact: {
      title: 'Get Started Today',
      subtitle: 'Ready to transform your manufacturing operations? Contact our experts for a personalized consultation.',
      requestDemo: 'Request Demo',
      contactSales: 'Contact Sales',
      emailSupport: {
        title: 'Email Support',
        email: 'support@dx-ai.com',
        description: '24/7 Technical Support'
      },
      systemStatus: {
        title: 'System Status',
        status: '🟢 All Systems Operational',
        description: '99.9% Uptime Guarantee'
      },
      documentation: {
        title: 'Documentation',
        description: 'Complete API & Setup Guide',
        subDescription: 'Developer Resources'
      }
    },
    // Footer
    footer: {
      company: 'Company',
      about: 'About Us',
      careers: 'Careers',
      contact: 'Contact',
      support: 'Support',
      documentation: 'Documentation',
      apiGuide: 'API Guide',
      tutorials: 'Tutorials',
      community: 'Community',
      github: 'GitHub',
      forum: 'Forum',
      blog: 'Blog',
      legal: 'Legal',
      privacy: 'Privacy Policy',
      terms: 'Terms of Service',
      copyright: '© 2025 DX-AI Manufacturing. All rights reserved.',
    },
    // API Demo
    apiDemo: {
      title: '🚀 Live API Demo',
      description: 'Experience the performance of AI engines by connecting to real FastAPI backend.',
      systemStatus: {
        title: 'System Status Check',
        description: 'Check the status of the entire system and AI engines.',
      },
      dataGeneration: {
        title: 'Data Generation',
        description: 'Generate and analyze manufacturing data with AI.',
      },
      processAnalysis: {
        title: 'Process Analysis',
        description: 'Analyze manufacturing process performance and suggest optimization plans.',
      },
      experimentDesign: {
        title: 'Experiment Design',
        description: 'Generate experimental designs through DOE and Bayesian optimization.',
      },
      costAnalysis: {
        title: 'Cost Analysis',
        description: 'Analyze manufacturing costs and present optimization plans.',
      },
      execute: 'Execute',
      executing: 'Executing...',
      success: 'Execution Success',
      failed: 'Execution Failed',
      connectionStatus: 'Backend Connection Status',
    },
    // Data Generation
    dataGeneration: {
      title: 'Data Generation',
      subtitle: 'Parameter-based production, experimental, and cost data generation and simulation UI page.',
      tabs: {
        production: 'Production Data',
        experimental: 'Experimental Data',
        cost: 'Cost & Production History Data',
      },
      production: {
        title: 'Production Data Generation Settings',
        basicParams: 'Basic Parameters',
        workSchedule: 'Work Schedule Settings',
        qualitySettings: 'Quality Indicator Settings',
        simulationOptions: 'Simulation Options',
        generating: 'Generating Production Data...',
        generate: 'Generate Production Data',
      },
      experimental: {
        title: 'Experimental Data Generation Settings',
        experimentDesign: 'Experiment Design (DoE)',
        conditionSettings: 'Experiment Condition Settings',
        scheduleSettings: 'Experiment Schedule Settings',
        metadata: 'Experiment Metadata',
        scheduleTitle: 'Experiment Schedule',
        generating: 'Generating Experiment Plan...',
        generate: 'Generate Experiment Plan',
      },
      cost: {
        title: 'Cost/Production History Data Generation',
        basicParams: 'Basic Parameters',
        productionPeriod: 'Production Period',
        productQuality: 'Product and Quality Settings',
        materials: 'Raw Materials and Input Settings',
        operations: 'Operating Conditions Settings',
        utilities: 'Utility Settings',
        marketVolatility: 'Market Volatility Settings',
        advancedSettings: 'Advanced Settings',
        generating: 'Generating Cost/Production History Data...',
        generate: 'Generate Cost/Production History Data',
      },
      productionData: {
        title: 'Production Data Gen',
        description: 'Generate actual production data from manufacturing processes with AI.',
        count: 'Number of Data to Generate',
        temperature: 'Temperature',
        pressure: 'Pressure',
        flowRate: 'Flow Rate',
        quality: 'Quality',
        yield: 'Yield',
        machineEfficiency: 'Machine Efficiency',
        defectRate: 'Defect Rate',
        energyConsumption: 'Energy Consumption',
        productionRate: 'Production Rate',
        generate: 'Generate',
      },
      experimentalData: {
        title: 'Experimental Data Gen',
        description: 'Generate data for DOE and optimization experiments.',
        experiments: 'Number of Experiments',
        factors: 'Number of Factors',
        responses: 'Number of Responses',
        designType: 'Design Type',
        replicates: 'Replicates',
        blocks: 'Blocks',
        generate: 'Generate',
      },
      costData: {
        title: 'Cost & History Data',
        description: 'Generate manufacturing cost and history data.',
        records: 'Number of Records',
        timeRange: 'Time Range',
        materialCost: 'Material Cost',
        laborCost: 'Labor Cost',
        overheadCost: 'Overhead Cost',
        energyCost: 'Energy Cost',
        maintenanceCost: 'Maintenance Cost',
        generate: 'Generate',
      },
      info: {
        production: {
          title: 'Production Data Information',
          description: 'Generate various production data that occurs in actual manufacturing processes with AI.',
          benefit1: 'Data patterns similar to actual processes',
          benefit2: 'Various scenario simulations',
          benefit3: 'Quality control and optimization support',
          benefit4: 'Machine learning model training data',
        },
        experimental: {
          title: 'Experimental Data Information',
          description: 'Generate systematic data for DOE and optimization experiments.',
          benefit1: 'Statistical experimental design',
          benefit2: 'Bayesian optimization support',
          benefit3: 'Multi-factor experimental analysis',
          benefit4: 'Optimal condition exploration',
        },
        cost: {
          title: 'Cost & History Data Information',
          description: 'Generate data for manufacturing cost analysis and history tracking.',
          benefit1: 'Detailed cost analysis',
          benefit2: 'Time-based cost tracking',
          benefit3: 'Cost optimization support',
          benefit4: 'Budget planning',
        },
      },
      generating: 'Generating...',
      generated: 'Generated',
      downloadData: 'Download Data',
      successMessage: 'Successfully generated',
      failureMessage: 'Failed to generate',
    },
    // Dashboard
    dashboard: {
      title: 'Dashboard',
      welcomeMessage: 'Welcome to DX-AI Manufacturing Optimization Dashboard.',
      sidebar: {
        collapse: 'Collapse Sidebar',
        expand: 'Expand Sidebar',
        navigation: 'Navigation',
        backToHome: 'Back to Home',
        openSettings: 'Open Settings',
        closeSettings: 'Close Settings',
      },
      footer: {
        copyright: '© 2025 DX-AI Manufacturing',
        version: 'Version',
        status: 'Status',
      },
      experimentDesign: {
        subtitle: "Design and optimize experiments using DOE methodologies",
        // Main sections for experiment design page
        tabs: {
          experiment: "Experiment Design",
          optimization: "Optimization",
          report: "AI Report"
        },
        // Experiment Design Tab
        experimentTab: {
          title: "Experiment Design Tools",
          parameterSettings: "Experiment Parameter Settings",
          doeSettings: "DoE (Design of Experiments) Settings",
          targetSettings: "Target Settings",
          factorSelection: "Factor Selection",
          experimentTypes: {
            fullFactorial: "Full Factorial",
            fractionalFactorial: "Fractional Factorial",
            centralComposite: "Central Composite",
            boxBehnken: "Box-Behnken"
          },
          factors: {
            temperature: "Temperature",
            pressure: "Pressure",
            ph: "pH",
            reactionTime: "Reaction Time",
            catalystConcentration: "Catalyst Concentration",
            stirringSpeed: "Stirring Speed"
          },
          parameters: {
            experimentType: "Experiment Type",
            numberOfRuns: "Number of Runs",
            replications: "Replications",
            optimizationGoal: "Optimization Goal",
            targetPurity: "Target Purity (%)",
            targetYield: "Target Yield (%)"
          },
          goals: {
            purityMaximization: "Purity Maximization",
            yieldMaximization: "Yield Maximization",
            costMinimization: "Cost Minimization",
            timeMinimization: "Time Minimization"
          },
          buttons: {
            generateExperimentPlan: "Generate Experiment Plan",
            generating: "Generating Experiment Plan...",
            showAll: "Show All",
            collapse: "Collapse"
          },
          experimentPlanSummary: "Experiment Plan Summary",
          factorSelectionTitle: "Factor Selection",
          targetSettingsTitle: "Target Settings",
          methodologyGuideTitle: "Experiment Design Methodology",
          status: {
            planReady: "Experiment plan is ready!",
            generateFirst: "Generate an experiment plan to see the summary here.",
            totalExperiments: "Total Experiments",
            factorsAnalyzed: "Factors Analyzed",
            designEfficiency: "Design Efficiency",
            statisticalPower: "Statistical Power"
          },
          analysis: {
            title: "Experiment Plan Analysis",
            recommendations: "Recommendations"
          },
          methodology: {
            title: "Experiment Design Methodology Guide",
            fullFactorial: {
              title: "Full Factorial (Complete Factorial Design)",
              features: "Tests all factor combinations\nComplete information available\nAccurate interaction effect analysis",
              applications: "3-4 factors or less\nPrecise interaction needed\nSufficient experimental resources"
            },
            fractionalFactorial: {
              title: "Fractional Factorial (Fractional Factorial Design)",
              features: "Significantly reduces experiments\nEfficient screening\nQuick identification of important factors",
              applications: "5+ factors\nInitial screening phase\nLimited experimental resources"
            },
            centralComposite: {
              title: "Central Composite (Central Composite Design)",
              features: "Quadratic curve modeling\nResponse Surface Methodology (RSM)\nOptimal point exploration",
              applications: "Optimization-focused\nCurved relationships expected\nQuality/yield maximization"
            },
            boxBehnken: {
              title: "Box-Behnken Design",
              features: "3-level design (-1, 0, +1)\nNo boundary points (safe)\nModerate number of experiments",
              applications: "Extreme conditions risky\nSafe experimental range\nMid-level optimization"
            }
          }
        },
        // Optimization Tab
        optimizationTab: {
          title: "Experiment Optimization",
          bayesianOptimization: "Bayesian Optimization",
          settings: "Optimization Settings",
          objectives: "Objective Function Settings",
          constraints: "Constraints",
          algorithmSettings: "Algorithm Settings",
          algorithms: {
            gaussianProcess: "Gaussian Process",
            tpe: "Tree-structured Parzen Estimator",
            randomSearch: "Random Search"
          },
          acquisitionFunctions: {
            expectedImprovement: "Expected Improvement",
            upperConfidenceBound: "Upper Confidence Bound",
            probabilityOfImprovement: "Probability of Improvement"
          },
          parameters: {
            optimizer: "Optimization Algorithm",
            maxIterations: "Maximum Iterations",
            acquisitionFunction: "Acquisition Function"
          },
          objectiveFunctionTitle: "Objective Function Settings",
          constraintsTitle: "Constraints",
          algorithmSettingsTitle: "Algorithm Settings",
          maxIterationsLabel: "Maximum Iterations",
          optimizationGuideTitle: "Optimization Guide",
          methodologyTitle: "Optimization Methodology",
          buttons: {
            runOptimization: "Run Optimization",
            running: "Running Optimization..."
          },
          results: {
            title: "Optimization Results",
            optimalConditions: "Optimal Conditions",
            predictedPerformance: "Predicted Performance",
            convergenceRate: "Convergence Rate",
            iterationsUsed: "Iterations Used",
            improvementRate: "Improvement Rate",
            ready: "Optimization completed successfully!",
            afterExecution: "Results will be displayed after optimization execution."
          },
          warnings: {
            generateExperimentFirst: "Please generate an experiment plan in the Experiment Design tab first."
          },
          guide: {
            title: "Bayesian Optimization Guide",
            gaussianProcess: {
              title: "Gaussian Process",
              features: "Probabilistic surrogate model\nUncertainty quantification\nContinuous function optimization",
              applications: "Non-linear complex functions\nNoisy data\nOptimization with few experiments"
            },
            tpe: {
              title: "Tree-structured Parzen Estimator",
              features: "Histogram-based model\nHandles discrete/continuous variables\nHyperparameter optimization",
              applications: "Mixed variable types\nConditional variables present\nFast convergence needed"
            },
            acquisitionFunctions: {
              title: "Acquisition Functions",
              expectedImprovement: "Maximizes expected improvement\nBalance between exploration and exploitation",
              upperConfidenceBound: "Maximizes upper confidence bound\nConsiders uncertainty",
              probabilityOfImprovement: "Maximizes improvement probability\nConservative approach"
            }
          }
        },
        // Report Tab
        reportTab: {
          title: "GenAI Report Generation",
          settings: "Report Settings",
          types: {
            experimentSummary: "Experiment Plan Summary",
            optimizationResults: "Optimization Results",
            doeAnalysis: "DoE Analysis",
            comprehensive: "Comprehensive Report"
          },
          sections: {
            executiveSummary: "Executive Summary",
            experimentDesign: "Experiment Design",
            optimizationResults: "Optimization Results",
            resultInterpretation: "Result Interpretation",
            improvementSuggestions: "Improvement Suggestions",
            nextSteps: "Next Steps"
          },
          lengths: {
            simple: "Simple (1-2 pages)",
            standard: "Standard (3-5 pages)",
            detailed: "Detailed (5-10 pages)"
          },
          buttons: {
            generate: "Generate Report",
            generating: "Generating Report...",
            download: "Download Report"
          },
          reportTypeTitle: "Report Type",
          includeSectionsTitle: "Include Sections",
          reportLengthTitle: "Report Length",
          dataInclusionTitle: "Data Inclusion",
          generatedReportTitle: "Generated Report",
          reportGuideTitle: "Report Guide",
          characteristicsTitle: "Report Type Characteristics",
          dataStatus: {
            title: "Data Inclusion Information",
            experimentData: "Experiment Data",
            optimizationData: "Optimization Data",
            included: "Included",
            notIncluded: "Not Included"
          },
          metadata: {
            reportType: "Report Type",
            generationTime: "Generation Time",
            wordCount: "Word Count",
            estimatedReadingTime: "Estimated Reading Time",
            estimatedPages: "Estimated Pages"
          },
          guide: {
            title: "Report Guide",
            afterGeneration: "Guide will be displayed after report generation.",
            characteristics: "Report Type Characteristics",
            experimentSummary: "Experiment design overview and factor information",
            optimizationResults: "Optimal conditions and performance improvement",
            doeAnalysis: "Design methodology and statistical characteristics analysis",
            comprehensive: "Complete report including all sections"
          }
        },
        // Common Messages
        common: {
          loading: "Loading...",
          error: "An error occurred",
          success: "Success",
          warning: "Warning",
          info: "Information",
          range: "Range",
          min: "Minimum",
          max: "Maximum",
          value: "Value",
          unit: "Unit",
          enabled: "Enabled",
          disabled: "Disabled",
          selected: "Selected",
          unselected: "Unselected",
          running: "Running Experiments",
          completed: "Completed Experiments",
          successful: "Successful Experiments",
          selectPlaceholder: "Select...",
          times: "times",
          count: "count",
          run: "Run",
          analysisResults: "Analysis Results",
          experimentPlanResults: "Experiment Plan Results",
          experimentResults: "Experiment Results",
          status: {
            excellent: "Excellent",
            good: "Good",
            needsImprovement: "Needs Improvement",
            sufficient: "Sufficient",
            moderate: "Moderate"
          },
          units: {
            celsius: "°C",
            bar: "bar",
            minutes: "min",
            molar: "M",
            rpm: "rpm",
            percent: "%"
          }
        }
      },
      productModeling: {
        subtitle: "Build and deploy machine learning models for product quality prediction",
        modelTypes: {
          neuralNetwork: {
            name: "Neural Network",
            description: "Deep learning model for complex patterns"
          },
          randomForest: {
            name: "Random Forest",
            description: "Ensemble method for feature importance"
          },
          xgboost: {
            name: "XGBoost",
            description: "Gradient boosting for high performance"
          },
          svm: {
            name: "Support Vector Machine",
            description: "SVM for classification and regression"
          }
        },
        sections: {
          configuration: "Model Configuration",
          inputFeatures: "Input Features",
          modelPerformance: "Model Performance",
          dataTraining: "Data & Training",
          datasetInfo: "Dataset Info",
          predictions: "Predictions"
        },
        features: {
          temperature: "Temperature",
          pressure: "Pressure",
          flowRate: "Flow Rate",
          humidity: "Humidity",
          phLevel: "pH Level",
          viscosity: "Viscosity"
        },
        metrics: {
          accuracy: "Accuracy",
          f1Score: "F1 Score",
          precision: "Precision"
        },
        buttons: {
          uploadData: "Upload Data",
          trainModel: "Train Model",
          validateModel: "Validate Model"
        },
        dataInfo: {
          totalSamples: "Total Samples",
          trainingSet: "Training Set",
          validationSet: "Validation Set",
          features: "Features"
        },
        predictions: {
          qualityScore: "Quality Score",
          defectRate: "Defect Rate",
          confidence: "Confidence"
        }
      },
      costManagement: {
        subtitle: "Monitor and optimize manufacturing costs across all processes",
        periods: {
          daily: "Daily",
          weekly: "Weekly",
          monthly: "Monthly",
          yearly: "Yearly"
        },
        categories: {
          materialCosts: "Material Costs",
          laborCosts: "Labor Costs",
          energyCosts: "Energy Costs",
          overhead: "Overhead"
        },
        overview: {
          totalCost: "Total Cost",
          costPerUnit: "Cost per Unit",
          budgetRemaining: "Budget Remaining",
          savingsTarget: "Savings Target"
        },
        sections: {
          costBreakdown: "Cost Breakdown",
          costCalculator: "Cost Calculator",
          costOptimization: "Cost Optimization",
          quickActions: "Quick Actions"
        },
        calculator: {
          productionVolume: "Production Volume",
          materialCostPerUnit: "Material Cost per Unit",
          calculateCost: "Calculate Cost"
        },
        optimization: {
          materialWaste: "Material Waste",
          energyEfficiency: "Energy Efficiency",
          laborUtilization: "Labor Utilization"
        },
        buttons: {
          generateReport: "Generate Report",
          exportData: "Export Data",
          setBudgetAlert: "Set Budget Alert"
        },
        trends: {
          fromLastMonth: "from last month"
        }
      },
      aiReport: {
        subtitle: "Generate intelligent reports and insights using AI analysis",
        reportTypes: {
          productionSummary: "Production Summary",
          qualityAnalysis: "Quality Analysis",
          costOptimization: "Cost Optimization",
          predictiveInsights: "Predictive Insights"
        },
        sections: {
          configuration: "Report Configuration",
          reportLibrary: "Report Library",
          recentReports: "Recent Reports",
          aiInsights: "AI Insights",
          quickActions: "Quick Actions"
        },
        parameters: {
          dateRange: "Date Range",
          reportFormat: "Report Format",
          includeSections: "Include Sections"
        },
        dateRanges: {
          last7Days: "Last 7 days",
          last30Days: "Last 30 days",
          last90Days: "Last 90 days",
          customRange: "Custom range"
        },
        formats: {
          pdf: "PDF",
          excel: "Excel",
          powerpoint: "PowerPoint",
          html: "HTML"
        },
        includeSections: {
          executiveSummary: "Executive Summary",
          dataAnalysis: "Data Analysis",
          trendsPatterns: "Trends & Patterns",
          recommendations: "Recommendations",
          riskAssessment: "Risk Assessment",
          appendices: "Appendices"
        },
        buttons: {
          generateAiReport: "Generate AI Report",
          scheduleReport: "Schedule Report",
          templateLibrary: "Template Library",
          exportSettings: "Export Settings",
          view: "View",
          download: "Download"
        },
        status: {
          completed: "completed",
          generating: "generating",
          failed: "failed"
        },
        insights: [
          "Production efficiency increased by 12% this month compared to the previous period.",
          "Quality defect rate shows a declining trend, suggesting improved process control.",
          "Cost optimization opportunities identified in material procurement processes."
        ]
      }
    },
    // Settings
    settings: {
      title: 'Settings',
      subtitle: 'Manage application settings',
      language: {
        title: 'Language',
        subtitle: 'Choose your preferred language',
        korean: 'Korean',
        english: 'English',
        currentLanguage: 'Current Language',
        changeLanguage: 'Change Language',
      },
      theme: {
        title: 'Theme',
        subtitle: 'Select your screen theme',
        light: 'Light Mode',
        dark: 'Dark Mode',
        system: 'System Settings',
      },
      notifications: {
        title: 'Notifications',
        subtitle: 'Manage notification settings',
        enable: 'Enable Notifications',
        disable: 'Disable Notifications',
        sound: 'Notification Sound',
        email: 'Email Notifications',
        push: 'Push Notifications',
      },
      privacy: {
        title: 'Privacy',
        subtitle: 'Privacy protection settings',
        dataCollection: 'Data Collection',
        analytics: 'Analytics Data',
        cookies: 'Cookie Settings',
      },
      account: {
        title: 'Account',
        subtitle: 'Manage account information',
        profile: 'Profile',
        security: 'Security',
        preferences: 'Preferences',
      },
      advanced: {
        title: 'Advanced Settings',
        subtitle: 'Advanced features and developer options',
        debug: 'Debug Mode',
        api: 'API Settings',
        cache: 'Cache Settings',
        reset: 'Reset Settings',
      },
    },
    // Process Analysis
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
    },

          // Chatbot
    chatbot: {
      title: 'AI Process Expert',
      titleWithTopic: 'AI Process Expert (Process Analysis)',
      titleGeneral: 'DX-AI Manufacturing Copilot',
      minimizedText: 'AI Process Expert',
      minimizedTextGeneral: 'AI Manufacturing Expert',
      placeholder: 'Ask about process analysis...',
      placeholderGeneral: 'Ask about DX-AI Manufacturing Copilot...',
      greeting: {
        hello: 'Hello! 👋',
        description: 'If you have any questions about process analysis, please feel free to ask anytime.',
        descriptionGeneral: 'If you have any questions about DX-AI Manufacturing Copilot, please feel free to ask anytime.'
      },
      actions: {
        send: 'Send',
        clear: 'Clear',
        minimize: 'Minimize',
        close: 'Close',
        settings: 'Settings',
        reset: 'Reset Chat',
        drag: 'Drag to move'
      },
      status: {
        generating: 'Generating response...',
        processing: 'Processing...',
        typing: 'Type a message...',
        sendWithEnter: 'Send with Enter'
      },
      resize: {
        diagonal: 'Diagonal resize',
        horizontal: 'Horizontal resize', 
        vertical: 'Vertical resize'
      },
      settings: {
        title: 'Chatbot Settings',
        model: 'LLM Model',
        temperature: 'Temperature',
        temperatureDesc: 'Controls response creativity (0.1-1.0)',
        temperatureMin: 'More consistent answers (0.0)',
        temperatureMax: 'More creative answers (2.0)',
        maxTokens: 'Max Tokens',
        maxTokensDesc: 'Generates longer responses but slower speed.',
        maxTurns: 'Max Memory Turns',
        maxTurnsDesc: 'Number of recent conversation turns to remember. Higher values retain longer context.',
        ollamaUrl: 'Ollama Base URL',
        streaming: 'Enable Streaming',
        streamingDesc: 'Get real-time responses.',
        resetDefaults: 'Reset to Defaults',
        loadError: 'Failed to load settings',
        saveError: 'Failed to save settings',
        currentSettings: 'Current Settings',
        modelLabel: 'Model',
        maxTokensLabel: 'Max Tokens',
        maxTurnsLabel: 'Max Memory Turns',
        streamingLabel: 'Streaming',
        enabled: 'Enabled',
        disabled: 'Disabled',
        reset: 'Reset',
        cancel: 'Cancel',
        save: 'Save',
        saving: 'Saving...'
      }
    },

      // Common
    common: {
      loading: 'Loading...',
      error: 'An error occurred',
      success: 'Successfully completed',
      cancel: 'Cancel',
      confirm: 'Confirm',
      save: 'Save',
      saving: 'Saving...',
      create: 'Create',
      creating: 'Creating...',
      update: 'Update',
      edit: 'Edit',
      delete: 'Delete',
      close: 'Close',
      search: 'Search',
      filter: 'Filter',
      sort: 'Sort',
      reset: 'Reset',
      apply: 'Apply',
      export: 'Export',
      import: 'Import',
      download: 'Download',
      upload: 'Upload',
      refresh: 'Refresh',
      settings: 'Settings',
      help: 'Help',
      back: 'Back',
      next: 'Next',
      previous: 'Previous',
      more: 'More',
      less: 'Less',
      view: 'View',
      hide: 'Hide',
      show: 'Show',
    },
    // Dify Service
    difyService: {
      subtitle: "Manage custom AI services through local Dify instances",
      statusCards: {
        totalServices: "Total Services",
        activeServices: "Active Services",
        totalApps: "Total Apps", 
        connectionStatus: "Connection Status",
        connected: "Connected",
        disconnected: "Disconnected"
      },
      sections: {
        serviceManagement: "Service Management",
        appStore: "App Store",
        activeServices: "Active Services",
        configuration: "Configuration",
        quickActions: "Quick Actions"
      },
      serviceForm: {
        name: "Service Name",
        description: "Description",
        apiUrl: "API URL",
        apiKey: "API Key",
        placeholders: {
          name: "My Dify Service",
          description: "Local Dify instance description",
          apiUrl: "http://localhost:5001/v1",
          apiKey: "app-xxxxxxxxxx"
        }
      },
      serviceStatus: {
        active: "Active",
        inactive: "Inactive",
        testing: "Testing Connection",
        error: "Error"
      },
      appTypes: {
        chatbot: "Chatbot",
        agent: "Agent",
        workflow: "Workflow"
      },
      buttons: {
        addService: "Add Service",
        editService: "Edit Service",
        deleteService: "Delete Service",
        testConnection: "Test Connection",
        createApp: "Create App",
        viewApps: "View Apps",
        activate: "Activate",
        deactivate: "Deactivate"
      },
      testResults: {
        success: "Connection Successful",
        failed: "Connection Failed",
        latency: "Response Time",
        appsFound: "Apps Found"
      },
      messages: {
        serviceCreated: "Service created successfully",
        serviceUpdated: "Service updated successfully",
        serviceDeleted: "Service deleted",
        noServices: "No Dify services registered",
        noApps: "No apps available",
        connectionFailed: "Failed to connect to service"
      },
              errors: {
          invalidUrl: "Invalid URL",
          invalidApiKey: "Invalid API key",
          connectionTimeout: "Connection timeout",
          serviceNotFound: "Service not found"
        },
        emptyStates: {
          noServicesTitle: "No Services Yet",
          noActiveServiceTitle: "No Active Service",
          selectActiveService: "Select an active service to view apps", 
          noAppsTitle: "No Apps Found",
          createFirstApp: "Create First App"
        },
        appForm: {
          name: "App Name",
          description: "Description", 
          type: "App Type",
          placeholders: {
            name: "Enter app name",
            description: "Enter app description"
          }
        }
      }
  }
} as const

export type TranslationKey = keyof typeof translations.ko 