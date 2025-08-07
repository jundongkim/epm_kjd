import { useState, useCallback, useMemo } from 'react';
import { 
  chatbotClient, 
  ChatMessage, 
  ChatRequest,
} from '@/lib/chatbot-client';

export interface ChatSession {
  session_id: string;
  topic: string;
  turn_count: number;
  message_count: number;
  created_at: string;
  model_used: string;
}

export interface UseChatbotProps {
  topic?: string;
  sessionId?: string;
  enableStreaming?: boolean;
  simulationParams?: Record<string, unknown>;
}

export function useChatbot({
  topic = 'process_analysis',
  sessionId = 'default',
  enableStreaming = true,
  simulationParams
}: UseChatbotProps = {}) {
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionInfo, setSessionInfo] = useState<ChatSession | null>(null);
  const [currentTopic, setCurrentTopic] = useState(topic);
  const [currentSimulationParams, setCurrentSimulationParams] = useState(simulationParams);

  // chatbotClient를 안정적인 참조로 유지
  const stableChatbotClient = useMemo(() => chatbotClient, []);

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const sendMessage = useCallback(async (message: string, context?: string) => {
    if (isLoading || isStreaming) return;

    setError(null);
    
    // 사용자 메시지 추가
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    addMessage(userMessage);

    const request: ChatRequest = {
      message,
      topic: currentTopic,
      session_id: sessionId,
      context,
      simulation_params: currentSimulationParams
    };

    try {
      if (enableStreaming) {
        setIsStreaming(true);
        
        // 스트리밍 모드 - 중복 방지 최적화
        let assistantMessage: ChatMessage | null = null;
        let accumulatedContent = '';
        
        for await (const data of stableChatbotClient.streamChat(request)) {
          if (data.type === 'session_info') {
            setSessionInfo({
              session_id: data.session_id || sessionId,
              topic: data.topic || currentTopic,
              turn_count: data.turn_count || 0,
              message_count: 0,
              created_at: new Date().toISOString(),
              model_used: data.model_used || 'unknown'
            });
          } else if (data.type === 'content') {
            // 콘텐츠 누적 및 중복 방지
            if (data.content) {
              accumulatedContent += data.content;
              
              if (!assistantMessage) {
                // 첫 번째 청크
                assistantMessage = {
                  role: 'assistant',
                  content: accumulatedContent,
                  timestamp: new Date().toISOString()
                };
                addMessage(assistantMessage);
              } else {
                // 후속 청크 - 전체 메시지 업데이트
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  
                  if (lastMessage && lastMessage.role === 'assistant') {
                    newMessages[newMessages.length - 1] = {
                      ...lastMessage,
                      content: accumulatedContent,
                      timestamp: new Date().toISOString()
                    };
                  }
                  
                  return newMessages;
                });
              }
            }
          } else if (data.type === 'error') {
            setError(data.error || 'Unknown error occurred');
            break;
          } else if (data.type === 'done') {
            break;
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  }, [
    isLoading, 
    isStreaming, 
    currentTopic, 
    sessionId, 
    currentSimulationParams, 
    enableStreaming, 
    addMessage
  ]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const resetSession = useCallback(() => {
    setMessages([]);
    setError(null);
    setSessionInfo(null);
  }, []);

  const setTopic = useCallback((newTopic: string) => {
    setCurrentTopic(newTopic);
  }, []);

  const setSimulationParams = useCallback((params: Record<string, unknown>) => {
    setCurrentSimulationParams(params);
  }, []);

  return {
    // 상태
    messages,
    isLoading,
    isStreaming,
    error,
    sessionInfo,
    
    // 액션
    sendMessage,
    clearMessages,
    resetSession,
    
    // 설정
    setTopic,
    setSimulationParams,
    
    // 클라이언트
    chatbotClient: stableChatbotClient
  };
} 