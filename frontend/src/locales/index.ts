import { experimentDesignTranslations } from './pages/experimentDesign'
import { productModelingTranslations } from './pages/productModeling'
import { processAnalysisTranslations } from './pages/processAnalysis'
import { dataGenerationTranslations } from './pages/dataGeneration'
import { dataAnalysisWorkflowTranslations } from './pages/dataAnalysisWorkflow'
import { costManagementTranslations } from './pages/costManagement'
import { aiReportTranslations } from './pages/aiReport'
import { aiAgentTranslations } from './pages/aiAgent'
import { workflowTranslations } from './pages/workflow'
import { homeTranslations } from './pages/home'
import { iotPrismDemo } from './pages/iotPrismDemo'
import { settingsTranslations } from './components/settings'
import { chatbotTranslations } from './components/chatbot'
import { translations as fullTranslations } from './translations'

// 기본 번역 (임시)
const basicTranslations = {
  ko: {
    nav: {
      home: '홈',
      dataGeneration: '데이터 생성',
      processAnalysis: '공정 분석',
      experimentDesign: '실험 설계',
      productDataAnalysis: '데이터 분석',
      dataAnalysisWorkflow: '데이터 분석 워크플로우',
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
      iotPrismDemo: 'IoT Prism',
    },
    common: {
      loading: '로딩 중...',
      error: '오류가 발생했습니다',
      success: '성공적으로 완료되었습니다',
      cancel: '취소',
      confirm: '확인',
      save: '저장',
      close: '닫기',
      view: '보기',
      hide: '숨기기',
      show: '보이기',
    }
  },
  en: {
    nav: {
      home: 'Home',
      dataGeneration: 'Data Gen',
      processAnalysis: 'Process Analysis',
      experimentDesign: 'Experiment Design',
      productDataAnalysis: 'Product Data Analysis',
      dataAnalysisWorkflow: 'Data Analysis Workflow',
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
      iotPrismDemo: 'IoT Prism',
    },
    common: {
      loading: 'Loading...',
      error: 'An error occurred',
      success: 'Successfully completed',
      cancel: 'Cancel',
      confirm: 'Confirm',
      save: 'Save',
      close: 'Close',
      view: 'View',
      hide: 'Hide',
      show: 'Show',
    }
  }
}

// 번역 통합
export const translations = {
  ko: {
    // 기본
    ...basicTranslations.ko,

    // Contact 섹션 추가
    contact: fullTranslations.ko.contact,

    // Dashboard 구조 직접 구성
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
      // 각 페이지별 dashboard 섹션 - 전체 dashboard 내용 포함
      ...experimentDesignTranslations.ko.dashboard || {},
      ...productModelingTranslations.ko.dashboard || {},
      ...costManagementTranslations.ko.dashboard || {},
      ...aiReportTranslations.ko.dashboard || {},
      ...aiAgentTranslations.ko.dashboard || {},
      ...workflowTranslations.ko.dashboard || {},
    },

    // 홈 페이지 번역
    ...homeTranslations.ko,

    // 페이지별 번역 (dashboard 제외)
    experimentDesign: experimentDesignTranslations.ko.experimentDesign,
    productModeling: productModelingTranslations.ko.productModeling,
    processAnalysis: processAnalysisTranslations.ko.processAnalysis,
    dataGeneration: dataGenerationTranslations.ko.dataGeneration,
    dataAnalysisWorkflow: dataAnalysisWorkflowTranslations.ko.dataAnalysisWorkflow,
    costManagement: costManagementTranslations.ko.costManagement,
    aiReport: aiReportTranslations.ko.aiReport,
    aiAgent: aiAgentTranslations.ko.aiAgent,
    workflow: workflowTranslations.ko.workflow,
    iotPrismDemo: iotPrismDemo.ko,

    // 컴포넌트 번역
    ...settingsTranslations.ko,
    ...chatbotTranslations.ko,
  },
  en: {
    // 기본
    ...basicTranslations.en,

    // Contact 섹션 추가
    contact: fullTranslations.en.contact,

    // Dashboard 구조 직접 구성
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
      // 각 페이지별 dashboard 섹션 - 전체 dashboard 내용 포함
      ...experimentDesignTranslations.en.dashboard || {},
      ...productModelingTranslations.en.dashboard || {},
      ...costManagementTranslations.en.dashboard || {},
      ...aiReportTranslations.en.dashboard || {},
      ...aiAgentTranslations.en.dashboard || {},
      ...workflowTranslations.en.dashboard || {},
    },

    // 홈 페이지 번역
    ...homeTranslations.en,

    // 페이지별 번역 (dashboard 제외)
    experimentDesign: experimentDesignTranslations.en.experimentDesign,
    productModeling: productModelingTranslations.en.productModeling,
    processAnalysis: processAnalysisTranslations.en.processAnalysis,
    dataGeneration: dataGenerationTranslations.en.dataGeneration,
    dataAnalysisWorkflow: dataAnalysisWorkflowTranslations.en.dataAnalysisWorkflow,
    costManagement: costManagementTranslations.en.costManagement,
    aiReport: aiReportTranslations.en.aiReport,
    aiAgent: aiAgentTranslations.en.aiAgent,
    workflow: workflowTranslations.en.workflow,
    iotPrismDemo: iotPrismDemo.en,

    // 컴포넌트 번역
    ...settingsTranslations.en,
    ...chatbotTranslations.en,
  }
} as const

export type TranslationKey = keyof typeof translations.ko