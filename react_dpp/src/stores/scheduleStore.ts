import { create } from 'zustand';
import { ScheduleItem, YardNote, ScheduleDateCell, ProcessInfo } from '@/types/schedule';

interface ScheduleStore {
  // State
  currentStartDate: string;
  scheduleData: ScheduleDateCell[];
  yardNotes: YardNote[];
  processes: ProcessInfo[];
  selectedItem: ScheduleItem | null;
  isLoading: boolean;
  
  // 새로운 스케일 관련 상태
  viewMode: 'week' | '2weeks' | '3weeks' | '4weeks';
  cellWidth: number;
  
  // Actions
  setCurrentStartDate: (date: string) => void;
  setScheduleData: (data: ScheduleDateCell[]) => void;
  addScheduleItem: (item: ScheduleItem) => void;
  updateScheduleItem: (id: string, updates: Partial<ScheduleItem>) => void;
  deleteScheduleItem: (id: string) => void;
  setSelectedItem: (item: ScheduleItem | null) => void;
  
  // 스케일 조정 액션
  setViewMode: (mode: 'week' | '2weeks' | '3weeks' | '4weeks') => void;
  setCellWidth: (width: number) => void;
  
  // Yard Notes
  addYardNote: (note: YardNote) => void;
  updateYardNote: (id: string, content: string) => void;
  deleteYardNote: (id: string) => void;
  
  // Utility
  setLoading: (loading: boolean) => void;
  moveToNextPeriod: () => void;
  moveToPrevPeriod: () => void;
}

export const useScheduleStore = create<ScheduleStore>((set) => ({
  // Initial state
  currentStartDate: '2025-05-21',
  scheduleData: [],
  yardNotes: [],
  processes: [
    { id: '1', name: 'No.1', color: '#EF4444' }, 
    { id: '2', name: 'No.2', color: '#EF4444' },
  ],
  selectedItem: null,
  isLoading: false,
  
  // 새로운 스케일 관련 초기값
  viewMode: 'week',
  cellWidth: 40,
  
  // Actions
  setCurrentStartDate: (date) => set({ currentStartDate: date }),
  
  setScheduleData: (data) => set({ scheduleData: data }),
  
  addScheduleItem: (item) => set((state) => {
    const newData = [...state.scheduleData];
    const dateIndex = newData.findIndex(d => d.date === item.startTime.split('T')[0]);
    if (dateIndex >= 0) {
      newData[dateIndex].items.push(item);
    }
    return { scheduleData: newData };
  }),
  
  updateScheduleItem: (id, updates) => set((state) => {
    const newData = state.scheduleData.map(dateCell => ({
      ...dateCell,
      items: dateCell.items.map(item => 
        item.id === id ? { ...item, ...updates } : item
      )
    }));
    return { scheduleData: newData };
  }),
  
  deleteScheduleItem: (id) => set((state) => {
    const newData = state.scheduleData.map(dateCell => ({
      ...dateCell,
      items: dateCell.items.filter(item => item.id !== id)
    }));
    return { scheduleData: newData };
  }),
  
  setSelectedItem: (item) => set({ selectedItem: item }),
  
  // 스케일 조정 액션
  setViewMode: (mode) => {
    const cellWidths = {
      'week': 40,      // 1주일: 7일 * 12시간 * 40px = 3360px 정도로 줄임
      '2weeks': 35,    // 2주일: 좀 더 작게
      '3weeks': 30,    // 3주일: 더 작게  
      '4weeks': 25     // 4주일: 가장 작게
    };
    set({ 
      viewMode: mode, 
      cellWidth: cellWidths[mode] 
    });
  },
  
  setCellWidth: (width) => set({ cellWidth: width }),
  
  // Yard Notes
  addYardNote: (note) => set((state) => ({
    yardNotes: [...state.yardNotes, note]
  })),
  
  updateYardNote: (id, content) => set((state) => ({
    yardNotes: state.yardNotes.map(note => 
      note.id === id ? { ...note, content, updatedAt: new Date().toISOString() } : note
    )
  })),
  
  deleteYardNote: (id) => set((state) => ({
    yardNotes: state.yardNotes.filter(note => note.id !== id)
  })),
  
  // Utility
  setLoading: (loading) => set({ isLoading: loading }),
  
  moveToNextPeriod: () => set((state) => {
    const weekMultiplier = {
      'week': 1,
      '2weeks': 2,
      '3weeks': 3,
      '4weeks': 4
    }[state.viewMode];
    
    const currentDate = new Date(state.currentStartDate);
    currentDate.setDate(currentDate.getDate() + (7 * weekMultiplier));
    return { currentStartDate: currentDate.toISOString().split('T')[0] };
  }),
  
  moveToPrevPeriod: () => set((state) => {
    const weekMultiplier = {
      'week': 1,
      '2weeks': 2,
      '3weeks': 3,
      '4weeks': 4
    }[state.viewMode];
    
    const currentDate = new Date(state.currentStartDate);
    currentDate.setDate(currentDate.getDate() - (7 * weekMultiplier));
    return { currentStartDate: currentDate.toISOString().split('T')[0] };
  }),
})); 