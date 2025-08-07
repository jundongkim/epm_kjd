export const difyServiceTranslations = {
  ko: {
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