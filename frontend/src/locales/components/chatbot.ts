export const chatbotTranslations = {
  ko: {
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
    }
  },
  en: {
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
    }
  }
} as const 