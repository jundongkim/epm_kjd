export const experimentDesignTranslations = {
  ko: {
    dashboard: {
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
        },
        // experimentTab 구조 추가
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
          constraintAutoSetting: "실험 설계에서 설정한 인자들에 대한 제약조건이 자동으로 설정됩니다.",
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
      }
    },
    // 독립적인 experimentDesign 구조 (탭 메뉴 등에서 사용)
    experimentDesign: {
      subtitle: "DOE 방법론을 사용한 실험 설계 및 최적화",
      tabs: {
        experiment: "실험 설계",
        optimization: "최적화",
        report: "AI 보고서"
      }
    }
  },
  en: {
    dashboard: {
      experimentDesign: {
        subtitle: "Design and optimize experiments using DOE methodologies",
        designTypes: {
          factorial: {
            name: "Factorial Design",
            description: "Complete factorial experimental design"
          },
          responseSurface: {
            name: "Response Surface Method",
            description: "Box-Behnken or Central Composite Design"
          },
          optimal: {
            name: "Optimal Design",
            description: "D-optimal or I-optimal design"
          },
          mixture: {
            name: "Mixture Design", 
            description: "Simplex centroid or extreme vertices"
          }
        },
        sections: {
          configuration: "Experiment Configuration",
          factors: "Factors",
          responses: "Responses",
          actions: "Actions",
          designSummary: "Design Summary"
        },
        factors: {
          temperature: "Temperature (°C)",
          pressure: "Pressure (bar)",
          flowRate: "Flow Rate (L/min)"
        },
        responses: {
          yield: "Yield (%)",
          qualityScore: "Quality Score",
          productionCost: "Production Cost"
        },
        buttons: {
          generateDesign: "Generate Design",
          analyzeResults: "Analyze Results",
          exportDesign: "Export Design"
        },
        summary: {
          runs: "Runs",
          factors: "Factors",
          responses: "Responses",
          blocks: "Blocks"
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
          constraintAutoSetting: "Constraints for factors set in the experiment design will be automatically configured.",
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
      }
    },
    // 독립적인 experimentDesign 구조 (탭 메뉴 등에서 사용)
    experimentDesign: {
      subtitle: "Design and optimize experiments using DOE methodologies",
      tabs: {
        experiment: "Experiment Design",
        optimization: "Optimization", 
        report: "AI Report"
      }
    }
  }
} as const 