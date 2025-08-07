export interface ScheduleItem {
  id: string;
  processNo: string;           // e.g., "5A-15"
  startTime: string;           // ISO DateTime
  durationHours: number;       // 생산시간 (시간 단위)
  quantityTon: number;         // 생산량
  description?: string;        // SIZE·톤수 등
  processLine?: string;        // 공정라인 (No.1, No.2)
}

export interface YardNote {
  id: string;
  content: string;
  updatedAt: string;
}

export interface ScheduleDateCell {
  date: string;                // YYYY-MM-DD
  isNonWorking: boolean;       // 비조업 여부
  isIdle: boolean;             // 비가동 여부
  items: ScheduleItem[];
}

export interface ProcessInfo {
  id: string;
  name: string;                // e.g., "No.1", "No.2", "5A-15"
  color: string;               // 막대 색상
}

export interface ScheduleGridProps {
  startDate: string;           // YYYY-MM-DD
  endDate: string;             // YYYY-MM-DD
  processes: ProcessInfo[];
  data: ScheduleDateCell[];
} 