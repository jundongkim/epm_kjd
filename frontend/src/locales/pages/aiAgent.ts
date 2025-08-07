export const aiAgentTranslations = {
  ko: {
    dashboard: {
      aiAgent: {
        subtitle: "Dify local hosting을 통해 커스텀 AI 서비스를 정의하고 관리합니다",
        // 상태 카드
        statusCards: {
          totalAgents: "등록된 에이전트",
          activeAgents: "활성 에이전트",
          totalChats: "총 대화 수",
          totalTemplates: "템플릿 수",
          difyStatus: "Dify 상태"
        },
        // 탭
        tabs: {
          overview: "개요",
          agents: "에이전트",
          templates: "템플릿"
        },
        // 상태
        status: {
          all: "모든 상태",
          active: "활성",
          inactive: "비활성",
          error: "오류",
          healthy: "정상",
          unhealthy: "오류",
          checking: "확인중",
          notUsed: "사용 안함",
          configured: "설정됨",
          notConfigured: "미설정"
        },
        // 타입
        types: {
          all: "모든 유형",
          chatbot: "ChatBot",
          workflow: "Workflow",
          agent: "Agent",
          completion: "Completion"
        },
        // 버튼
        buttons: {
          save: "저장",
          saving: "설정 중...",
          create: "생성",
          creating: "생성 중...",
          instantUse: "즉시 사용",
          generating: "생성중...",
          edit: "편집",
          delete: "삭제",
          chat: "채팅",
          copy: "복사",
          refresh: "새로고침",
          openDify: "Dify 열기",
          retry: "다시 시도",
          manualCreate: "수동 설정으로 생성"
        },
        // 폼 라벨
        form: {
          name: "이름",
          description: "설명",
          apiKey: "API 키",
          agentId: "에이전트 ID",
          customName: "사용자 정의 이름",
          filterByStatus: "상태별 필터",
          filterByType: "유형별 필터",
          difyApiKey: "Dify App API 키",
          apiKeyPlaceholder: "app-xxxxxxxxxxxxxxxxx"
        },
        // 메시지
        messages: {
          chatRequestFailed: "채팅 요청 실패",
          chatError: "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.",
          autoCreateFailed: "자동 에이전트 생성 실패",
          createFailed: "에이전트 생성 실패",
          autoCreateError: "자동 생성에 실패했습니다.",
          loadAgentsFailed: "에이전트 목록을 불러오는데 실패했습니다.",
          loadTemplatesFailed: "템플릿 로드 실패:",
          deleteAgentFailed: "에이전트 삭제 실패:",
          instantCreateAgent: "즉시 사용 가능한 에이전트 생성",
          loadingAgents: "에이전트를 불러오는 중...",
          welcomeMessage: "안녕하세요! 무엇을 도와드릴까요?",
          inputPlaceholder: "메시지를 입력하세요..."
        },
        // 에이전트 정보
        agent: {
          lastUsed: "마지막 사용",
          apiKeyStatus: "API 키",
          createdAt: "생성일",
          description: "설명",
          type: "유형",
          status: "상태",
          conversations: "대화",
          assistant: "AI 어시스턴트"
        },
        // 템플릿
        template: {
          title: "템플릿에서 생성",
          description: "미리 만들어진 템플릿으로 빠르게 AI 에이전트를 생성할 수 있습니다.",
          selectTemplate: "템플릿 선택",
          features: "주요 기능"
        },
        // 필터
        filter: {
          status: "상태 필터",
          type: "유형 필터",
          search: "검색",
          searchPlaceholder: "에이전트 이름으로 검색..."
        },
        // 빈 상태
        emptyState: {
          noAgents: "등록된 에이전트가 없습니다",
          noTemplates: "사용 가능한 템플릿이 없습니다",
          createFirst: "첫 번째 에이전트를 만들어보세요"
        },
        // 개요
        overview: {
          typeDistribution: "에이전트 유형별 분포",
          recentActivity: "최근 활동"
        },
        // Dify iframe
        iframe: {
          description: "Dify 화면 열기",
          button: {
            open: "열기",
            close: "닫기"
          }
        }
      }
    },
    // 독립적인 aiAgent 구조 (페이지 레벨)
    aiAgent: {
      title: "AI 에이전트",
      subtitle: "Dify local hosting을 통해 커스텀 AI 서비스를 정의하고 관리합니다"
    }
  },
  en: {
    dashboard: {
      aiAgent: {
        subtitle: "Define and manage custom AI services through Dify local hosting",
        // Status Cards
        statusCards: {
          totalAgents: "Total Agents",
          activeAgents: "Active Agents",
          totalChats: "Total Chats",
          totalTemplates: "Total Templates",
          difyStatus: "Dify Status"
        },
        // Tabs
        tabs: {
          overview: "Overview",
          agents: "Agents",
          templates: "Templates"
        },
        // Status
        status: {
          all: "All Status",
          active: "Active",
          inactive: "Inactive",
          error: "Error",
          healthy: "Healthy",
          unhealthy: "Error",
          checking: "Checking",
          notUsed: "Not Used",
          configured: "Configured",
          notConfigured: "Not Configured"
        },
        // Types
        types: {
          all: "All Types",
          chatbot: "ChatBot",
          workflow: "Workflow",
          agent: "Agent",
          completion: "Completion"
        },
        // Buttons
        buttons: {
          save: "Save",
          saving: "Setting up...",
          create: "Create",
          creating: "Creating...",
          instantUse: "Instant Use",
          generating: "Generating...",
          edit: "Edit",
          delete: "Delete",
          chat: "Chat",
          copy: "Copy",
          refresh: "Refresh",
          openDify: "Open Dify",
          retry: "Retry",
          manualCreate: "Manual Setup"
        },
        // Form Labels
        form: {
          name: "Name",
          description: "Description",
          apiKey: "API Key",
          agentId: "Agent ID",
          customName: "Custom Name",
          filterByStatus: "Filter by Status",
          filterByType: "Filter by Type",
          difyApiKey: "Dify App API Key",
          apiKeyPlaceholder: "app-xxxxxxxxxxxxxxxxx"
        },
        // Messages
        messages: {
          chatRequestFailed: "Chat request failed",
          chatError: "Sorry, an error occurred. Please try again.",
          autoCreateFailed: "Auto agent creation failed",
          createFailed: "Agent creation failed",
          autoCreateError: "Auto creation failed.",
          loadAgentsFailed: "Failed to load agent list.",
          loadTemplatesFailed: "Template load failed:",
          deleteAgentFailed: "Agent deletion failed:",
          instantCreateAgent: "Create instantly available agent",
          loadingAgents: "Loading agents...",
          welcomeMessage: "Hello! How can I help you?",
          inputPlaceholder: "Type your message..."
        },
        // Agent Info
        agent: {
          lastUsed: "Last Used",
          apiKeyStatus: "API Key",
          createdAt: "Created At",
          description: "Description",
          type: "Type",
          status: "Status",
          conversations: "conversations",
          assistant: "AI Assistant"
        },
        // Template
        template: {
          title: "Create from Template",
          description: "Quickly create AI agents with pre-built templates.",
          selectTemplate: "Select Template",
          features: "Key Features"
        },
        // Filter
        filter: {
          status: "Status Filter",
          type: "Type Filter",
          search: "Search",
          searchPlaceholder: "Search by agent name..."
        },
        // Empty State
        emptyState: {
          noAgents: "No agents registered",
          noTemplates: "No templates available",
          createFirst: "Create your first agent"
        },
        // Overview
        overview: {
          typeDistribution: "Agent Type Distribution",
          recentActivity: "Recent Activity"
        },
        // Dify iframe
        iframe: {
          description: "Open Dify UI",
          button: {
            open: "Open",
            close: "Close"
          }
        }
      }
    },
    // Independent aiAgent structure (page level)
    aiAgent: {
      title: "AI Agent",
      subtitle: "Define and manage custom AI services through Dify local hosting"
    }
  }
} as const