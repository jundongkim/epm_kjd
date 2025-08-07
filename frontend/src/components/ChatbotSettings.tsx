'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChatConfig, ChatbotClient } from '@/lib/chatbot-client';
import { useTranslation } from '@/hooks/useTranslation';
import { Settings, X, Bot, Sliders, Zap, RotateCcw } from 'lucide-react';
import { NumberInput, Select } from '@/components/ui';

interface ChatbotSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  chatbotClient: ChatbotClient;
}

export default function ChatbotSettings({ isOpen, onClose, chatbotClient }: ChatbotSettingsProps) {
  const { t } = useTranslation();
  const [config, setConfig] = useState<ChatConfig>({
    current_model: 'gemma3:4b-it-qat',
    temperature: 0.7,
    max_tokens: 2048,
    max_turn_count: 10,
    ollama_base_url: 'http://localhost:11434',
    enable_streaming: true,
  });

  const [originalConfig, setOriginalConfig] = useState<ChatConfig>({
    current_model: 'gemma3:4b-it-qat',
    temperature: 0.7,
    max_tokens: 2048,
    max_turn_count: 10,
    ollama_base_url: 'http://localhost:11434',
    enable_streaming: true,
  });

  const [isLoading, setIsLoading] = useState(false);

  // 설정 로드 - 무한 루프 방지를 위해 useEffect 내부에서 직접 정의
  useEffect(() => {
    if (!isOpen) return;
    
    const loadConfig = async () => {
      try {
        setIsLoading(true);
        const currentConfig = await chatbotClient.getConfig();
        setConfig(currentConfig);
        setOriginalConfig(currentConfig);
      } catch (error) {
        console.error('설정 로드 실패:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadConfig();
  }, [isOpen, chatbotClient]);

  const handleSave = async () => {
    try {
      setIsLoading(true);
      // ChatConfig를 ChatConfigRequest 형태로 변환
      const updateRequest = {
        model: config.current_model,  // current_model -> model 필드명 변경
        temperature: config.temperature,
        max_tokens: config.max_tokens,
        max_turn_count: config.max_turn_count,
        enable_streaming: config.enable_streaming
      };
      
      const updatedConfig = await chatbotClient.updateConfig(updateRequest);
      setConfig(updatedConfig);
      setOriginalConfig(updatedConfig);
      onClose();
    } catch (error) {
      console.error('설정 저장 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setConfig(originalConfig);
    onClose();
  };

  const handleReset = () => {
    const defaultConfig: ChatConfig = {
      current_model: 'gemma3:4b-it-qat',
      temperature: 0.7,
      max_tokens: 2048,
      max_turn_count: 10,
      ollama_base_url: 'http://localhost:11434',
      enable_streaming: true,
    };
    setConfig(defaultConfig);
  };

  const modelOptions = [
    'gemma3:1b-it-qat',
    'gemma3:4b-it-qat',
    'gemma3:12b-it-qat',
    'gemma3:27b-it-qat'
  ];

  const getModelDisplayName = (model: string) => {
    const displayNames: Record<string, string> = {
      'gemma3:1b-it-qat': 'Gemma3 1B-It-Qat - 경량 모델',
      'gemma3:4b-it-qat': 'Gemma3 4B-It-Qat - 표준 모델',
      'gemma3:12b-it-qat': 'Gemma3 12B-It-Qat - 고성능 모델',
      'gemma3:27b-it-qat': 'Gemma3 27B-It-Qat - 최고성능 모델'
    };
    return displayNames[model] || model;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
      <div 
        className="bg-card backdrop-blur-glass-xl border border-border rounded-glass-lg shadow-glass-lg max-w-lg w-full max-h-[90vh] overflow-y-auto"
        style={{
          backgroundColor: 'var(--card)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--border)',
        }}
      >
        {/* 헤더 */}
        <div className="flex justify-between items-center p-6 border-b border-border">
          <div className="flex items-center">
            <Bot className="w-5 h-5 mr-3 text-card-foreground" />
            <h2 className="text-xl font-semibold text-card-foreground">{t('chatbot.settings.title')}</h2>
          </div>
          <button
            onClick={handleCancel}
            className="text-muted-foreground hover:text-card-foreground transition-colors p-1 rounded-glass hover:bg-glass-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 설정 내용 */}
        <div className="p-6 space-y-4">
          {/* LLM 모델 선택 */}
          <div>
            <div className="flex items-center mb-2">
              <Settings className="w-4 h-4 mr-2 text-card-foreground" />
              <label className="block text-sm font-medium text-card-foreground">
                {t('chatbot.settings.model')}
              </label>
            </div>
            <Select
              value={getModelDisplayName(config.current_model)}
              onChange={(selectedDisplay) => {
                // 선택된 표시 이름으로부터 실제 모델 값 찾기
                const selectedModel = modelOptions.find(model => 
                  getModelDisplayName(model) === selectedDisplay
                ) || config.current_model;
                setConfig(prev => ({ ...prev, current_model: selectedModel }));
              }}
              options={modelOptions.map(model => getModelDisplayName(model))}
              label=""
              placeholder="모델을 선택하세요"
            />
          </div>

          {/* Temperature 슬라이더 */}
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-2 flex items-center">
              <Sliders className="w-4 h-4 mr-2" />
              {t('chatbot.settings.temperature')}: <span className="text-primary font-semibold ml-2">{config.temperature.toFixed(1)}</span>
            </label>
            <div className="flex items-center space-x-3">
              <span className="text-xs text-muted-foreground">0.0</span>
              <input
                type="range"
                min="0.0"
                max="2.0"
                step="0.1"
                value={config.temperature}
                onChange={(e) => setConfig(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                className="flex-1 h-2 bg-glass-300 rounded-full appearance-none cursor-pointer slider-thumb"
                style={{
                  background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${(config.temperature / 2) * 100}%, var(--glass-300) ${(config.temperature / 2) * 100}%, var(--glass-300) 100%)`
                }}
              />
              <span className="text-xs text-muted-foreground">2.0</span>
            </div>
          </div>

          {/* 최대 토큰 수 */}
          <div>
            <NumberInput
              value={config.max_tokens}
              onChange={(value) => setConfig(prev => ({ ...prev, max_tokens: value }))}
              min={512}
              max={4096}
              step={256}
              label={t('chatbot.settings.maxTokens')}
              unit="tokens"
            />
          </div>

          {/* 최대 대화 턴 수 */}
          <div>
            <NumberInput
              value={config.max_turn_count}
              onChange={(value) => setConfig(prev => ({ ...prev, max_turn_count: value }))}
              min={1}
              max={50}
              step={1}
              label={t('chatbot.settings.maxTurns')}
              unit="턴"
            />
          </div>

          {/* 스트리밍 활성화 */}
          <div className="flex items-center justify-between p-3 bg-glass-300 rounded-glass border border-border">
            <div className="flex items-center">
              <Zap className="w-4 h-4 mr-3 text-card-foreground" />
              <label className="block text-sm font-medium text-card-foreground">
                {t('chatbot.settings.streaming')}
              </label>
            </div>
            <button
              onClick={() => setConfig(prev => ({ ...prev, enable_streaming: !prev.enable_streaming }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                config.enable_streaming ? 'bg-primary' : 'bg-glass-300 border border-border'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  config.enable_streaming ? 'translate-x-6 shadow-glow' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* 버튼들 */}
        <div className="flex justify-end space-x-3 p-4 border-t border-border">
          <button
            onClick={handleReset}
            disabled={isLoading}
            className="flex items-center px-4 py-2.5 text-muted-foreground hover:text-card-foreground hover:bg-glass-300 transition-all disabled:opacity-50 border border-border rounded-glass"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            {t('chatbot.settings.reset')}
          </button>
          <button
            onClick={handleCancel}
            disabled={isLoading}
            className="px-4 py-2.5 text-muted-foreground hover:text-card-foreground hover:bg-glass-300 transition-all disabled:opacity-50 border border-border rounded-glass"
          >
            {t('chatbot.settings.cancel')}
          </button>
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="px-4 py-2.5 bg-gradient-primary text-white rounded-glass hover:opacity-90 transition-all disabled:opacity-50 shadow-glow"
          >
            {isLoading ? t('chatbot.settings.saving') : t('chatbot.settings.save')}
          </button>
        </div>
      </div>
    </div>
  );
} 