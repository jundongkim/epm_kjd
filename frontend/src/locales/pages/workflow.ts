export const workflowTranslations = {
  ko: {
    dashboard: {
      workflow: {
        subtitle: "n8n을 활용한 자동화 워크플로우 관리",
        // 상태 카드
        statusCards: {
          totalWorkflows: "총 워크플로우",
          activeWorkflows: "활성 워크플로우",
          totalTemplates: "템플릿 수",
          n8nStatus: "n8n 상태"
        },
        // 탭
        tabs: {
          workflows: "워크플로우",
          executions: "실행 기록",
          templates: "템플릿",
          test: "테스트"
        },
        // 상태
        status: {
          healthy: "정상",
          unhealthy: "오류",
          checking: "확인중",
          active: "활성",
          inactive: "비활성",
          success: "성공",
          failed: "실패",
          running: "실행중",
          completed: "완료",
          error: "오류"
        },
        // 버튼
        buttons: {
          openN8n: "n8n 열기",
          refresh: "새로고침",
          refreshing: "새로고침 중...",
          execute: "실행",
          executing: "실행 중...",
          viewResult: "결과 보기",
          activate: "활성화",
          deactivate: "비활성화",
          delete: "삭제",
          copy: "복사",
          close: "닫기",
          createFromTemplate: "템플릿에서 생성",
          createAllTemplates: "모든 템플릿 생성",
          createInN8n: "n8n에 생성",
          templateCopy: "템플릿 복사",
          showTemplates: "템플릿 보기",
          runWorkflow: "워크플로우 실행하기",
          resetFilter: "필터 초기화"
        },
        // 헤더
        header: {
          title: "워크플로우",
          subtitle: "n8n을 활용한 자동화 워크플로우 관리"
        },
        // 섹션 제목
        sections: {
          workflowList: "워크플로우 목록",
          executionHistory: "실행 기록",
          workflowTemplates: "워크플로우 템플릿",
          executionResult: "워크플로우 실행 결과",
          responseData: "응답 데이터",
          webhookResponse: "웹훅 응답",
          fullResponse: "전체 응답",
          errorInfo: "오류 정보",
          executionInfo: "실행 정보"
        },
        // 폼 라벨
        form: {
          workflowName: "워크플로우 이름",
          category: "카테고리",
          sortBy: "정렬",
          allCategories: "전체",
          sortByName: "이름순",
          sortByCategory: "카테고리순",
          sortByNodesDesc: "노드 많은순",
          sortByNodesAsc: "노드 적은순"
        },
        // 메시지
        messages: {
          deleteConfirm: "정말로 이 워크플로우를 삭제하시겠습니까?",
          createAllConfirm: "모든 템플릿 워크플로우를 n8n에 생성하시겠습니까?",
          createTemplateConfirm: "이 템플릿 워크플로우를 n8n에 생성하시겠습니까?",
          createSuccess: "워크플로우 생성 성공!",
          createFailed: "워크플로우 생성 실패",
          executionSuccess: "실행 성공",
          executionFailed: "실행 실패",
          loadingWorkflows: "워크플로우 데이터를 로드하는 중...",
          loadingTemplates: "템플릿을 로드하는 중...",
          unknown: "알 수 없음",
          noDescription: "설명이 없습니다.",
          promptWorkflowName: "워크플로우 이름을 입력하세요:",
          more: "더보기"
        },
        // 워크플로우 정보
        workflow: {
          nodes: "노드",
          created: "생성",
          updated: "수정",
          description: "설명",
          tags: "태그",
          workflowChart: "워크플로우",
          executionId: "실행 ID",
          workflowId: "워크플로우",
          status: "상태",
          executionTime: "실행 시간",
          startTime: "시작",
          endTime: "완료"
        },
        // 빈 상태
        emptyState: {
          noWorkflows: {
            title: "No Workflows Yet",
            subtitle: "생성된 워크플로우가 없습니다.",
            description: "템플릿에서 새 워크플로우를 생성하거나 n8n에서 직접 만들어보세요."
          },
          noExecutions: {
            title: "No Executions Yet",
            subtitle: "실행 기록이 없습니다."
          },
          noTemplates: {
            title: "Loading Templates",
            subtitle: "템플릿을 로드하는 중..."
          },
          noTemplatesFiltered: {
            title: "No Templates Found",
            subtitle: "선택한 조건에 맞는 템플릿이 없습니다."
          }
        },
        // 통계
        stats: {
          total: "총",
          recent: "최근",
          templates: "개 템플릿",
          executions: "개",
          workflows: "개",
          nodes: "개 노드"
        },
        // 실행 결과 모달
        executionModal: {
          title: "워크플로우 실행 결과",
          message: "메시지",
          copyResponse: "응답 데이터 복사",
          copyFull: "전체 응답 복사",
          copyError: "오류 정보 복사"
        },
        // 미니 플로우차트
        miniFlow: {
          moreNodes: "개 더"
        }
      }
    },
    // 독립적인 workflow 구조 (페이지 레벨)
    workflow: {
      title: "워크플로우",
      subtitle: "n8n을 활용한 자동화 워크플로우로 반복 작업을 효율적으로 관리합니다."
    }
  },
  en: {
    dashboard: {
      workflow: {
        subtitle: "Automated workflow management using n8n",
        // Status Cards
        statusCards: {
          totalWorkflows: "Total Workflows",
          activeWorkflows: "Active Workflows",
          totalTemplates: "Total Templates",
          n8nStatus: "n8n Status"
        },
        // Tabs
        tabs: {
          workflows: "Workflows",
          executions: "Executions",
          templates: "Templates",
          test: "Test"
        },
        // Status
        status: {
          healthy: "Healthy",
          unhealthy: "Error",
          checking: "Checking",
          active: "Active",
          inactive: "Inactive",
          success: "Success",
          failed: "Failed",
          running: "Running",
          completed: "Completed",
          error: "Error"
        },
        // Buttons
        buttons: {
          openN8n: "Open n8n",
          refresh: "Refresh",
          refreshing: "Refreshing...",
          execute: "Execute",
          executing: "Executing...",
          viewResult: "View Result",
          activate: "Activate",
          deactivate: "Deactivate",
          delete: "Delete",
          copy: "Copy",
          close: "Close",
          createFromTemplate: "Create from Template",
          createAllTemplates: "Create All Templates",
          createInN8n: "Create in n8n",
          templateCopy: "Copy Template",
          showTemplates: "View Templates",
          runWorkflow: "Run Workflow",
          resetFilter: "Reset Filter"
        },
        // Header
        header: {
          title: "Workflow",
          subtitle: "Automated workflow management using n8n"
        },
        // Section Titles
        sections: {
          workflowList: "Workflow List",
          executionHistory: "Execution History",
          workflowTemplates: "Workflow Templates",
          executionResult: "Workflow Execution Result",
          responseData: "Response Data",
          webhookResponse: "Webhook Response",
          fullResponse: "Full Response",
          errorInfo: "Error Information",
          executionInfo: "Execution Information"
        },
        // Form Labels
        form: {
          workflowName: "Workflow Name",
          category: "Category",
          sortBy: "Sort By",
          allCategories: "All",
          sortByName: "Name",
          sortByCategory: "Category",
          sortByNodesDesc: "Most Nodes",
          sortByNodesAsc: "Fewest Nodes"
        },
        // Messages
        messages: {
          deleteConfirm: "Are you sure you want to delete this workflow?",
          createAllConfirm: "Do you want to create all template workflows in n8n?",
          createTemplateConfirm: "Do you want to create this template workflow in n8n?",
          createSuccess: "Workflow created successfully!",
          createFailed: "Workflow creation failed",
          executionSuccess: "Execution Success",
          executionFailed: "Execution Failed",
          loadingWorkflows: "Loading workflow data...",
          loadingTemplates: "Loading templates...",
          unknown: "Unknown",
          noDescription: "No description available.",
          promptWorkflowName: "Enter workflow name:",
          more: "More"
        },
        // Workflow Info
        workflow: {
          nodes: "Nodes",
          created: "Created",
          updated: "Updated",
          description: "Description",
          tags: "Tags",
          workflowChart: "Workflow",
          executionId: "Execution ID",
          workflowId: "Workflow",
          status: "Status",
          executionTime: "Execution Time",
          startTime: "Started",
          endTime: "Completed"
        },
        // Empty State
        emptyState: {
          noWorkflows: {
            title: "No Workflows Yet",
            subtitle: "No workflows have been created.",
            description: "Create a new workflow from templates or build directly in n8n."
          },
          noExecutions: {
            title: "No Executions Yet",
            subtitle: "No execution history available."
          },
          noTemplates: {
            title: "Loading Templates",
            subtitle: "Loading templates..."
          },
          noTemplatesFiltered: {
            title: "No Templates Found",
            subtitle: "No templates match the selected criteria."
          }
        },
        // Statistics
        stats: {
          total: "Total",
          recent: "Recent",
          templates: " templates",
          executions: "",
          workflows: "",
          nodes: " nodes"
        },
        // Execution Result Modal
        executionModal: {
          title: "Workflow Execution Result",
          message: "Message",
          copyResponse: "Copy Response Data",
          copyFull: "Copy Full Response",
          copyError: "Copy Error Information"
        },
        // Mini Flow Chart
        miniFlow: {
          moreNodes: " more"
        }
      }
    },
    // Independent workflow structure (page level)
    workflow: {
      title: "Workflow",
      subtitle: "Efficiently manage repetitive tasks with automated workflows using n8n."
    }
  }
} as const 