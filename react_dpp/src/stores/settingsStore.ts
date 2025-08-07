import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ColorSetting {
  id: string;
  name: string;
  label: string;
  color: string;
  description: string;
}

export interface LabelSetting {
  id: string;
  name: string;
  label: string;
  value: string;
  description: string;
}

interface SettingsState {
  colorSettings: ColorSetting[];
  labelSettings: LabelSetting[];
  
  // Actions
  updateColorSetting: (id: string, color: string) => void;
  updateLabelSetting: (id: string, value: string) => void;
  resetToDefaults: () => void;
  
  // Getters
  getColorByName: (name: string) => string;
  getLabelByName: (name: string) => string;
}

const defaultColorSettings: ColorSetting[] = [
  {
    id: 'no1-process',
    name: 'no1ProcessColor',
    label: 'No.1 공정라인',
    color: '#EF4444',
    description: 'No.1 공정라인 스케줄 바 색상'
  },
  {
    id: 'no2-process',
    name: 'no2ProcessColor',
    label: 'No.2 공정라인',
    color: '#10B981',
    description: 'No.2 공정라인 스케줄 바 색상'
  },
  {
    id: 'weekend-bg',
    name: 'weekendBackground',
    label: '주말 배경',
    color: '#E5E7EB',
    description: '토요일/일요일 배경 색상'
  },
  {
    id: 'idle-bg',
    name: 'idleBackground',
    label: '비가동 배경',
    color: '#FEF3C7',
    description: '비가동 시간 배경 색상'
  },
  {
    id: 'header-bg',
    name: 'headerBackground',
    label: '헤더 배경',
    color: '#3B82F6',
    description: '테이블 헤더 배경 색상'
  }
];

const defaultLabelSettings: LabelSetting[] = [
  {
    id: 'no1-label',
    name: 'no1Label',
    label: 'No.1 라벨',
    value: 'No.1',
    description: 'No.1 공정라인 표시 라벨'
  },
  {
    id: 'no2-label',
    name: 'no2Label',
    label: 'No.2 라벨',
    value: 'No.2',
    description: 'No.2 공정라인 표시 라벨'
  },
  {
    id: 'detail-label',
    name: 'detailLabel',
    label: '상세 라벨',
    value: '상세',
    description: '상세 정보 섹션 라벨'
  },
  {
    id: 'rolling-label',
    name: 'rollingLabel',
    label: '압연일정 라벨',
    value: '압연일정',
    description: '압연일정 섹션 라벨'
  },
  {
    id: 'uncorrected-label',
    name: 'uncorrectedLabel',
    label: '미교정 라벨',
    value: '미교정',
    description: '미교정 섹션 라벨'
  },
  {
    id: 'transfer-label',
    name: 'transferLabel',
    label: '당진이관재 라벨',
    value: '당진이관재',
    description: '당진이관재 섹션 라벨'
  },
  {
    id: 'billet-label',
    name: 'billetLabel',
    label: '빌렛 라벨',
    value: '빌렛',
    description: '빌렛 섹션 라벨'
  }
];

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      colorSettings: defaultColorSettings,
      labelSettings: defaultLabelSettings,

      updateColorSetting: (id: string, color: string) => {
        set((state) => ({
          colorSettings: state.colorSettings.map((setting) =>
            setting.id === id ? { ...setting, color } : setting
          ),
        }));
      },

      updateLabelSetting: (id: string, value: string) => {
        set((state) => ({
          labelSettings: state.labelSettings.map((setting) =>
            setting.id === id ? { ...setting, value } : setting
          ),
        }));
      },

      resetToDefaults: () => {
        set({
          colorSettings: [...defaultColorSettings],
          labelSettings: [...defaultLabelSettings],
        });
      },

      getColorByName: (name: string) => {
        const setting = get().colorSettings.find((s) => s.name === name);
        return setting?.color || '#000000';
      },

      getLabelByName: (name: string) => {
        const setting = get().labelSettings.find((s) => s.name === name);
        return setting?.value || '';
      },
    }),
    {
      name: 'dpp-settings-storage',
      version: 1,
    }
  )
); 