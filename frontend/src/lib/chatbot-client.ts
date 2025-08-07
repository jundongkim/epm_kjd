// 인터페이스 정의
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ChatRequest {
  message: string;
  topic?: string;
  session_id?: string;
  context?: string;
  simulation_params?: Record<string, unknown>;
  model?: string;
  temperature?: number;
}

export interface StreamData {
  type: 'session_info' | 'content' | 'done' | 'error';
  content?: string;
  session_id?: string;
  topic?: string;
  turn_count?: number;
  model_used?: string;
  error?: string;
  timestamp?: string;
}

export interface ChatConfig {
  current_model: string;
  temperature: number;
  max_tokens: number;
  max_turn_count: number;
  ollama_base_url: string;
  enable_streaming: boolean;
}

export class ChatbotClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL ? 
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chatbot` : 
      'http://localhost:8000/api/v1/chatbot';
  }

  /**
   * 간단한 스트리밍 채팅 (기존 FloatingChatbot 방식)
   */
  async *streamChat(request: ChatRequest): AsyncGenerator<StreamData, void, unknown> {
    console.log('🔄 스트리밍 API 호출:', {
      message: request.message.substring(0, 50) + '...',
      topic: request.topic,
      sessionId: request.session_id,
      hasContext: !!request.context
    });

    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: request.message,
          topic: request.topic || 'process_analysis',
          session_id: request.session_id || 'default',
          context: request.context || '',
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      // 세션 정보 먼저 보내기
      yield {
        type: 'session_info',
        session_id: request.session_id || 'default',
        topic: request.topic || 'process_analysis',
        turn_count: 1,
        model_used: 'ollama',
        timestamp: new Date().toISOString()
      };

      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 마지막 불완전한 라인 보관

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          try {
            // 안전한 파싱
            let jsonStr = '';
            if (line.startsWith('data: ')) {
              jsonStr = line.substring(6); // 'data: ' 제거
            } else if (line.trim() !== '') {
              jsonStr = line.trim();
            } else {
              continue; // 빈 라인 건너뛰기
            }

            // JSON 파싱 시도
            const data = JSON.parse(jsonStr);
            console.log('📨 파싱 성공:', data);

            if (data.type === 'session_info') {
              yield {
                type: 'session_info',
                session_id: data.session_id,
                topic: data.topic,
                timestamp: new Date().toISOString()
              };
            } else if (data.type === 'content' && data.content) {
              yield {
                type: 'content',
                content: data.content,
                timestamp: new Date().toISOString()
              };
            } else if (data.type === 'done') {
              yield {
                type: 'done',
                timestamp: new Date().toISOString()
              };
              return;
            } else if (data.type === 'error') {
              yield {
                type: 'error',
                error: data.error || 'Unknown error',
                timestamp: new Date().toISOString()
              };
              return;
            }
          } catch (parseError) {
            const errorMessage = parseError instanceof Error ? parseError.message : 'Unknown error';
            console.warn('⚠️ JSON 파싱 실패:', errorMessage);
            console.warn('문제 라인:', line);
            
            // 파싱 실패한 라인이 의미있는 텍스트인지 확인
            const cleanLine = line.replace(/^data:\s*/, '').trim();
            if (cleanLine && cleanLine.length > 0 && !cleanLine.startsWith('{')) {
              console.log('📝 일반 텍스트로 처리:', cleanLine);
              yield {
                type: 'content',
                content: cleanLine,
                timestamp: new Date().toISOString()
              };
            }
          }
        }
      }

      // 완료 신호
      yield {
        type: 'done',
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('스트리밍 오류:', error);
      yield {
        type: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * 🚀 NEW: JSON 기반 일반 채팅
   */
  async sendMessage(request: ChatRequest): Promise<string> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: request.message,
        topic: request.topic || 'process_analysis',
        session_id: request.session_id || 'default',
        context: request.context || '', // JSON 기반 시스템에서는 폴백용으로만 사용
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.response || '응답을 받을 수 없습니다.';
  }

  /**
   * 설정 조회
   */
  async getConfig(): Promise<ChatConfig> {
    const response = await fetch(`${this.baseUrl}/config`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * 설정 업데이트
   */
  async updateConfig(config: Partial<ChatConfig>): Promise<ChatConfig> {
    const response = await fetch(`${this.baseUrl}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}

// 기본 클라이언트 인스턴스
export const chatbotClient = new ChatbotClient(); 