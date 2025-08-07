'use client';

import React, { useState, useRef, useEffect, useCallback, useDeferredValue } from 'react';
import { useChatbot, UseChatbotProps } from '@/hooks/useChatbot';
import MarkdownRenderer from './MarkdownRenderer';
import { 
  MessageCircle, X, Minus, RefreshCw, Send, Settings,
  Bot, User, AlertTriangle, Loader2, Move
} from 'lucide-react';
import ChatbotSettings from './ChatbotSettings';
import { useTranslation } from '@/hooks/useTranslation';

interface FloatingChatbotProps extends UseChatbotProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  theme?: 'light' | 'dark';
  accentColor?: string;
  minimizedText?: string;
  placeholder?: string;
  maxHeight?: number;
  width?: number;
  showSessionInfo?: boolean;
  onToggle?: (isOpen: boolean) => void;
}

export function FloatingChatbot({
  topic = 'process_analysis',
  sessionId = 'default',
  enableStreaming = true,
  simulationParams,
  position = 'bottom-right',
  theme: _theme = 'dark',
  accentColor = 'blue',
  minimizedText,
  placeholder,
  maxHeight = 500,
  width = 400,
  showSessionInfo = false,
  onToggle
}: FloatingChatbotProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  // topic에 따른 번역된 기본값 사용
  const chatbotMinimizedText = minimizedText || (topic === 'general' ? t('chatbot.minimizedTextGeneral') : t('chatbot.minimizedText'));
  const chatbotPlaceholder = placeholder || (topic === 'general' ? t('chatbot.placeholderGeneral') : t('chatbot.placeholder'));
  
  // 리사이즈 상태 관리
  const [currentWidth, setCurrentWidth] = useState(width);
  const [currentHeight, setCurrentHeight] = useState(maxHeight);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeDirection, setResizeDirection] = useState<'both' | 'width' | 'height'>('both');
  
  // 드래그 상태 관리
  const [isDragging, setIsDragging] = useState(false);
  const [position2D, setPosition2D] = useState({ x: 0, y: 0 });
  const [hasBeenMoved, setHasBeenMoved] = useState(false);
  
  // React 18의 useDeferredValue로 부드러운 상태 업데이트
  const deferredPosition = useDeferredValue(position2D);
  const deferredWidth = useDeferredValue(currentWidth);
  const deferredHeight = useDeferredValue(currentHeight);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatWidgetRef = useRef<HTMLDivElement>(null);

  // 단순화된 드래그/리사이즈 데이터 관리
  const dragDataRef = useRef({ x: 0, y: 0, initialX: 0, initialY: 0 });
  const resizeDataRef = useRef({ x: 0, y: 0, width: 0, height: 0 });

  // 최소/최대 크기 제한
  const MIN_WIDTH = 280;
  const MAX_WIDTH = 800;
  const MIN_HEIGHT = 300;
  const MAX_HEIGHT = 1000;

  const {
    messages,
    isLoading,
    isStreaming,
    error,
    sessionInfo,
    sendMessage,
    clearMessages,
    resetSession,
    chatbotClient
  } = useChatbot({
    topic,
    sessionId,
    enableStreaming,
    simulationParams
  });

  // 초기 위치 설정 (사용자가 이동하지 않은 경우에만)
  useEffect(() => {
    if (typeof window !== 'undefined' && !hasBeenMoved) {
      const setInitialPosition = () => {
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        const widgetWidth = currentWidth;
        const widgetHeight = currentHeight;
        
        let x = 0;
        let y = 0;
        
        switch (position) {
          case 'bottom-right':
            x = windowWidth - widgetWidth - 16;
            y = windowHeight - widgetHeight - 16;
            break;
          case 'bottom-left':
            x = 16;
            y = windowHeight - widgetHeight - 16;
            break;
          case 'top-right':
            x = windowWidth - widgetWidth - 16;
            y = 16;
            break;
          case 'top-left':
            x = 16;
            y = 16;
            break;
          default:
            x = windowWidth - widgetWidth - 16;
            y = windowHeight - widgetHeight - 16;
        }
        
        setPosition2D({ x, y });
      };
      
      setInitialPosition();
      window.addEventListener('resize', setInitialPosition);
      
      return () => {
        window.removeEventListener('resize', setInitialPosition);
      };
    }
  }, [position, hasBeenMoved, currentWidth, currentHeight]);

  // 메시지 스크롤 관리
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 텍스트 영역 자동 크기 조정
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputMessage]);

  // 최적화된 드래그 핸들러 (단순하고 안정적)
  const handleDragMove = useCallback((e: MouseEvent) => {
    if (!isDragging || isResizing || !chatWidgetRef.current) return;

    e.preventDefault();
    
    const deltaX = e.clientX - dragDataRef.current.x;
    const deltaY = e.clientY - dragDataRef.current.y;
    
    let newX = dragDataRef.current.initialX + deltaX;
    let newY = dragDataRef.current.initialY + deltaY;
    
    // 화면 경계 체크
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const margin = 20;
    
    newX = Math.max(margin, Math.min(windowWidth - currentWidth - margin, newX));
    newY = Math.max(margin, Math.min(windowHeight - currentHeight - margin, newY));
    
    // 단순한 직접 DOM 조작 (가장 안정적)
    chatWidgetRef.current.style.left = `${newX}px`;
    chatWidgetRef.current.style.top = `${newY}px`;
  }, [isDragging, isResizing, currentWidth, currentHeight]);

  // 최적화된 리사이즈 핸들러
  const handleResizeMove = useCallback((e: MouseEvent) => {
    if (!isResizing || !chatWidgetRef.current) return;

    e.preventDefault();
    
    const deltaX = e.clientX - resizeDataRef.current.x;
    const deltaY = e.clientY - resizeDataRef.current.y;
    
    let newWidth = resizeDataRef.current.width + deltaX;
    let newHeight = resizeDataRef.current.height + deltaY;
    
    // 리사이즈 방향에 따라 처리
    if (resizeDirection === 'both' || resizeDirection === 'width') {
      newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
      chatWidgetRef.current.style.width = `${newWidth}px`;
    }
    
    if (resizeDirection === 'both' || resizeDirection === 'height') {
      newHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, newHeight));
      chatWidgetRef.current.style.height = `${newHeight}px`;
    }
  }, [isResizing, resizeDirection]);

  // 마우스 업 핸들러 (단순화)
  const handleMouseUp = useCallback((e: MouseEvent) => {
    e.preventDefault();
    
    if (isDragging && chatWidgetRef.current) {
      const rect = chatWidgetRef.current.getBoundingClientRect();
      setPosition2D({ x: rect.left, y: rect.top });
      setHasBeenMoved(true);
      setIsDragging(false);
    }
    
    if (isResizing && chatWidgetRef.current) {
      const rect = chatWidgetRef.current.getBoundingClientRect();
      setCurrentWidth(Math.round(rect.width));
      setCurrentHeight(Math.round(rect.height));
      setIsResizing(false);
      setResizeDirection('both');
    }
    
    document.body.style.userSelect = '';
    document.body.style.cursor = '';
  }, [isDragging, isResizing]);

  // 이벤트 리스너 관리
  useEffect(() => {
    if (isDragging || isResizing) {
      document.body.style.userSelect = 'none';
      
      if (isDragging) {
        document.body.style.cursor = 'move';
        document.addEventListener('mousemove', handleDragMove);
      } else if (isResizing) {
        const cursor = resizeDirection === 'width' ? 'ew-resize' : 
                      resizeDirection === 'height' ? 'ns-resize' : 
                      'se-resize';
        document.body.style.cursor = cursor;
        document.addEventListener('mousemove', handleResizeMove);
      }
      
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleDragMove);
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isDragging, isResizing, handleDragMove, handleResizeMove, handleMouseUp, resizeDirection]);

  // UI 이벤트 핸들러
  const handleToggle = () => {
    const newIsOpen = !isOpen;
    setIsOpen(newIsOpen);
    onToggle?.(newIsOpen);
  };

  const handleMinimize = () => {
    setIsOpen(false);
    onToggle?.(false);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || isStreaming) return;

    const message = inputMessage.trim();
    setInputMessage('');
    
    await sendMessage(message);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleResizeMouseDown = useCallback((e: React.MouseEvent, direction: 'both' | 'width' | 'height' = 'both') => {
    e.preventDefault();
    e.stopPropagation();
    
    setIsResizing(true);
    setResizeDirection(direction);
    resizeDataRef.current = {
      x: e.clientX,
      y: e.clientY,
      width: currentWidth,
      height: currentHeight
    };
  }, [currentWidth, currentHeight]);

  const handleDragMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    let currentX = position2D.x;
    let currentY = position2D.y;
    
    if (position2D.x === 0 && position2D.y === 0) {
      const rect = chatWidgetRef.current?.getBoundingClientRect();
      if (rect) {
        currentX = rect.left;
        currentY = rect.top;
        setPosition2D({ x: currentX, y: currentY });
      }
    }
    
    setIsDragging(true);
    dragDataRef.current = {
      x: e.clientX,
      y: e.clientY,
      initialX: currentX,
      initialY: currentY
    };
  }, [position2D]);

  // 스타일링 함수들
  const getThemeClasses = () => {
    return 'bg-card text-card-foreground border-border';
  };

  const getAccentClasses = () => {
    const colors = {
      blue: 'bg-accent-blue hover:bg-accent-cyan text-white',
      green: 'bg-accent-cyan hover:bg-accent-blue text-white',
      purple: 'bg-accent-purple hover:bg-accent-blue text-white',
      red: 'bg-accent-pink hover:bg-accent-orange text-white',
      gray: 'bg-muted hover:bg-muted-foreground text-foreground'
    };
    return colors[accentColor as keyof typeof colors] || colors.blue;
  };

  // 플로팅 버튼 위치
  const getFloatingButtonPosition = () => {
    switch (position) {
      case 'bottom-right': return { right: '16px', bottom: '16px' };
      case 'bottom-left': return { left: '16px', bottom: '16px' };
      case 'top-right': return { right: '16px', top: '16px' };
      case 'top-left': return { left: '16px', top: '16px' };
      default: return { right: '16px', bottom: '16px' };
    }
  };

  // 위젯 위치 가져오기 (deferred 값 사용)
  const getWidgetPosition = () => {
    if (deferredPosition.x === 0 && deferredPosition.y === 0) {
      switch (position) {
        case 'bottom-right': return { right: '16px', bottom: '16px' };
        case 'bottom-left': return { left: '16px', bottom: '16px' };
        case 'top-right': return { right: '16px', top: '16px' };
        case 'top-left': return { left: '16px', top: '16px' };
        default: return { right: '16px', bottom: '16px' };
      }
    }
    
    return {
      left: `${deferredPosition.x}px`,
      top: `${deferredPosition.y}px`
    };
  };

  return (
    <div className="fixed z-[9999] font-paperlogy">
      {/* 플로팅 버튼 */}
      {!isOpen && (
        <button
          onClick={handleToggle}
          className={`group relative px-4 py-3 rounded-full shadow-lg ${getAccentClasses()} transition-all duration-200 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center space-x-2 font-paperlogy`}
          style={{
            ...getFloatingButtonPosition(),
            zIndex: 9999,
            position: 'fixed'
          }}
        >
          <MessageCircle className="w-5 h-5 text-white" />
          <span className="text-sm font-medium whitespace-nowrap text-white">{chatbotMinimizedText}</span>
          
          {/* 대화 턴 수 표시 */}
          {messages.length > 0 && (
            <div className="absolute -top-2 -right-2 w-5 h-5 bg-accent-pink text-white text-xs rounded-full flex items-center justify-center">
              {Math.ceil(messages.length / 2) > 9 ? '9+' : Math.ceil(messages.length / 2)}
            </div>
          )}
        </button>
      )}

      {/* 챗봇 위젯 */}
      {isOpen && (
        <div 
          ref={chatWidgetRef}
          className={`${getThemeClasses()} border rounded-lg shadow-xl overflow-hidden relative ${
            isResizing ? 'select-none' : ''
          } ${isDragging ? 'cursor-move' : ''}`}
          style={{ 
            width: `${deferredWidth}px`,
            height: `${deferredHeight}px`,
            ...getWidgetPosition(),
            zIndex: 9999,
            position: 'fixed',
            // CSS Containment로 레이아웃 최적화
            contain: 'layout style paint',
            // 부드러운 전환을 위한 CSS
            transition: isDragging || isResizing ? 'none' : 'all 0.2s ease-out'
          }}
        >
          {/* 헤더 */}
          <div 
            className={`flex items-center justify-between p-3 border-b border-border bg-muted ${isDragging ? 'cursor-move' : 'cursor-grab'} select-none hover:bg-opacity-80 transition-colors`}
            onMouseDown={handleDragMouseDown}
            title={t('chatbot.actions.drag')}
          >
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-accent-cyan rounded-full"></div>
              <h3 className="font-medium text-sm font-paperlogy text-card-foreground">
                {topic === 'general' ? t('chatbot.titleGeneral') : 
                 topic === 'process_analysis' ? t('chatbot.titleWithTopic') : 
                 t('chatbot.title')}
              </h3>
              <Move className={`w-3 h-3 ${isDragging ? 'text-card-foreground' : 'text-muted-foreground'} transition-colors`} />
            </div>
            
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="p-1 rounded hover:bg-glass-200 transition-colors font-paperlogy"
                title={t('chatbot.actions.settings')}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <Settings className="w-3 h-3 text-muted-foreground hover:text-card-foreground transition-colors" />
              </button>
              
              <button
                onClick={handleMinimize}
                className="p-1 rounded hover:bg-glass-200 transition-colors font-paperlogy"
                title={t('chatbot.actions.minimize')}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <Minus className="w-3 h-3 text-muted-foreground hover:text-card-foreground transition-colors" />
              </button>
              
              <button
                onClick={resetSession}
                className="p-1 rounded hover:bg-glass-200 transition-colors font-paperlogy"
                title={t('chatbot.actions.reset')}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <RefreshCw className="w-3 h-3 text-muted-foreground hover:text-card-foreground transition-colors" />
              </button>
              
              <button
                onClick={handleToggle}
                className="p-1 rounded hover:bg-glass-200 transition-colors font-paperlogy"
                title={t('chatbot.actions.close')}
                onMouseDown={(e) => e.stopPropagation()}
              >
                <X className="w-3 h-3 text-muted-foreground hover:text-card-foreground transition-colors" />
              </button>
            </div>
          </div>

          {/* 메시지 목록 */}
          <div 
            className="overflow-y-auto p-3 space-y-3"
            style={{ 
              height: `${deferredHeight - 160}px`
            }}
          >
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground py-6">
                <div className="w-12 h-12 mx-auto mb-3 bg-muted rounded-full flex items-center justify-center">
                  <Bot className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium">{t('chatbot.greeting.hello')}</p>
                <p className="text-xs mt-1">
                  {topic === 'general' ? t('chatbot.greeting.descriptionGeneral') : t('chatbot.greeting.description')}
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                      message.role === 'user'
                        ? `${getAccentClasses()}`
                        : 'bg-muted text-foreground'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.role === 'assistant' && (
                        <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      {message.role === 'user' && (
                        <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        {message.role === 'user' ? (
                          <p className="whitespace-pre-wrap font-paperlogy">{message.content}</p>
                        ) : (
                          <MarkdownRenderer 
                            content={message.content}
                            className="prose prose-sm max-w-none font-paperlogy"
                          />
                        )}
                      </div>
                    </div>
                    
                    <div className={`text-xs mt-1 opacity-70 ${
                      message.role === 'user' ? 'text-white' : 'text-muted-foreground'
                    }`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                      {isStreaming && index === messages.length - 1 && message.role === 'assistant' && (
                        <span className="ml-2 animate-pulse">●</span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {/* 에러 표시 */}
            {error && (
              <div className="flex justify-center">
                <div className="bg-accent-pink/10 border border-accent-pink text-accent-pink px-3 py-2 rounded-lg text-sm flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span>{error}</span>
                </div>
              </div>
            )}
            
            {/* 로딩 표시 */}
            {(isLoading || isStreaming) && (
              <div className="flex justify-start">
                <div className="px-3 py-2 rounded-lg bg-muted flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {isStreaming ? t('chatbot.status.generating') : t('chatbot.status.processing')}
                  </span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* 입력 영역 */}
          <div className="border-t border-border p-3">
            <div className="flex space-x-2">
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={chatbotPlaceholder}
                className="flex-1 resize-none border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent min-h-[36px] max-h-[100px] font-paperlogy bg-input text-foreground placeholder-muted-foreground"
                disabled={isLoading || isStreaming}
                rows={1}
              />
              
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading || isStreaming}
                className={`p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-paperlogy ${getAccentClasses()}`}
              >
                {isLoading || isStreaming ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            
            {/* 액션 버튼들 */}
            <div className="flex justify-between items-center mt-2">
              <div className="flex space-x-2">
                <button
                  onClick={clearMessages}
                  className="text-xs px-2 py-1 rounded transition-colors text-muted-foreground hover:text-card-foreground hover:bg-glass-200"
                >
                  {t('chatbot.actions.clear')}
                </button>
                {showSessionInfo && sessionInfo && (
                  <span className="text-xs text-muted-foreground">
                    턴: {sessionInfo.turn_count}
                  </span>
                )}
              </div>
              
              <div className="text-xs text-muted-foreground">
                {t('chatbot.status.sendWithEnter')}
              </div>
            </div>
          </div>

          {/* 리사이즈 핸들 */}
          <div
            className={`absolute bottom-0 right-0 w-4 h-4 cursor-se-resize z-20 ${
              isResizing 
                ? 'opacity-100' 
                : 'opacity-60 hover:opacity-100'
            } transition-all duration-200 flex items-center justify-center`}
            onMouseDown={(e) => handleResizeMouseDown(e, 'both')}
            title={t('chatbot.resize.diagonal')}
          >
            <div className="w-full h-full relative overflow-hidden">
              <div className="absolute inset-0 text-muted-foreground">
                <svg 
                  className="w-full h-full"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                >
                  <path d="M16 16H14L16 14V16Z"/>
                  <path d="M16 12H10L16 6V8L14 10L16 12Z"/>
                  <path d="M16 8H6L16 0V2L12 6L16 8Z"/>
                </svg>
              </div>
            </div>
          </div>

          {/* 추가 리사이즈 영역 */}
          <div
            className="absolute top-0 right-0 w-2 cursor-ew-resize z-10 hover:bg-accent-blue hover:bg-opacity-20 transition-colors"
            style={{ height: `calc(100% - 16px)` }}
            onMouseDown={(e) => handleResizeMouseDown(e, 'width')}
            title={t('chatbot.resize.horizontal')}
          />

          <div
            className="absolute bottom-0 left-0 h-2 cursor-ns-resize z-10 hover:bg-accent-blue hover:bg-opacity-20 transition-colors"
            style={{ width: `calc(100% - 16px)` }}
            onMouseDown={(e) => handleResizeMouseDown(e, 'height')}
            title={t('chatbot.resize.vertical')}
          />
        </div>
      )}
      
      {/* 설정 모달 */}
      <ChatbotSettings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        chatbotClient={chatbotClient}
      />
    </div>
  );
} 