'use client';

import { useState } from 'react';
import { 
  PaintBrushIcon, 
  TagIcon, 
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { useSettingsStore } from '@/stores/settingsStore';

interface ColorSetting {
  id: string;
  name: string;
  label: string;
  color: string;
  description: string;
}

interface LabelSetting {
  id: string;
  name: string;
  label: string;
  value: string;
  description: string;
}

export const SettingsPage = () => {
  const [activeTab, setActiveTab] = useState<'colors' | 'labels'>('colors');
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const {
    colorSettings,
    labelSettings,
    updateColorSetting,
    updateLabelSetting,
    resetToDefaults,
    getColorByName,
    getLabelByName
  } = useSettingsStore();

  const handleColorChange = (id: string, newColor: string) => {
    updateColorSetting(id, newColor);
  };

  const handleLabelChange = (id: string, newValue: string) => {
    updateLabelSetting(id, newValue);
  };

  const handleSave = async () => {
    setIsSaving(true);
    
    try {
      // 설정은 이미 store에 저장되어 있으므로 여기서는 UI 피드백만 제공
      await new Promise(resolve => setTimeout(resolve, 1000));
      setLastSaved(new Date());
    } catch (error) {
      console.error('설정 저장 오류:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('모든 설정을 기본값으로 초기화하시겠습니까?')) {
      resetToDefaults();
      setLastSaved(new Date());
    }
  };

  const tabs = [
    { id: 'colors', label: '색상 설정', icon: PaintBrushIcon },
    { id: 'labels', label: '라벨 설정', icon: TagIcon }
  ];

  return (
    <div className="pt-8">
      {/* 헤더 */}
      <div className="mb-8 px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">설정</h1>
        <p className="text-lg text-gray-600">
          공정표 색상 및 라벨을 사용자 정의하세요
        </p>
      </div>

      {/* 저장 상태 */}
      <div className="mb-6 flex items-center justify-between px-8">
        <div className="flex items-center space-x-4">
          {isSaving && (
            <div className="flex items-center text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm">저장 중...</span>
            </div>
          )}
          {lastSaved && !isSaving && (
            <div className="flex items-center text-green-600">
              <CheckIcon className="w-4 h-4 mr-2" />
              <span className="text-sm">저장됨 ({lastSaved.toLocaleTimeString()})</span>
            </div>
          )}
          <div className="text-sm text-gray-500">
            ※ 변경사항은 자동으로 저장되며 공정표에 즉시 반영됩니다
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            초기화
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? '저장 중...' : '설정 확인'}
          </button>
        </div>
      </div>

      {/* 탭 메뉴 */}
      <div className="border-b border-gray-200 mb-6 px-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'colors' | 'labels')}
                className={`
                  flex items-center py-2 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-5 h-5 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* 색상 설정 탭 */}
      {activeTab === 'colors' && (
        <div className="space-y-6 px-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">색상 설정</h2>
              <div className="space-y-4">
                {colorSettings.map((setting) => (
                  <div key={setting.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{setting.label}</h3>
                      <p className="text-sm text-gray-600">{setting.description}</p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-10 h-10 rounded-lg border border-gray-300"
                        style={{ backgroundColor: setting.color }}
                      ></div>
                      <input
                        type="color"
                        value={setting.color}
                        onChange={(e) => handleColorChange(setting.id, e.target.value)}
                        className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={setting.color}
                        onChange={(e) => handleColorChange(setting.id, e.target.value)}
                        className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 라벨 설정 탭 */}
      {activeTab === 'labels' && (
        <div className="space-y-6 px-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">라벨 설정</h2>
              <div className="space-y-4">
                {labelSettings.map((setting) => (
                  <div key={setting.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{setting.label}</h3>
                      <p className="text-sm text-gray-600">{setting.description}</p>
                    </div>
                    <div className="w-48">
                      <input
                        type="text"
                        value={setting.value}
                        onChange={(e) => handleLabelChange(setting.id, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={`${setting.label} 입력`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 실시간 미리보기 */}
      <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 mx-8">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">실시간 미리보기</h2>
          <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
            <div className="text-sm text-gray-600 mb-4">현재 설정된 색상과 라벨이 실시간으로 반영됩니다.</div>
            
            {/* 공정라인 미리보기 */}
            <div className="space-y-4">
              <div className="flex space-x-4">
                <div 
                  className="px-4 py-2 rounded text-white text-sm font-medium"
                  style={{ backgroundColor: getColorByName('no1ProcessColor') }}
                >
                  {getLabelByName('no1Label')} 공정라인
                </div>
                <div 
                  className="px-4 py-2 rounded text-white text-sm font-medium"
                  style={{ backgroundColor: getColorByName('no2ProcessColor') }}
                >
                  {getLabelByName('no2Label')} 공정라인
                </div>
              </div>
              
              {/* 배경색 미리보기 */}
              <div className="grid grid-cols-2 gap-4">
                <div 
                  className="p-3 rounded border text-sm"
                  style={{ backgroundColor: getColorByName('weekendBackground') }}
                >
                  주말 배경색
                </div>
                <div 
                  className="p-3 rounded border text-sm"
                  style={{ backgroundColor: getColorByName('idleBackground') }}
                >
                  비가동 배경색
                </div>
              </div>
              
              {/* 라벨 미리보기 */}
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="p-2 bg-blue-50 rounded border">
                  <strong>{getLabelByName('detailLabel')}</strong> 섹션
                </div>
                <div className="p-2 bg-blue-50 rounded border">
                  <strong>{getLabelByName('rollingLabel')}</strong> 섹션
                </div>
                <div className="p-2 bg-blue-50 rounded border">
                  <strong>{getLabelByName('uncorrectedLabel')}</strong> 섹션
                </div>
                <div className="p-2 bg-blue-50 rounded border">
                  <strong>{getLabelByName('transferLabel')}</strong> 섹션
                </div>
                <div className="p-2 bg-blue-50 rounded border">
                  <strong>{getLabelByName('billetLabel')}</strong> 섹션
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 