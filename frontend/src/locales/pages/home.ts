export const homeTranslations = {
  ko: {
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
        workflowAutomization: '워크플로우 자동화',
        aiAgent: 'AI 에이전트 통합'
      }
    },
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
    stats: {
      title: '실시간 성과 지표',
      subtitle: '데이터 기반 의사결정을 위한 핵심 메트릭',
      processOptimization: '공정 최적화',
      qualityImprovement: '품질 개선',
      costReduction: '비용 절감',
      productionEfficiency: '생산 효율성',
    },
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
    }
  },
  en: {
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
        workflowAutomization: 'Workflow Automation',
        aiAgent: 'AI Agent Integration'
      }
    },
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
    stats: {
      title: 'Real-time Performance Metrics',
      subtitle: 'Key metrics for data-driven decision making',
      processOptimization: 'Process Optimization',
      qualityImprovement: 'Quality Improvement',
      costReduction: 'Cost Reduction',
      productionEfficiency: 'Production Efficiency',
    },
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
    }
  }
} as const 