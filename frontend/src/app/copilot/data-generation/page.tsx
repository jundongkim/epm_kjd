'use client'

import { useState, useEffect } from 'react'
import { 
  Database, Factory, FlaskConical, DollarSign, 
  Settings, Download, Play, AlertCircle, CheckCircle,
  Calendar, Clock, Sliders, TrendingUp, Zap, Beaker,
  ChevronDown, ChevronUp, X, Info, RefreshCw, Activity
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { Slider, RangeSlider, Select, MultiSelect, NumberInput, Checkbox, TabNavigation } from '@/components/ui'
import MarkdownRenderer from '@/components/MarkdownRenderer'

// ============================
// API 호출 함수들
// ============================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 데이터 생성 API 호출
const generateDataAPI = async (type: string, config: unknown) => {
  const response = await fetch(`${API_BASE_URL}/api/data/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      dataType: type,
      config: config
    })
  })
  
  if (!response.ok) {
    throw new Error(`API 호출 실패: ${response.statusText}`)
  }
  
  return await response.json()
}

// 저장된 파일 목록 조회 API
const getStoredFilesAPI = async () => {
  const response = await fetch(`${API_BASE_URL}/api/data/files`)
  
  if (!response.ok) {
    throw new Error(`파일 목록 조회 실패: ${response.statusText}`)
  }
  
  return await response.json()
}

// 파일 미리보기 API
const getFilePreviewAPI = async (filename: string) => {
  const response = await fetch(`${API_BASE_URL}/api/data/preview/${encodeURIComponent(filename)}`)
  console.log('🎯 파일 미리보기 API 호출:', response)
  if (!response.ok) {
    throw new Error(`미리보기 조회 실패: ${response.statusText}`)
  }
  
  return await response.json()
}

// 파일 삭제 API
const deleteFileAPI = async (filename: string) => {
  const response = await fetch(`${API_BASE_URL}/api/data/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    throw new Error(`파일 삭제 실패: ${response.statusText}`)
  }
  
  return await response.json()
}

// ============================
// StatusCard 컴포넌트 (공정분석 페이지와 동일)
// ============================

interface StatusCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: string
  color: string
}

function StatusCard({ title, value, icon, trend, color }: StatusCardProps) {
  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-muted-foreground text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {trend && (
            <p className={`text-sm ${trend.includes('↑') ? 'text-accent-cyan' : trend.includes('↓') ? 'text-accent-orange' : 'text-muted-foreground'}`}>
              {trend}
            </p>
          )}
        </div>
        <div 
          className="p-3 rounded-lg"
          style={{ backgroundColor: color }}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

// ============================
// 타입 정의
// ============================

interface GenerationResult {
  success: boolean
  data?: any[]
  message: string
  filename?: string
  summary?: {
    totalRecords: number
    totalLots?: number
    averagePurity?: number
    averageYield?: number
    averageCost?: number
    dateRange?: string
    costRange?: number
    sensorTypes?: Array<{
      name: string
      average: number
      max: number
      min: number
      unit: string
    }>
  }
}

interface ProductionConfig {
  lotCount: number
  equipmentCount: number
  timePeriod: string
  workDateStart: string
  workDateEnd: string
  shiftType: string
  customShiftStart?: string
  customShiftEnd?: string
  purityRange: [number, number]
  yieldRange: [number, number]
  addNoise: boolean
  noiseLevel: number
  addAnomalies: boolean
  anomalyRatio: number
}

interface SensorConfig {
  dataCount: number
  selectedEquipment: string
  selectedSensors: string[]
  collectionInterval: string
  workDateStart: string
  workDateEnd: string
  shiftType: string
  customShiftStart?: string
  customShiftEnd?: string
  sensorRanges: Record<string, [number, number]>
  addNoise: boolean
  noiseLevel: number
  addAnomalies: boolean
  anomalyRatio: number
  addMissingData: boolean
  missingDataRatio: number
  dataPattern: string
  variationIntensity: number
}

interface ExperimentalConfig {
  experimentType: string
  selectedFactors: string[]
  levels: number
  replications: number
  numExperiments: number
  factorRanges: Record<string, [number, number]>
  experimentDateStart: string
  experimentDateEnd: string
  experimentShiftType: string
  experimentInterval: string
  experimenter: string
  experimentPurpose: string
  experimentObjective: string
}

interface CostConfig {
  recordCount: number
  startDate: string
  endDate: string
  productGrade: string
  purityRange: [number, number]
  yieldRange: [number, number]
  materialARage: [number, number]
  materialACost: number
  materialBRange: [number, number]
  materialBCost: number
  catalystRange: [number, number]
  catalystCost: number
  tempRange: [number, number]
  pressureRange: [number, number]
  flowRange: [number, number]
  steamRange: [number, number]
  steamCost: number
  electricityRange: [number, number]
  electricityCost: number
  coolingRange: [number, number]
  coolingCost: number
  priceVolatility: number
  utilityVolatility: number
  seasonalEffect: boolean
  correlationStrength: number
  noiseLevel: number
  includeShifts: boolean
  includeEquipmentWear: boolean
}

interface DataFile {
  filepath: string
  dataType: string
  filename: string
  createTime: Date
  fileSizeKb: number
  rowCount?: number
  colCount?: number
  previewData?: any[]
  error?: string
}

// ============================
// 재사용 가능한 컴포넌트들
// ============================

interface ExpanderProps {
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
  icon?: React.ReactNode
}

function Expander({ title, children, defaultExpanded = false, icon }: ExpanderProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="mb-4 bg-card backdrop-blur-sm border border-border rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          {icon}
          <span className="font-medium text-foreground">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-5 h-5 text-muted-foreground" />
        )}
      </button>
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4">
          {children}
        </div>
      )}
    </div>
  )
}







interface TextInputProps {
  value: string
  onChange: (value: string) => void
  label: string
  placeholder?: string
}

function TextInput({ value, onChange, label, placeholder }: TextInputProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-foreground text-sm placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
      />
    </div>
  )
}

interface TextAreaProps {
  value: string
  onChange: (value: string) => void
  label: string
  placeholder?: string
  rows?: number
}

function TextArea({ value, onChange, label, placeholder, rows = 3 }: TextAreaProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-foreground text-sm placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent resize-none"
      />
    </div>
  )
}

interface DateInputProps {
  value: string
  onChange: (value: string) => void
  label: string
  min?: string
  max?: string
}

function DateInput({ value, onChange, label, min, max }: DateInputProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={min}
        max={max}
        className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
      />
    </div>
  )
}

interface TimeInputProps {
  value: string
  onChange: (value: string) => void
  label: string
}

function TimeInput({ value, onChange, label }: TimeInputProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <input
        type="time"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
      />
    </div>
  )
}

// ============================
// 메인 컴포넌트
// ============================

export default function DataGenerationPage() {
  const [activeTab, setActiveTab] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<GenerationResult | null>(null)
  const [savedFiles, setSavedFiles] = useState<DataFile[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(false)
  const { t } = useTranslation()

  // 데이터 생성 통계 (안전한 계산)
  const dataStats = {
    totalFiles: Array.isArray(savedFiles) ? savedFiles.length : 0,
    generatingFiles: isGenerating ? 1 : 0,
    totalRecords: Array.isArray(savedFiles) ? savedFiles.reduce((sum, file) => sum + (file.rowCount || 0), 0) : 0,
    lastGenerated: Array.isArray(savedFiles) && savedFiles.length > 0 && savedFiles[0]?.createTime 
      ? new Date(savedFiles[0].createTime).toLocaleDateString() 
      : '데이터 없음'
  }

  const tabs = [
    { id: 'production', name: t('dataGeneration.tabs.production'), icon: Factory },
    { id: 'sensor', name: '센서 데이터', icon: Activity },
    { id: 'experimental', name: t('dataGeneration.tabs.experimental'), icon: FlaskConical },
    { id: 'cost', name: t('dataGeneration.tabs.cost'), icon: DollarSign },
  ]

  // 저장된 파일 목록 불러오기
  const loadSavedFiles = async () => {
    setIsLoadingFiles(true)
    try {
      // 실제 백엔드 API에서 파일 목록 가져오기
      const response = await getStoredFilesAPI()
      setSavedFiles(response.files || [])
    } catch (error) {
      console.error('파일 목록 로드 실패:', error)
      // API 실패 시 빈 배열로 설정
      setSavedFiles([])
    } finally {
      setIsLoadingFiles(false)
    }
  }

  // 백업용 목데이터 로드 함수 (개발/테스트 환경용)
  const loadMockFiles = async () => {
    setIsLoadingFiles(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 목데이터
      const mockFiles: DataFile[] = [
        {
          filepath: '/data/generated/production/manufacturing_copilot_production_data_100lots_100records_20250711_064508.csv',
          dataType: 'production',
          filename: 'manufacturing_copilot_production_data_100lots_100records_20250711_064508.csv',
          createTime: new Date('2025-07-11T06:45:08'),
          fileSizeKb: 15.0,
          rowCount: 100,
          colCount: 11,
          previewData: [
            { id: 1, timestamp: '2025-07-11T06:00:00', lot_id: 'LOT-001', equipment_id: 'EQ-A1', temperature: 285, pressure: 15.2, purity: 96.5, yield: 89.2, cost: 45280, operator: 'Kim', shift: 'Day' },
            { id: 2, timestamp: '2025-07-11T06:15:00', lot_id: 'LOT-002', equipment_id: 'EQ-A2', temperature: 290, pressure: 15.8, purity: 95.8, yield: 87.9, cost: 46150, operator: 'Lee', shift: 'Day' },
            { id: 3, timestamp: '2025-07-11T06:30:00', lot_id: 'LOT-003', equipment_id: 'EQ-B1', temperature: 275, pressure: 14.9, purity: 97.1, yield: 91.3, cost: 44890, operator: 'Park', shift: 'Day' },
            { id: 4, timestamp: '2025-07-11T06:45:00', lot_id: 'LOT-004', equipment_id: 'EQ-A1', temperature: 288, pressure: 15.5, purity: 96.8, yield: 90.1, cost: 45150, operator: 'Kim', shift: 'Day' },
            { id: 5, timestamp: '2025-07-11T07:00:00', lot_id: 'LOT-005', equipment_id: 'EQ-C1', temperature: 282, pressure: 15.0, purity: 95.2, yield: 88.5, cost: 46820, operator: 'Choi', shift: 'Day' },
            { id: 6, timestamp: '2025-07-11T07:15:00', lot_id: 'LOT-006', equipment_id: 'EQ-B2', temperature: 295, pressure: 16.1, purity: 97.3, yield: 92.0, cost: 44320, operator: 'Jung', shift: 'Day' },
            { id: 7, timestamp: '2025-07-11T07:30:00', lot_id: 'LOT-007', equipment_id: 'EQ-A2', temperature: 280, pressure: 14.7, purity: 96.1, yield: 89.8, cost: 45690, operator: 'Lee', shift: 'Day' },
            { id: 8, timestamp: '2025-07-11T07:45:00', lot_id: 'LOT-008', equipment_id: 'EQ-C2', temperature: 287, pressure: 15.3, purity: 95.9, yield: 88.2, cost: 46050, operator: 'Song', shift: 'Day' }
          ]
        },
        {
          filepath: '/data/generated/production/manufacturing_copilot_production_data_100lots_100records_20250711_064507.csv',
          dataType: 'production',
          filename: 'manufacturing_copilot_production_data_100lots_100records_20250711_064507.csv',
          createTime: new Date('2025-07-11T06:45:07'),
          fileSizeKb: 15.0,
          rowCount: 100,
          colCount: 11,
          previewData: [
            { id: 1, timestamp: '2025-07-11T05:00:00', lot_id: 'LOT-101', equipment_id: 'EQ-A3', temperature: 283, pressure: 15.0, purity: 96.2, yield: 88.8, cost: 45480, operator: 'Yoon', shift: 'Day' },
            { id: 2, timestamp: '2025-07-11T05:15:00', lot_id: 'LOT-102', equipment_id: 'EQ-B3', temperature: 287, pressure: 15.4, purity: 95.5, yield: 87.5, cost: 46380, operator: 'Han', shift: 'Day' },
            { id: 3, timestamp: '2025-07-11T05:30:00', lot_id: 'LOT-103', equipment_id: 'EQ-C3', temperature: 292, pressure: 15.9, purity: 97.0, yield: 90.8, cost: 44720, operator: 'Lim', shift: 'Day' },
            { id: 4, timestamp: '2025-07-11T05:45:00', lot_id: 'LOT-104', equipment_id: 'EQ-A3', temperature: 279, pressure: 14.6, purity: 96.7, yield: 89.5, cost: 45220, operator: 'Yoon', shift: 'Day' },
            { id: 5, timestamp: '2025-07-11T06:00:00', lot_id: 'LOT-105', equipment_id: 'EQ-B1', temperature: 285, pressure: 15.2, purity: 95.8, yield: 88.2, cost: 46110, operator: 'Park', shift: 'Day' },
            { id: 6, timestamp: '2025-07-11T06:15:00', lot_id: 'LOT-106', equipment_id: 'EQ-C1', temperature: 289, pressure: 15.6, purity: 97.2, yield: 91.5, cost: 44580, operator: 'Choi', shift: 'Day' },
            { id: 7, timestamp: '2025-07-11T06:30:00', lot_id: 'LOT-107', equipment_id: 'EQ-A1', temperature: 282, pressure: 14.8, purity: 96.1, yield: 89.0, cost: 45750, operator: 'Kim', shift: 'Day' },
            { id: 8, timestamp: '2025-07-11T06:45:00', lot_id: 'LOT-108', equipment_id: 'EQ-B2', temperature: 291, pressure: 15.7, purity: 95.9, yield: 88.7, cost: 45980, operator: 'Jung', shift: 'Day' }
          ]
        },
        {
          filepath: '/data/generated/production/manufacturing_copilot_production_data_100lots_100records_20250711_064506.csv',
          dataType: 'production',
          filename: 'manufacturing_copilot_production_data_100lots_100records_20250711_064506.csv',
          createTime: new Date('2025-07-11T06:45:06'),
          fileSizeKb: 15.0,
          rowCount: 100,
          colCount: 11,
          previewData: [
            { id: 1, timestamp: '2025-07-11T04:00:00', lot_id: 'LOT-201', equipment_id: 'EQ-D1', temperature: 281, pressure: 14.7, purity: 96.0, yield: 88.5, cost: 45620, operator: 'Shin', shift: 'Night' },
            { id: 2, timestamp: '2025-07-11T04:15:00', lot_id: 'LOT-202', equipment_id: 'EQ-D2', temperature: 286, pressure: 15.3, purity: 95.7, yield: 87.8, cost: 46210, operator: 'Oh', shift: 'Night' },
            { id: 3, timestamp: '2025-07-11T04:30:00', lot_id: 'LOT-203', equipment_id: 'EQ-E1', temperature: 293, pressure: 16.0, purity: 97.4, yield: 91.2, cost: 44450, operator: 'Kang', shift: 'Night' },
            { id: 4, timestamp: '2025-07-11T04:45:00', lot_id: 'LOT-204', equipment_id: 'EQ-D1', temperature: 277, pressure: 14.4, purity: 96.9, yield: 89.7, cost: 45080, operator: 'Shin', shift: 'Night' },
            { id: 5, timestamp: '2025-07-11T05:00:00', lot_id: 'LOT-205', equipment_id: 'EQ-E2', temperature: 284, pressure: 15.1, purity: 95.4, yield: 88.0, cost: 46450, operator: 'Baek', shift: 'Night' },
            { id: 6, timestamp: '2025-07-11T05:15:00', lot_id: 'LOT-206', equipment_id: 'EQ-D2', temperature: 288, pressure: 15.5, purity: 97.1, yield: 90.9, cost: 44680, operator: 'Oh', shift: 'Night' },
            { id: 7, timestamp: '2025-07-11T05:30:00', lot_id: 'LOT-207', equipment_id: 'EQ-E1', temperature: 290, pressure: 15.8, purity: 96.3, yield: 89.3, cost: 45410, operator: 'Kang', shift: 'Night' },
            { id: 8, timestamp: '2025-07-11T05:45:00', lot_id: 'LOT-208', equipment_id: 'EQ-D1', temperature: 285, pressure: 15.2, purity: 95.6, yield: 88.4, cost: 46080, operator: 'Shin', shift: 'Night' }
          ]
        },
        {
          filepath: '/data/generated/production/manufacturing_copilot_production_data_100lots_100records_20250711_064503.csv',
          dataType: 'production',
          filename: 'manufacturing_copilot_production_data_100lots_100records_20250711_064503.csv',
          createTime: new Date('2025-07-11T06:45:03'),
          fileSizeKb: 15.0,
          rowCount: 100,
          colCount: 11,
          previewData: [
            { id: 1, timestamp: '2025-07-11T03:00:00', lot_id: 'LOT-301', equipment_id: 'EQ-F1', temperature: 280, pressure: 14.5, purity: 95.8, yield: 88.1, cost: 45890, operator: 'Nam', shift: 'Night' },
            { id: 2, timestamp: '2025-07-11T03:15:00', lot_id: 'LOT-302', equipment_id: 'EQ-F2', temperature: 289, pressure: 15.6, purity: 96.4, yield: 89.6, cost: 45320, operator: 'Ryu', shift: 'Night' },
            { id: 3, timestamp: '2025-07-11T03:30:00', lot_id: 'LOT-303', equipment_id: 'EQ-G1', temperature: 294, pressure: 16.2, purity: 97.6, yield: 91.8, cost: 44190, operator: 'Seo', shift: 'Night' },
            { id: 4, timestamp: '2025-07-11T03:45:00', lot_id: 'LOT-304', equipment_id: 'EQ-F1', temperature: 276, pressure: 14.2, purity: 97.0, yield: 90.2, cost: 44820, operator: 'Nam', shift: 'Night' },
            { id: 5, timestamp: '2025-07-11T04:00:00', lot_id: 'LOT-305', equipment_id: 'EQ-G2', temperature: 287, pressure: 15.4, purity: 95.2, yield: 87.7, cost: 46580, operator: 'Jang', shift: 'Night' },
            { id: 6, timestamp: '2025-07-11T04:15:00', lot_id: 'LOT-306', equipment_id: 'EQ-F2', temperature: 291, pressure: 15.9, purity: 96.8, yield: 90.5, cost: 44950, operator: 'Ryu', shift: 'Night' },
            { id: 7, timestamp: '2025-07-11T04:30:00', lot_id: 'LOT-307', equipment_id: 'EQ-G1', temperature: 283, pressure: 14.9, purity: 96.1, yield: 88.9, cost: 45650, operator: 'Seo', shift: 'Night' },
            { id: 8, timestamp: '2025-07-11T04:45:00', lot_id: 'LOT-308', equipment_id: 'EQ-F1', temperature: 288, pressure: 15.5, purity: 95.5, yield: 88.3, cost: 46170, operator: 'Nam', shift: 'Night' }
          ]
        },
        {
          filepath: '/data/generated/experimental_data_20241130_50experiments.csv',
          dataType: 'experimental',
          filename: 'experimental_data_20241130_50experiments.csv',
          createTime: new Date('2024-11-30T15:45:00'),
          fileSizeKb: 12.3,
          rowCount: 50,
          colCount: 12,
          previewData: [
            { experiment_id: 1, run_date: '2024-11-30', temperature: 280, pressure: 15.2, catalyst: 0.05, flowrate: 125, residence_time: 45, purity: 94.8, yield: 86.5, selectivity: 91.2, researcher: 'Dr.Kim', design_type: 'Full_Factorial' },
            { experiment_id: 2, run_date: '2024-11-30', temperature: 290, pressure: 16.0, catalyst: 0.06, flowrate: 130, residence_time: 42, purity: 96.2, yield: 88.1, selectivity: 92.8, researcher: 'Dr.Lee', design_type: 'Full_Factorial' },
            { experiment_id: 3, run_date: '2024-11-30', temperature: 275, pressure: 14.8, catalyst: 0.04, flowrate: 120, residence_time: 48, purity: 93.5, yield: 85.2, selectivity: 89.7, researcher: 'Dr.Park', design_type: 'Central_Composite' },
            { experiment_id: 4, run_date: '2024-11-30', temperature: 285, pressure: 15.5, catalyst: 0.055, flowrate: 127, residence_time: 44, purity: 95.1, yield: 87.3, selectivity: 91.8, researcher: 'Dr.Kim', design_type: 'Full_Factorial' },
            { experiment_id: 5, run_date: '2024-11-30', temperature: 295, pressure: 16.3, catalyst: 0.065, flowrate: 135, residence_time: 40, purity: 96.8, yield: 89.2, selectivity: 93.5, researcher: 'Dr.Choi', design_type: 'Taguchi' },
            { experiment_id: 6, run_date: '2024-11-30', temperature: 270, pressure: 14.5, catalyst: 0.035, flowrate: 115, residence_time: 50, purity: 92.8, yield: 84.1, selectivity: 88.4, researcher: 'Dr.Jung', design_type: 'Central_Composite' },
            { experiment_id: 7, run_date: '2024-11-30', temperature: 288, pressure: 15.8, catalyst: 0.058, flowrate: 128, residence_time: 43, purity: 95.7, yield: 88.0, selectivity: 92.1, researcher: 'Dr.Lee', design_type: 'Taguchi' }
          ]
        },
        {
          filepath: '/data/generated/cost_data_20241129_200records.csv',
          dataType: 'cost',
          filename: 'cost_data_20241129_200records.csv',
          createTime: new Date('2024-11-29T14:20:00'),
          fileSizeKb: 41.2,
          rowCount: 200,
          colCount: 16,
          previewData: [
            { id: 1, date: '2024-11-29', product_grade: 'Grade A', batch_id: 'B001', material_A: 12500, material_B: 8200, catalyst: 2800, steam: 4200, electricity: 2900, cooling: 1800, labor: 6500, maintenance: 1200, total_cost: 52480, purity: 96.2, yield: 89.5, plant: 'Plant_1' },
            { id: 2, date: '2024-11-29', product_grade: 'Grade A', batch_id: 'B002', material_A: 12200, material_B: 8000, catalyst: 2750, steam: 4150, electricity: 2850, cooling: 1750, labor: 6400, maintenance: 1150, total_cost: 51890, purity: 95.8, yield: 88.9, plant: 'Plant_1' },
            { id: 3, date: '2024-11-29', product_grade: 'Grade B', batch_id: 'B003', material_A: 11800, material_B: 7500, catalyst: 2600, steam: 3900, electricity: 2650, cooling: 1650, labor: 6200, maintenance: 1100, total_cost: 48320, purity: 94.1, yield: 87.2, plant: 'Plant_2' },
            { id: 4, date: '2024-11-29', product_grade: 'Grade A', batch_id: 'B004', material_A: 12800, material_B: 8400, catalyst: 2900, steam: 4300, electricity: 3000, cooling: 1900, labor: 6600, maintenance: 1250, total_cost: 53150, purity: 96.8, yield: 90.1, plant: 'Plant_1' },
            { id: 5, date: '2024-11-29', product_grade: 'Grade B', batch_id: 'B005', material_A: 11600, material_B: 7200, catalyst: 2500, steam: 3800, electricity: 2550, cooling: 1600, labor: 6100, maintenance: 1050, total_cost: 47890, purity: 93.5, yield: 86.8, plant: 'Plant_2' },
            { id: 6, date: '2024-11-29', product_grade: 'Grade C', batch_id: 'B006', material_A: 10800, material_B: 6800, catalyst: 2200, steam: 3500, electricity: 2300, cooling: 1450, labor: 5800, maintenance: 950, total_cost: 44200, purity: 91.2, yield: 84.5, plant: 'Plant_3' },
            { id: 7, date: '2024-11-29', product_grade: 'Grade A', batch_id: 'B007', material_A: 12600, material_B: 8300, catalyst: 2850, steam: 4250, electricity: 2950, cooling: 1850, labor: 6550, maintenance: 1200, total_cost: 52750, purity: 96.5, yield: 89.8, plant: 'Plant_1' },
            { id: 8, date: '2024-11-29', product_grade: 'Grade B', batch_id: 'B008', material_A: 12000, material_B: 7600, catalyst: 2650, steam: 3950, electricity: 2700, cooling: 1700, labor: 6300, maintenance: 1080, total_cost: 48680, purity: 94.8, yield: 87.6, plant: 'Plant_2' }
          ]
        },

        {
          filepath: '/data/generated/experimental_data_20241127_75experiments.csv',
          dataType: 'experimental',
          filename: 'experimental_data_20241127_75experiments.csv',
          createTime: new Date('2024-11-27T16:30:00'),
          fileSizeKb: 18.7,
          rowCount: 75,
          colCount: 12
        }
      ]

      setSavedFiles(mockFiles)
    } catch (error) {
      console.error('목데이터 로드 실패:', error)
      setSavedFiles([])
    } finally {
      setIsLoadingFiles(false)
    }
  }

  // 페이지 로드 시 저장된 파일 목록 불러오기
  useEffect(() => {
    const initializeFiles = async () => {
      try {
        // 먼저 실제 API 시도
        await loadSavedFiles()
      } catch (error) {
        console.log('API 호출 실패, 목데이터 사용:', error)
        // API 실패 시 목데이터 사용
        await loadMockFiles()
      }
    }
    
    initializeFiles()
  }, [])

  const generateData = async (type: string, config: any) => {
    setIsGenerating(true)
    setResult(null)

    try {
      // 디버깅: 전송되는 config 확인
      console.log('DEBUG - Frontend sending config:', config)
      console.log('DEBUG - Type:', type)
      console.log('DEBUG - lotCount in config:', config.lotCount)
      
      // 실제 백엔드 API 호출
      const response = await generateDataAPI(type, config)
      
      // 디버깅: 응답 데이터 확인
      console.log('DEBUG - Backend response:', response)
      console.log('DEBUG - Response data length:', response.data?.length)
      
      setResult({
        success: true,
        data: response.data || [],
        message: response.message || `${type} 데이터가 성공적으로 생성되었습니다.`,
        filename: response.filename,
        summary: response.summary || {
          totalRecords: response.data?.length || 0,
          averagePurity: response.summary?.averagePurity,
          averageYield: response.summary?.averageYield,
          averageCost: response.summary?.averageCost,
          dateRange: response.summary?.dateRange,
          costRange: response.summary?.costRange
        }
      })
      
      // 데이터 생성 완료 후 저장된 파일 목록 새로고침
      await loadSavedFiles()
      
    } catch (error) {
      console.error('데이터 생성 오류:', error)
      setResult({
        success: false,
        message: `${type} 데이터 생성 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="p-6">
      <div className="w-full">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-4 flex items-center">
            <Database className="w-8 h-8 mr-3 text-accent-blue" />
            {t('dataGeneration.title')}
          </h1>
          <p className="text-muted-foreground text-lg">
            {t('dataGeneration.subtitle')}
          </p>
        </div>

        {/* 데이터 생성 현황 대시보드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title="총 생성 파일"
            value={dataStats.totalFiles}
            icon={<Database className="w-6 h-6 text-white" />}
            color="#3b82f6"
          />
          <StatusCard
            title="생성 중 파일"
            value={dataStats.generatingFiles}
            icon={<Activity className="w-6 h-6 text-white" />}
            color="#f97316"
          />
          <StatusCard
            title="총 레코드 수"
            value={dataStats.totalRecords.toLocaleString()}
            icon={<TrendingUp className="w-6 h-6 text-white" />}
            color="#22c55e"
          />
          <StatusCard
            title="최근 생성일"
            value={dataStats.lastGenerated}
            icon={<Clock className="w-6 h-6 text-white" />}
            color="#8b5cf6"
          />
        </div>

        {/* Tabs */}
        <TabNavigation
          tabs={tabs.map((tab, index) => ({
            id: index,
            name: tab.name,
            icon: tab.icon
          }))}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as number)}
          className="mb-8"
        />

        {/* Content */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Configuration Panel */}
          <div>
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-sm">
              {activeTab === 0 && <ProductionDataConfig onGenerate={generateData} isGenerating={isGenerating} />}
              {activeTab === 1 && <SensorDataConfig onGenerate={generateData} isGenerating={isGenerating} />}
              {activeTab === 2 && <ExperimentalDataConfig onGenerate={generateData} isGenerating={isGenerating} />}
              {activeTab === 3 && <CostDataConfig onGenerate={generateData} isGenerating={isGenerating} />}
            </div>
          </div>

          {/* Info & Result Panel */}
          <div className="space-y-6">
            <InfoPanel activeTab={activeTab} />
            {result && <ResultPanel result={result} />}
          </div>
        </div>

        {/* Saved Data Management Section */}
        <div className="mt-16">
          <DataManagementPanel 
            files={savedFiles} 
            isLoading={isLoadingFiles} 
            onRefresh={async () => {
              try {
                await loadSavedFiles()
              } catch (error) {
                console.log('API 새로고침 실패, 목데이터 사용:', error)
                await loadMockFiles()
              }
            }}
            activeTab={activeTab}
            onFileDelete={(filename: string) => {
              setSavedFiles(prev => prev.filter(file => file.filename !== filename))
            }}
          />
        </div>
      </div>
    </div>
  )
}

// ============================
// 생산 데이터 설정 컴포넌트
// ============================

function ProductionDataConfig({ onGenerate, isGenerating }: { onGenerate: (type: string, config: unknown) => void, isGenerating: boolean }) {
  const { t } = useTranslation()
  const [config, setConfig] = useState<ProductionConfig>({
    lotCount: 100,
    equipmentCount: 10,
    timePeriod: "1개월",
    workDateStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    workDateEnd: new Date().toISOString().split('T')[0],
    shiftType: "주간(08:00-16:00)",
    purityRange: [95.0, 98.5],
    yieldRange: [85.0, 95.0],
    addNoise: true,
    noiseLevel: 1.0,
    addAnomalies: false,
    anomalyRatio: 3
  })

  const handleGenerate = () => {
    onGenerate('production', config)
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-foreground flex items-center">
        <Settings className="w-6 h-6 mr-2 text-accent-blue" />
        {t('dataGeneration.production.title')}
      </h3>

      {/* 기본 파라미터 */}
      <Expander title={t('dataGeneration.production.basicParams')} defaultExpanded={true}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Slider
            min={10}
            max={1000}
            step={10}
            value={config.lotCount}
            onChange={(value) => setConfig(prev => ({ ...prev, lotCount: value }))}
            label="Lot 개수"
            unit="개"
          />
          <Slider
            min={1}
            max={50}
            value={config.equipmentCount}
            onChange={(value) => setConfig(prev => ({ ...prev, equipmentCount: value }))}
            label="설비 개수"
            unit="개"
          />
        </div>

        <Select
          value={config.timePeriod}
          onChange={(value) => setConfig(prev => ({ ...prev, timePeriod: value }))}
          options={["1일", "1주", "1개월", "3개월", "6개월"]}
          label="기간"
        />

        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-medium text-foreground mb-4 flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            {t('dataGeneration.production.workSchedule')}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DateInput
              value={config.workDateStart}
              onChange={(value) => setConfig(prev => ({ ...prev, workDateStart: value }))}
              label="작업 시작 날짜"
              max={new Date().toISOString().split('T')[0]}
            />
            <DateInput
              value={config.workDateEnd}
              onChange={(value) => setConfig(prev => ({ ...prev, workDateEnd: value }))}
              label="작업 종료 날짜"
              min={config.workDateStart}
              max={new Date().toISOString().split('T')[0]}
            />
          </div>
        </div>

        <Select
          value={config.shiftType}
          onChange={(value) => setConfig(prev => ({ ...prev, shiftType: value }))}
          options={["주간(08:00-16:00)", "야간(22:00-06:00)", "전체(24시간)", "사용자 정의"]}
          label="시간대 설정"
        />

        {config.shiftType === "사용자 정의" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TimeInput
              value={config.customShiftStart || "08:00"}
              onChange={(value) => setConfig(prev => ({ ...prev, customShiftStart: value }))}
              label="작업 시작 시간"
            />
            <TimeInput
              value={config.customShiftEnd || "16:00"}
              onChange={(value) => setConfig(prev => ({ ...prev, customShiftEnd: value }))}
              label="작업 종료 시간"
            />
          </div>
        )}
      </Expander>

      {/* 품질 지표 */}
      <Expander title={t('dataGeneration.production.qualitySettings')} icon={<TrendingUp className="w-5 h-5 text-accent-cyan" />}>
        <div className="space-y-4">
          <RangeSlider
            min={90.0}
            max={99.9}
            step={0.1}
            value={config.purityRange}
            onChange={(value) => setConfig(prev => ({ ...prev, purityRange: value }))}
            label="순도 범위 (%)"
            unit="%"
          />
          <RangeSlider
            min={80.0}
            max={100.0}
            step={0.5}
            value={config.yieldRange}
            onChange={(value) => setConfig(prev => ({ ...prev, yieldRange: value }))}
            label="수율 범위 (%)"
            unit="%"
          />
        </div>
      </Expander>

      {/* 시뮬레이션 옵션 */}
      <Expander title={t('dataGeneration.production.simulationOptions')} icon={<Sliders className="w-5 h-5 text-accent-orange" />}>
        <div className="space-y-4">
          <Checkbox
            checked={config.addNoise}
            onChange={(checked) => setConfig(prev => ({ ...prev, addNoise: checked }))}
            label={t('dataGeneration.production.addNoise')}
          />
          
          {config.addNoise && (
            <Slider
              min={0.1}
              max={5.0}
              step={0.1}
              value={config.noiseLevel}
              onChange={(value) => setConfig(prev => ({ ...prev, noiseLevel: value }))}
              label={t('dataGeneration.production.noiseLevel')}
            />
          )}

          <Checkbox
            checked={config.addAnomalies}
            onChange={(checked) => setConfig(prev => ({ ...prev, addAnomalies: checked }))}
            label={t('dataGeneration.production.addAnomalies')}
          />

          {config.addAnomalies && (
            <Slider
              min={1}
              max={10}
              value={config.anomalyRatio}
              onChange={(value) => setConfig(prev => ({ ...prev, anomalyRatio: value }))}
              label={t('dataGeneration.production.anomalyRatio')}
              unit="%"
            />
          )}
        </div>
      </Expander>

      {/* 생성 버튼 */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="w-full flex items-center justify-center px-6 py-4 bg-gradient-primary hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-glass-lg transition-all duration-300 shadow-glow disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            {t('dataGeneration.production.generating')}
          </>
        ) : (
          <>
            <Play className="w-5 h-5 mr-2" />
            {t('dataGeneration.production.generate')}
          </>
        )}
      </button>
    </div>
  )
}

// ============================
// 센서 데이터 설정 컴포넌트
// ============================

function SensorDataConfig({ onGenerate, isGenerating }: { onGenerate: (type: string, config: unknown) => void, isGenerating: boolean }) {
  const [config, setConfig] = useState<SensorConfig>({
    dataCount: 15000,
    selectedEquipment: 'dryer',
    selectedSensors: ['outlet_humidity', 'inlet_humidity', 'drying_temperature', 'air_flow', 'pressure_diff', 'moisture_content', 'residence_time'],
    collectionInterval: "10초",
    workDateStart: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    workDateEnd: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    shiftType: "주간(08:00-16:00)",
    sensorRanges: {
      // 건조기 센서
      outlet_humidity: [40.0, 80.0],
      inlet_humidity: [5.0, 15.0],
      drying_temperature: [80.0, 200.0],
      air_flow: [1000, 5000],
      pressure_diff: [50, 500],
      moisture_content: [0.0, 1.0],
      residence_time: [200.0, 300.0],
      // 분급기 센서
      mill_rpm: [100, 800],
      crushing_pressure: [2.0, 10.0],
      classifier_speed: [300, 1500],
      vacuum_pressure: [0.1, 0.8],
      particle_size: [10, 100],
      particle_d50: [5.0, 25.0],
      // 펌프 센서
      flow_rate: [10, 200],
      discharge_pressure: [2.0, 15.0],
      suction_pressure: [0.5, 3.0],
      vibration: [0.5, 5.0],
      temperature: [20.0, 80.0],
      // 컴프레서 센서
      discharge_temperature: [60.0, 150.0],
      current: [10.0, 100.0],
      // 모터 센서
      rpm: [500, 3000],
      torque: [50, 500],
      // 팬 센서
      // 보일러 센서
      steam_pressure: [5.0, 20.0],
      steam_temperature: [150.0, 300.0],
      feed_water_temp: [80.0, 150.0],
      fuel_pressure: [1.0, 5.0],
      oxygen_level: [2.0, 8.0]
    },
    addNoise: true,
    noiseLevel: 1.0,
    addAnomalies: false,
    anomalyRatio: 3,
    addMissingData: false,
    missingDataRatio: 5,
    dataPattern: "정상",
    variationIntensity: 3
  })

  // 산업 설비별 센서 매핑
  const equipmentSensorMap = {
    dryer: {
      name: '건조기 (Dryer)',
      sensors: ['outlet_humidity', 'inlet_humidity', 'drying_temperature', 'air_flow', 'pressure_diff', 'moisture_content', 'residence_time']
    },
    classifier: {
      name: '분급기 (Classifier)', 
      sensors: ['mill_rpm', 'crushing_pressure', 'classifier_speed', 'vacuum_pressure', 'particle_size', 'particle_d50']
    },
    pump: {
      name: '펌프 (Pump)',
      sensors: ['flow_rate', 'discharge_pressure', 'suction_pressure', 'vibration', 'temperature']
    },
    compressor: {
      name: '컴프레셔 (Compressor)',
      sensors: ['discharge_pressure', 'suction_pressure', 'discharge_temperature', 'vibration', 'current']
    },
    motor: {
      name: '모터 (Motor)',
      sensors: ['rpm', 'torque', 'current', 'temperature', 'vibration']
    },
    fan: {
      name: '팬 (Fan)',
      sensors: ['rpm', 'air_flow', 'discharge_pressure', 'vibration', 'current']
    },
    boiler: {
      name: '보일러 (Boiler)',
      sensors: ['steam_pressure', 'steam_temperature', 'feed_water_temp', 'fuel_pressure', 'oxygen_level']
    }
  }

  const equipmentOptions = Object.keys(equipmentSensorMap)

  // 설비 변경 시 센서 자동 업데이트
  const handleEquipmentChange = (equipment: string) => {
    const equipmentData = equipmentSensorMap[equipment as keyof typeof equipmentSensorMap]
    if (equipmentData) {
      setConfig(prev => ({
        ...prev,
        selectedEquipment: equipment,
        selectedSensors: equipmentData.sensors
      }))
    }
  }

  const getSensorLabel = (sensorType: string) => {
    const labels: Record<string, string> = {
      // 건조기 센서
      'outlet_humidity': '출구습도 (%)',
      'inlet_humidity': '입구습도 (%)',
      'drying_temperature': '건조온도 (°C)',
      'air_flow': '풍량 (m³/h)',
      'pressure_diff': '압력차 (Pa)',
      'moisture_content': '수분값 (wt%)',
      'residence_time': '체류시간 (s)',
      // 분급기 센서
      'mill_rpm': '밀 회전속도 (RPM)',
      'crushing_pressure': '분쇄압력 (MPa)',
      'classifier_speed': '분급기 속도 (RPM)',
      'vacuum_pressure': '진공압 (MPa)',
      'particle_size': '입자크기 (μm)',
      'particle_d50': '입도 D50 (μm)',
      // 펌프 센서
      'flow_rate': '유량 (L/min)',
      'discharge_pressure': '토출압력 (MPa)',
      'suction_pressure': '흡입압력 (MPa)',
      'vibration': '진동 (mm/s)',
      'temperature': '온도 (°C)',
      // 컴프레서 센서
      'discharge_temperature': '토출온도 (°C)',
      'current': '전류 (A)',
      // 모터 센서
      'rpm': '회전속도 (RPM)',
      'torque': '토크 (Nm)',
      // 팬 센서 (일부 공통)
      // 보일러 센서
      'steam_pressure': '증기압력 (MPa)',
      'steam_temperature': '증기온도 (°C)',
      'feed_water_temp': '급수온도 (°C)',
      'fuel_pressure': '연료압력 (MPa)',
      'oxygen_level': '산소농도 (%)'
    }
    return labels[sensorType] || sensorType
  }

  const handleGenerate = () => {
    onGenerate('sensor', config)
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-foreground flex items-center">
        <Settings className="w-6 h-6 mr-2 text-accent-blue" />
        센서 데이터 생성 설정
      </h3>

      {/* 기본 파라미터 */}
      <Expander title="기본 파라미터" defaultExpanded={true}>
        <div className="grid grid-cols-1 gap-4">
          <NumberInput
            value={config.dataCount}
            onChange={(value) => setConfig(prev => ({ ...prev, dataCount: value }))}
            label="데이터 개수"
            min={1}
            max={100000}
            unit="개"
            placeholder="생성할 데이터 개수를 입력하세요 (1~100,000)"
          />
          <Select
            value={config.selectedEquipment}
            onChange={handleEquipmentChange}
            options={equipmentOptions.map(eq => ({ value: eq, label: equipmentSensorMap[eq as keyof typeof equipmentSensorMap].name }))}
            label="설비 선택"
          />
          <MultiSelect
            options={equipmentSensorMap[config.selectedEquipment as keyof typeof equipmentSensorMap]?.sensors || []}
            value={config.selectedSensors}
            onChange={(value) => setConfig(prev => ({ ...prev, selectedSensors: value }))}
            label="센서 선택"
            placeholder="센서를 선택하세요"
          />
        </div>

        <Select
          value={config.collectionInterval}
          onChange={(value) => setConfig(prev => ({ ...prev, collectionInterval: value }))}
          options={["1초", "5초", "10초", "30초", "1분"]}
          label="데이터 수집 간격"
        />

        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-medium text-foreground mb-4 flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            수집 시작 일정
          </h4>
          <div className="grid grid-cols-1 gap-4">
            <DateInput
              value={config.workDateStart}
              onChange={(value) => setConfig(prev => ({ ...prev, workDateStart: value }))}
              label="수집 시작 날짜"
            />
          </div>
        </div>

        <Select
          value={config.shiftType}
          onChange={(value) => setConfig(prev => ({ ...prev, shiftType: value }))}
          options={["주간(08:00-16:00)", "야간(22:00-06:00)", "전체(24시간)", "사용자 정의"]}
          label="시간대 설정"
        />

        {config.shiftType === "사용자 정의" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TimeInput
              value={config.customShiftStart || "08:00"}
              onChange={(value) => setConfig(prev => ({ ...prev, customShiftStart: value }))}
              label="수집 시작 시간"
            />
            <TimeInput
              value={config.customShiftEnd || "16:00"}
              onChange={(value) => setConfig(prev => ({ ...prev, customShiftEnd: value }))}
              label="수집 종료 시간"
            />
          </div>
        )}
      </Expander>

      {/* 센서 값 범위 */}
      <Expander title="센서 값 범위" icon={<TrendingUp className="w-5 h-5 text-accent-cyan" />}>
        <div className="space-y-4">
          {config.selectedSensors.map(sensorType => {
            const getSensorRangeProps = (type: string) => {
              switch (type) {
                // 건조기 센서
                case 'outlet_humidity':
                  return { min: 20.0, max: 100.0, step: 1.0, unit: '%' }
                case 'inlet_humidity':
                  return { min: 0.0, max: 30.0, step: 0.5, unit: '%' }
                case 'drying_temperature':
                  return { min: 50.0, max: 250.0, step: 1.0, unit: '°C' }
                case 'air_flow':
                  return { min: 500, max: 8000, step: 100, unit: 'm³/h' }
                case 'pressure_diff':
                  return { min: 10, max: 1000, step: 10, unit: 'Pa' }
                case 'moisture_content':
                  return { min: 0.0, max: 1.0, step: 0.01, unit: 'wt%' }
                case 'residence_time':
                  return { min: 200.0, max: 300.0, step: 1.0, unit: 's' }
                // 분급기 센서
                case 'mill_rpm':
                  return { min: 50, max: 1200, step: 10, unit: 'RPM' }
                case 'crushing_pressure':
                  return { min: 1.0, max: 15.0, step: 0.1, unit: 'MPa' }
                case 'classifier_speed':
                  return { min: 200, max: 2000, step: 50, unit: 'RPM' }
                case 'vacuum_pressure':
                  return { min: 0.05, max: 1.0, step: 0.01, unit: 'MPa' }
                case 'particle_size':
                  return { min: 5, max: 150, step: 1, unit: 'μm' }
                case 'particle_d50':
                  return { min: 5.0, max: 25.0, step: 0.1, unit: 'μm' }
                // 펌프 센서
                case 'flow_rate':
                  return { min: 5, max: 300, step: 5, unit: 'L/min' }
                case 'discharge_pressure':
                  return { min: 1.0, max: 20.0, step: 0.1, unit: 'MPa' }
                case 'suction_pressure':
                  return { min: 0.1, max: 5.0, step: 0.1, unit: 'MPa' }
                case 'vibration':
                  return { min: 0.1, max: 10.0, step: 0.1, unit: 'mm/s' }
                case 'temperature':
                  return { min: 10.0, max: 100.0, step: 1.0, unit: '°C' }
                // 컴프레서 센서
                case 'discharge_temperature':
                  return { min: 40.0, max: 200.0, step: 1.0, unit: '°C' }
                case 'current':
                  return { min: 5.0, max: 150.0, step: 1.0, unit: 'A' }
                // 모터 센서
                case 'rpm':
                  return { min: 300, max: 4000, step: 50, unit: 'RPM' }
                case 'torque':
                  return { min: 20, max: 800, step: 10, unit: 'Nm' }
                // 보일러 센서
                case 'steam_pressure':
                  return { min: 3.0, max: 30.0, step: 0.5, unit: 'MPa' }
                case 'steam_temperature':
                  return { min: 120.0, max: 350.0, step: 5.0, unit: '°C' }
                case 'feed_water_temp':
                  return { min: 60.0, max: 200.0, step: 5.0, unit: '°C' }
                case 'fuel_pressure':
                  return { min: 0.5, max: 8.0, step: 0.1, unit: 'MPa' }
                case 'oxygen_level':
                  return { min: 1.0, max: 12.0, step: 0.1, unit: '%' }
                default:
                  return { min: 0.0, max: 100.0, step: 1.0, unit: '' }
              }
            }
            
            const rangeProps = getSensorRangeProps(sensorType)
            const currentRange = config.sensorRanges[sensorType] || [rangeProps.min, rangeProps.max]
            
            return (
              <RangeSlider
                key={sensorType}
                min={rangeProps.min}
                max={rangeProps.max}
                step={rangeProps.step}
                value={currentRange}
                onChange={(value) => setConfig(prev => ({
                  ...prev,
                  sensorRanges: {
                    ...prev.sensorRanges,
                    [sensorType]: value
                  }
                }))}
                label={`${getSensorLabel(sensorType)} 범위`}
                unit={rangeProps.unit}
              />
            )
          })}
          {config.selectedSensors.length === 0 && (
            <div className="text-center text-muted-foreground py-4">
              센서를 선택하면 범위 설정이 표시됩니다.
            </div>
          )}
        </div>
      </Expander>

      {/* 시뮬레이션 옵션 */}
      <Expander title="시뮬레이션 옵션" icon={<Sliders className="w-5 h-5 text-accent-orange" />}>
        <div className="space-y-4">
          <Checkbox
            checked={config.addNoise}
            onChange={(checked) => setConfig(prev => ({ ...prev, addNoise: checked }))}
            label="노이즈 추가"
          />
          
          {config.addNoise && (
            <Slider
              min={0.1}
              max={5.0}
              step={0.1}
              value={config.noiseLevel}
              onChange={(value) => setConfig(prev => ({ ...prev, noiseLevel: value }))}
              label="노이즈 레벨"
            />
          )}

          <Checkbox
            checked={config.addAnomalies}
            onChange={(checked) => setConfig(prev => ({ ...prev, addAnomalies: checked }))}
            label="이상치 추가"
          />

          {config.addAnomalies && (
            <Slider
              min={1}
              max={10}
              value={config.anomalyRatio}
              onChange={(value) => setConfig(prev => ({ ...prev, anomalyRatio: value }))}
              label="이상치 비율"
              unit="%"
            />
          )}

          <Checkbox
            checked={config.addMissingData}
            onChange={(checked) => setConfig(prev => ({ ...prev, addMissingData: checked }))}
            label="결측치 추가"
          />

          {config.addMissingData && (
            <Slider
              min={1}
              max={30}
              value={config.missingDataRatio}
              onChange={(value) => setConfig(prev => ({ ...prev, missingDataRatio: value }))}
              label="결측치 비율"
              unit="%"
            />
          )}

          <Select
            value={config.dataPattern}
            onChange={(value) => setConfig(prev => ({ ...prev, dataPattern: value }))}
            options={["정상", "증가 추세", "감소 추세", "주기적 변동", "계단식 변화", "급격한 변화"]}
            label="데이터 패턴"
          />

          <Slider
            min={1}
            max={10}
            value={config.variationIntensity}
            onChange={(value) => setConfig(prev => ({ ...prev, variationIntensity: value }))}
            label="변동폭 강도"
            unit=""
          />
        </div>
      </Expander>

      {/* 생성 버튼 */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="w-full flex items-center justify-center px-6 py-4 bg-gradient-primary hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-glass-lg transition-all duration-300 shadow-glow disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            센서 데이터 생성 중...
          </>
        ) : (
          <>
            <Play className="w-5 h-5 mr-2" />
            센서 데이터 생성
          </>
        )}
      </button>
    </div>
  )
}

// ============================
// 실험 데이터 설정 컴포넌트
// ============================

function ExperimentalDataConfig({ onGenerate, isGenerating }: { onGenerate: (type: string, config: unknown) => void, isGenerating: boolean }) {
  const { t } = useTranslation()
  const [config, setConfig] = useState<ExperimentalConfig>({
    experimentType: "Full Factorial",
    selectedFactors: ["온도", "압력", "pH"],
    levels: 3,
    replications: 2,
    numExperiments: 25,
    factorRanges: {
      "온도": [150, 200],
      "압력": [1.5, 3.0],
      "pH": [6.5, 8.5],
      "반응시간": [60, 180],
      "촉매농도": [200, 500],
      "교반속도": [200, 600],
      "원료농도": [0.5, 1.5]
    },
    experimentDateStart: new Date().toISOString().split('T')[0],
    experimentDateEnd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    experimentShiftType: "일반 실험시간(09:00-17:00)",
    experimentInterval: "동시 수행",
    experimenter: "연구원A",
    experimentPurpose: "공정 조건 최적화를 위한 인자 스크리닝",
    experimentObjective: "순도 최대화"
  })

  const availableFactors = ["온도", "압력", "pH", "반응시간", "촉매농도", "교반속도", "원료농도"]

  const handleGenerate = () => {
    onGenerate('experimental', config)
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-foreground flex items-center">
        <Beaker className="w-6 h-6 mr-2 text-accent-blue" />
        {t('dataGeneration.experimental.title')}
      </h3>

      {/* 실험 설계 */}
      <Expander title={t('dataGeneration.experimental.experimentDesign')} defaultExpanded={true}>
        <div className="space-y-4">
          <Select
            value={config.experimentType}
            onChange={(value) => setConfig(prev => ({ ...prev, experimentType: value }))}
            options={["Full Factorial", "Fractional Factorial", "Central Composite", "Box-Behnken", "Custom"]}
            label="실험 설계 방법"
          />

          <MultiSelect
            value={config.selectedFactors}
            onChange={(value) => setConfig(prev => ({ ...prev, selectedFactors: value }))}
            options={availableFactors}
            label="실험 인자 선택"
          />

          {config.experimentType === "Full Factorial" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Slider
                min={2}
                max={5}
                value={config.levels}
                onChange={(value) => setConfig(prev => ({ ...prev, levels: value }))}
                label="수준 수"
              />
              <Slider
                min={1}
                max={5}
                value={config.replications}
                onChange={(value) => setConfig(prev => ({ ...prev, replications: value }))}
                label="반복 횟수"
              />
            </div>
          )}

          {config.experimentType === "Fractional Factorial" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Slider
                min={2}
                max={3}
                value={config.levels}
                onChange={(value) => setConfig(prev => ({ ...prev, levels: value }))}
                label="수준 수"
              />
              <Select
                value="1/2"
                onChange={() => {}}
                options={["1/2", "1/4", "1/8"]}
                label="분수 설계"
              />
              <Slider
                min={1}
                max={3}
                value={config.replications}
                onChange={(value) => setConfig(prev => ({ ...prev, replications: value }))}
                label="반복 횟수"
              />
            </div>
          )}

          {(config.experimentType === "Central Composite" || config.experimentType === "Box-Behnken" || config.experimentType === "Custom") && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Slider
                min={10}
                max={100}
                value={config.numExperiments}
                onChange={(value) => setConfig(prev => ({ ...prev, numExperiments: value }))}
                label="실험 횟수"
              />
              <Slider
                min={1}
                max={3}
                value={config.replications}
                onChange={(value) => setConfig(prev => ({ ...prev, replications: value }))}
                label="반복 횟수"
              />
            </div>
          )}
        </div>
      </Expander>

      {/* 실험 조건 설정 */}
      <Expander title={t('dataGeneration.experimental.conditionSettings')} icon={<Settings className="w-5 h-5 text-accent-purple" />}>
        <div className="space-y-4">
          {config.selectedFactors.map((factor) => (
            <div key={factor}>
              {factor === "온도" && (
                <RangeSlider
                  min={120}
                  max={250}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위 (°C)`}
                  unit="°C"
                />
              )}
              {factor === "압력" && (
                <RangeSlider
                  min={1.0}
                  max={5.0}
                  step={0.1}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위 (bar)`}
                  unit="bar"
                />
              )}
              {factor === "pH" && (
                <RangeSlider
                  min={5.0}
                  max={9.0}
                  step={0.1}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위`}
                />
              )}
              {factor === "반응시간" && (
                <RangeSlider
                  min={30}
                  max={300}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위 (분)`}
                  unit="분"
                />
              )}
              {factor === "촉매농도" && (
                <RangeSlider
                  min={100}
                  max={1000}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위 (ppm)`}
                  unit="ppm"
                />
              )}
              {factor === "교반속도" && (
                <RangeSlider
                  min={100}
                  max={1000}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위 (rpm)`}
                  unit="rpm"
                />
              )}
              {factor === "원료농도" && (
                <RangeSlider
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  value={config.factorRanges[factor] as [number, number]}
                  onChange={(value) => setConfig(prev => ({ 
                    ...prev, 
                    factorRanges: { ...prev.factorRanges, [factor]: value }
                  }))}
                  label={`${factor} 범위 (M)`}
                  unit="M"
                />
              )}
            </div>
          ))}
        </div>
      </Expander>

      {/* 실험 일자 설정 */}
      <Expander title={t('dataGeneration.experimental.scheduleSettings')} icon={<Calendar className="w-5 h-5 text-accent-cyan" />}>
        <div className="space-y-4">
                      <h4 className="text-sm font-medium text-muted-foreground">{t('dataGeneration.experimental.scheduleTitle')}</h4>  
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DateInput
              value={config.experimentDateStart}
              onChange={(value) => setConfig(prev => ({ ...prev, experimentDateStart: value }))}
              label="실험 시작 날짜"
              max={new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
            />
            <DateInput
              value={config.experimentDateEnd}
              onChange={(value) => setConfig(prev => ({ ...prev, experimentDateEnd: value }))}
              label="실험 종료 날짜"
              min={config.experimentDateStart}
              max={new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
            />
          </div>

          <Select
            value={config.experimentShiftType}
            onChange={(value) => setConfig(prev => ({ ...prev, experimentShiftType: value }))}
            options={["일반 실험시간(09:00-17:00)", "연장 실험시간(09:00-21:00)", "24시간 연속실험", "사용자 정의"]}
            label="실험 시간대 설정"
          />

          <Select
            value={config.experimentInterval}
            onChange={(value) => setConfig(prev => ({ ...prev, experimentInterval: value }))}
            options={["동시 수행", "1시간 간격", "2시간 간격", "4시간 간격", "일별 수행", "사용자 정의"]}
            label="실험 간격"
          />
        </div>
      </Expander>

      {/* 실험 메타데이터 */}
      <Expander title={t('dataGeneration.experimental.metadata')} icon={<Info className="w-5 h-5 text-accent-pink" />}>
        <div className="space-y-4">
          <TextInput
            value={config.experimenter}
            onChange={(value) => setConfig(prev => ({ ...prev, experimenter: value }))}
            label="실험자"
            placeholder="연구원A"
          />
          <TextArea
            value={config.experimentPurpose}
            onChange={(value) => setConfig(prev => ({ ...prev, experimentPurpose: value }))}
            label="실험 목적"
            placeholder="공정 조건 최적화를 위한 인자 스크리닝"
          />
          <Select
            value={config.experimentObjective}
            onChange={(value) => setConfig(prev => ({ ...prev, experimentObjective: value }))}
            options={["순도 최대화", "수율 최대화", "비용 최소화", "다목적 최적화"]}
            label="실험 목표"
          />
        </div>
      </Expander>

      {/* 생성 버튼 */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="w-full flex items-center justify-center px-6 py-4 bg-gradient-primary hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-glass-lg transition-all duration-300 shadow-glow disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            실험 계획 생성 중...
          </>
        ) : (
          <>
            <FlaskConical className="w-5 h-5 mr-2" />
            실험 계획 생성
          </>
        )}
      </button>
    </div>
  )
}

// ============================
// 원가/생산 이력 데이터 설정 컴포넌트
// ============================

function CostDataConfig({ onGenerate, isGenerating }: { onGenerate: (type: string, config: unknown) => void, isGenerating: boolean }) {
  const { t } = useTranslation()
  const [config, setConfig] = useState<CostConfig>({
    recordCount: 1000,
    startDate: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    productGrade: "Standard",
    purityRange: [92.0, 96.0],
    yieldRange: [85.0, 92.0],
    materialARage: [80.0, 120.0],
    materialACost: 450,
    materialBRange: [40.0, 60.0],
    materialBCost: 720,
    catalystRange: [3.0, 8.0],
    catalystCost: 18000,
    tempRange: [160, 190],
    pressureRange: [2.0, 3.0],
    flowRange: [180, 220],
    steamRange: [120, 180],
    steamCost: 50,
    electricityRange: [60, 100],
    electricityCost: 120,
    coolingRange: [400, 600],
    coolingCost: 5,
    priceVolatility: 10,
    utilityVolatility: 5,
    seasonalEffect: true,
    correlationStrength: 0.7,
    noiseLevel: 2.0,
    includeShifts: true,
    includeEquipmentWear: true
  })

  const handleProductGradeChange = (grade: string) => {
    let purityRange: [number, number]
    let yieldRange: [number, number]

    switch (grade) {
      case "Premium":
        purityRange = [96.0, 99.0]
        yieldRange = [88.0, 95.0]
        break
      case "Standard":
        purityRange = [92.0, 96.0]
        yieldRange = [85.0, 92.0]
        break
      case "Economy":
        purityRange = [88.0, 93.0]
        yieldRange = [82.0, 89.0]
        break
      default: // Mixed
        purityRange = [88.0, 99.0]
        yieldRange = [82.0, 95.0]
    }

    setConfig(prev => ({ 
      ...prev, 
      productGrade: grade,
      purityRange,
      yieldRange
    }))
  }

  const handleGenerate = () => {
    onGenerate('cost_production', config)
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-foreground flex items-center">
        <DollarSign className="w-6 h-6 mr-2 text-accent-blue" />
        {t('dataGeneration.cost.title')}
      </h3>
      <p className="text-muted-foreground text-sm">
        **{t('dataGeneration.cost.description')}**
      </p>

      {/* 기본 파라미터 */}
      <Expander title={t('dataGeneration.cost.basicParams')} defaultExpanded={true}>
        <div className="space-y-4">
          <Slider
            min={100}
            max={10000}
            step={100}
            value={config.recordCount}
            onChange={(value) => setConfig(prev => ({ ...prev, recordCount: value }))}
            label={t('dataGeneration.cost.productionRecords')}
          />

          <div className="border-t border-white/10 pt-4">
            <h4 className="text-sm font-medium text-muted-foreground mb-4">**{t('dataGeneration.cost.productionPeriod')}**</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DateInput
                value={config.startDate}
                onChange={(value) => setConfig(prev => ({ ...prev, startDate: value }))}
                label={t('dataGeneration.cost.startDate')}
                max={new Date().toISOString().split('T')[0]}
              />
              <DateInput
                value={config.endDate}
                onChange={(value) => setConfig(prev => ({ ...prev, endDate: value }))}
                label={t('dataGeneration.cost.endDate')}
                min={config.startDate}
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>
        </div>
      </Expander>

      {/* 제품 및 품질 설정 */}
      <Expander title="제품 및 품질 설정" icon={<TrendingUp className="w-5 h-5 text-accent-cyan" />}>
        <div className="space-y-4">
          <Select
            value={config.productGrade}
            onChange={handleProductGradeChange}
            options={["Premium", "Standard", "Economy", "Mixed"]}
            label="제품 그레이드"
          />

          <div className="p-4 bg-glass-50 rounded-glass border border-white/10">
            <p className="text-sm text-muted-foreground">
              순도 목표: {config.purityRange[0]}% - {config.purityRange[1]}%
            </p>
            <p className="text-sm text-muted-foreground">
              수율 목표: {config.yieldRange[0]}% - {config.yieldRange[1]}%
            </p>
          </div>

          <Checkbox
            checked={false}
            onChange={() => {}}
            label="사용자 정의 품질 범위"
          />
        </div>
      </Expander>

      {/* 원료 및 투입량 설정 */}
      <Expander title="원료 및 투입량 설정" icon={<Database className="w-5 h-5 text-accent-orange" />}>
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">**원료 A (주원료)**</h4>
            <div className="space-y-3">
              <RangeSlider
                min={50.0}
                max={200.0}
                step={5.0}
                value={config.materialARage}
                onChange={(value) => setConfig(prev => ({ ...prev, materialARage: value }))}
                label="원료 A 사용량 (kg/h)"
                unit="kg/h"
              />
              <NumberInput
                value={config.materialACost}
                onChange={(value) => setConfig(prev => ({ ...prev, materialACost: value }))}
                label="원료 A 단가 (원/kg)"
                min={100}
                max={1000}
                step={10}
                unit="원/kg"
              />
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">**원료 B (부원료)**</h4>
            <div className="space-y-3">
              <RangeSlider
                min={20.0}
                max={100.0}
                step={2.5}
                value={config.materialBRange}
                onChange={(value) => setConfig(prev => ({ ...prev, materialBRange: value }))}
                label="원료 B 사용량 (kg/h)"
                unit="kg/h"
              />
              <NumberInput
                value={config.materialBCost}
                onChange={(value) => setConfig(prev => ({ ...prev, materialBCost: value }))}
                label="원료 B 단가 (원/kg)"
                min={200}
                max={1500}
                step={20}
                unit="원/kg"
              />
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">**촉매**</h4>
            <div className="space-y-3">
              <RangeSlider
                min={1.0}
                max={20.0}
                step={0.5}
                value={config.catalystRange}
                onChange={(value) => setConfig(prev => ({ ...prev, catalystRange: value }))}
                label="촉매 사용량 (kg/h)"
                unit="kg/h"
              />
              <NumberInput
                value={config.catalystCost}
                onChange={(value) => setConfig(prev => ({ ...prev, catalystCost: value }))}
                label="촉매 단가 (원/kg)"
                min={5000}
                max={50000}
                step={500}
                unit="원/kg"
              />
            </div>
          </div>
        </div>
      </Expander>

      {/* 운전 조건 설정 */}
      <Expander title="운전 조건 설정" icon={<Settings className="w-5 h-5 text-accent-purple" />}>
        <div className="space-y-4">
          <RangeSlider
            min={100}
            max={250}
            step={5}
            value={config.tempRange}
            onChange={(value) => setConfig(prev => ({ ...prev, tempRange: value }))}
            label="온도 범위 (°C)"
            unit="°C"
          />
          <RangeSlider
            min={1.0}
            max={5.0}
            step={0.1}
            value={config.pressureRange}
            onChange={(value) => setConfig(prev => ({ ...prev, pressureRange: value }))}
            label="압력 범위 (bar)"
            unit="bar"
          />
          <RangeSlider
            min={100}
            max={400}
            step={10}
            value={config.flowRange}
            onChange={(value) => setConfig(prev => ({ ...prev, flowRange: value }))}
            label="유량 범위 (L/h)"
            unit="L/h"
          />
        </div>
      </Expander>

      {/* 유틸리티 설정 */}
      <Expander title="유틸리티 설정" icon={<Zap className="w-5 h-5 text-accent-pink" />}>
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">**스팀**</h4>
            <div className="space-y-3">
              <RangeSlider
                min={50}
                max={300}
                step={10}
                value={config.steamRange}
                onChange={(value) => setConfig(prev => ({ ...prev, steamRange: value }))}
                label="스팀 사용량 (kg/h)"
                unit="kg/h"
              />
              <NumberInput
                value={config.steamCost}
                onChange={(value) => setConfig(prev => ({ ...prev, steamCost: value }))}
                label="스팀 단가 (원/kg)"
                min={20}
                max={100}
                step={5}
                unit="원/kg"
              />
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">**전력**</h4>
            <div className="space-y-3">
              <RangeSlider
                min={30}
                max={150}
                step={5}
                value={config.electricityRange}
                onChange={(value) => setConfig(prev => ({ ...prev, electricityRange: value }))}
                label="전력 사용량 (kWh)"
                unit="kWh"
              />
              <NumberInput
                value={config.electricityCost}
                onChange={(value) => setConfig(prev => ({ ...prev, electricityCost: value }))}
                label="전력 단가 (원/kWh)"
                min={50}
                max={200}
                step={10}
                unit="원/kWh"
              />
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">**냉각수**</h4>
            <div className="space-y-3">
              <RangeSlider
                min={200}
                max={1000}
                step={25}
                value={config.coolingRange}
                onChange={(value) => setConfig(prev => ({ ...prev, coolingRange: value }))}
                label="냉각수 사용량 (L/h)"
                unit="L/h"
              />
              <NumberInput
                value={config.coolingCost}
                onChange={(value) => setConfig(prev => ({ ...prev, coolingCost: value }))}
                label="냉각수 단가 (원/L)"
                min={1}
                max={20}
                step={1}
                unit="원/L"
              />
            </div>
          </div>
        </div>
      </Expander>

      {/* 시장 변동성 설정 */}
      <Expander title="시장 변동성 설정" icon={<TrendingUp className="w-5 h-5 text-accent-cyan" />}>
        <div className="space-y-4">
          <Slider
            min={0}
            max={30}
            value={config.priceVolatility}
            onChange={(value) => setConfig(prev => ({ ...prev, priceVolatility: value }))}
            label="원료 가격 변동성 (%)"
            unit="%"
          />
          <Slider
            min={0}
            max={20}
            value={config.utilityVolatility}
            onChange={(value) => setConfig(prev => ({ ...prev, utilityVolatility: value }))}
            label="유틸리티 가격 변동성 (%)"
            unit="%"
          />
          <Checkbox
            checked={config.seasonalEffect}
            onChange={(checked) => setConfig(prev => ({ ...prev, seasonalEffect: checked }))}
            label="계절별 효과 적용"
          />
        </div>
      </Expander>

      {/* 고급 설정 */}
      <Expander title="고급 설정" icon={<Beaker className="w-5 h-5 text-accent-orange" />}>
        <div className="space-y-4">
          <Slider
            min={0.3}
            max={0.9}
            step={0.05}
            value={config.correlationStrength}
            onChange={(value) => setConfig(prev => ({ ...prev, correlationStrength: value }))}
            label="투입량-품질 상관관계 강도"
          />
          <Slider
            min={0.5}
            max={5.0}
            step={0.1}
            value={config.noiseLevel}
            onChange={(value) => setConfig(prev => ({ ...prev, noiseLevel: value }))}
            label="데이터 노이즈 수준"
          />
          <Checkbox
            checked={config.includeShifts}
            onChange={(checked) => setConfig(prev => ({ ...prev, includeShifts: checked }))}
            label="교대 근무 효과 포함"
          />
          <Checkbox
            checked={config.includeEquipmentWear}
            onChange={(checked) => setConfig(prev => ({ ...prev, includeEquipmentWear: checked }))}
            label="설비 마모 효과 포함"
          />
        </div>
      </Expander>

      {/* 생성 버튼 */}
      <button
        onClick={handleGenerate}
        disabled={isGenerating}
        className="w-full flex items-center justify-center px-6 py-4 bg-gradient-primary hover:opacity-90 disabled:opacity-50 text-white font-semibold rounded-glass-lg transition-all duration-300 shadow-glow disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            {t('dataGeneration.cost.generating')}
          </>
        ) : (
          <>
            <DollarSign className="w-5 h-5 mr-2" />
            {t('dataGeneration.cost.generate')}
          </>
        )}
      </button>
    </div>
  )
}

// ============================
// 정보 패널 컴포넌트
// ============================

function InfoPanel({ activeTab }: { activeTab: number }) {
  const { t } = useTranslation()
  
  const getInfo = () => {
    switch (activeTab) {
      case 0:
        return {
          title: t('dataGeneration.info.production.title'),
          content: t('dataGeneration.info.production.content')
        }
      case 1:
        return {
          title: '센서 데이터 생성',
          content: ['IoT 센서에서 수집되는 실시간 데이터를 시뮬레이션합니다.', 
                   '온도, 습도, 압력, 진동 등의 센서 값을 생성하며, 실제 산업 환경의 센서 데이터 패턴을 반영합니다.', 
                   '디바이스별 센서 ID 관리 및 시간대별 데이터 수집 패턴을 지원합니다.']
        }
      case 2:
        return {
          title: t('dataGeneration.info.experimental.title'),
          content: t('dataGeneration.info.experimental.content')
        }
      case 3:
        return {
          title: t('dataGeneration.info.cost.title'),
          content: t('dataGeneration.info.cost.content')
        }
      default:
        return { title: "", content: [] }
    }
  }

  const info = getInfo()

  // 배열을 마크다운 문자열로 변환
  const contentToMarkdown = (content: any): string => {
    if (Array.isArray(content)) {
      return content.join('\n\n')
    }
    return typeof content === 'string' ? content : ''
  }

  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-foreground mb-4">{info.title}</h3>
      <div className="text-sm text-muted-foreground">
        <MarkdownRenderer content={contentToMarkdown(info.content)} />
      </div>
    </div>
  )
}

// ============================
// 결과 패널 컴포넌트
// ============================

function ResultPanel({ result }: { result: GenerationResult }) {
  const [lotResult, setLotResult] = useState<any>(null)
  const [isGeneratingLot, setIsGeneratingLot] = useState(false)

  const downloadCSV = () => {
    if (!result.data || !Array.isArray(result.data) || result.data.length === 0) return

    try {
      // 첫 번째 데이터 항목의 키를 기반으로 헤더 생성
      const firstRow = result.data[0]
      const headers = Object.keys(firstRow)
      
      const csvContent = "data:text/csv;charset=utf-8," + 
        headers.join(",") + "\n" +
        result.data.map(row => 
          headers.map(header => {
            const value = row[header]
            if (typeof value === 'number') {
              return value.toString()
            }
            return `"${String(value).replace(/"/g, '""')}"` // CSV 이스케이핑
          }).join(",")
        ).join("\n")

      const encodedUri = encodeURI(csvContent)
      const link = document.createElement("a")
      link.setAttribute("href", encodedUri)
      link.setAttribute("download", result.filename || "data.csv")
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('CSV 다운로드 실패:', error)
      alert('CSV 다운로드에 실패했습니다.')
    }
  }

  const generateLotNumbers = async () => {
    if (!result.filename) return

    setIsGeneratingLot(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/data/generate/lot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: result.filename
        })
      })

      if (!response.ok) {
        throw new Error(`LOT 생성 실패: ${response.statusText}`)
      }

      const lotData = await response.json()
      setLotResult(lotData)
    } catch (error) {
      console.error('LOT 생성 실패:', error)
      alert('LOT 생성에 실패했습니다.')
    } finally {
      setIsGeneratingLot(false)
    }
  }

  const downloadLotCSV = async () => {
    if (!lotResult || !lotResult.filename) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/data/download/${lotResult.filename}`)
      if (!response.ok) {
        throw new Error('파일 다운로드 실패')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = lotResult.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('LOT 파일 다운로드 실패:', error)
      alert('LOT 파일 다운로드에 실패했습니다.')
    }
  }

  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground flex items-center">
          {result.success ? (
            <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
          ) : (
            <AlertCircle className="w-5 h-5 mr-2 text-red-400" />
          )}
          생성 결과
        </h3>
        {result.success && result.data && Array.isArray(result.data) && result.data.length > 0 && (
          <button
            onClick={downloadCSV}
            className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 text-white rounded-lg text-sm transition-colors"
          >
            <Download className="w-4 h-4 mr-2" />
            CSV 다운로드
          </button>
        )}
      </div>

      <div className={`p-4 rounded-lg ${result.success ? 'bg-green-400/10 border border-green-400/20' : 'bg-red-400/10 border border-red-400/20'}`}>
        <p className={`text-sm ${result.success ? 'text-green-300' : 'text-red-300'}`}>
          {result.message}
        </p>
      </div>

      {result.success && result.summary && (
        <>
          {/* 센서 데이터인 경우 */}
          {result.summary.sensorTypes && Array.isArray(result.summary.sensorTypes) ? (
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="bg-muted/50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-foreground">
                  {result.summary.totalLots ? result.summary.totalLots.toLocaleString() : '0'}
                </div>
                <div className="text-sm text-muted-foreground">총 LOT 수</div>
              </div>
              {result.summary.sensorTypes.slice(0, 3).map((sensor, index) => {
                const getSensorDisplayName = (name: string) => {
                  // 건조기 센서
                  if (name === '출구습도_%') return '출구습도 (%)'
                  if (name === '입구습도_%') return '입구습도 (%)'
                  if (name === '건조온도_C') return '건조온도 (°C)'
                  if (name === '풍량_m3h') return '풍량 (m³/h)'
                  if (name === '압력차_Pa') return '압력차 (Pa)'
                  if (name === '수분값_wt%') return '수분값 (wt%)'
                  if (name === '체류시간_s') return '체류시간 (s)'
                  // 분급기 센서
                  if (name === '밀회전속도_RPM') return '밀 회전속도 (RPM)'
                  if (name === '분쇄압력_MPa') return '분쇄압력 (MPa)'
                  if (name === '분급기속도_RPM') return '분급기 속도 (RPM)'
                  if (name === '진공압_MPa') return '진공압 (MPa)'
                  if (name === '입자크기_um') return '입자크기 (μm)'
                  if (name === '입도D50_um') return '입도 D50 (μm)'
                  // 펌프 센서
                  if (name === '유량_Lmin') return '유량 (L/min)'
                  if (name === '토출압력_MPa') return '토출압력 (MPa)'
                  if (name === '흡입압력_MPa') return '흡입압력 (MPa)'
                  if (name === '진동_mms') return '진동 (mm/s)'
                  if (name === '온도_C') return '온도 (°C)'
                  // 컴프레서 센서
                  if (name === '토출온도_C') return '토출온도 (°C)'
                  if (name === '전류_A') return '전류 (A)'
                  // 모터 센서
                  if (name === '회전속도_RPM') return '회전속도 (RPM)'
                  if (name === '토크_Nm') return '토크 (Nm)'
                  // 보일러 센서
                  if (name === '증기압력_MPa') return '증기압력 (MPa)'
                  if (name === '증기온도_C') return '증기온도 (°C)'
                  if (name === '급수온도_C') return '급수온도 (°C)'
                  if (name === '연료압력_MPa') return '연료압력 (MPa)'
                  if (name === '산소농도_%') return '산소농도 (%)'
                  return name
                }
                
                return (
                  <div key={index} className="bg-glass-50 p-3 rounded-glass">
                    <div className="text-2xl font-bold text-foreground">
                      {sensor.average.toFixed(2)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      평균 {getSensorDisplayName(sensor.name)}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            /* 기존 생산/실험/원가 데이터인 경우 */
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="bg-muted/50 p-3 rounded-lg">
                <div className="text-2xl font-bold text-foreground">
                  {result.summary.totalRecords ? result.summary.totalRecords.toLocaleString() : '0'}
                </div>
                <div className="text-sm text-muted-foreground">총 레코드 수</div>
              </div>
              <div className="bg-glass-50 p-3 rounded-glass">
                <div className="text-2xl font-bold text-foreground">
                  {result.summary.averagePurity ? `${result.summary.averagePurity.toFixed(1)}%` : 'N/A'}
                </div>
                <div className="text-sm text-muted-foreground">평균 순도</div>
              </div>
              <div className="bg-glass-50 p-3 rounded-glass">
                <div className="text-2xl font-bold text-foreground">
                  {result.summary.averageYield ? `${result.summary.averageYield.toFixed(1)}%` : 'N/A'}
                </div>
                <div className="text-sm text-muted-foreground">평균 수율</div>
              </div>
              <div className="bg-glass-50 p-3 rounded-glass">
                <div className="text-2xl font-bold text-foreground">
                  {result.summary.averageCost ? `${result.summary.averageCost.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}원` : 'N/A'}
                </div>
                <div className="text-sm text-muted-foreground">평균 총 비용</div>
              </div>
            </div>
          )}

          {result.data && Array.isArray(result.data) && result.data.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-muted-foreground mb-3">데이터 미리보기</h4>
              <div className="bg-glass-50 rounded-glass overflow-hidden">
                {(() => {
                  const firstRow = result.data[0]
                  const headers = Object.keys(firstRow)
                  
                  return (
                    <>
                      <div className="grid gap-4 p-3 bg-glass-100 text-sm font-medium text-muted-foreground" style={{ gridTemplateColumns: `repeat(${headers.length}, 1fr)` }}>
                        {headers.map((header, index) => (
                          <div key={index}>{header}</div>
                        ))}
                      </div>
                      {result.data.slice(0, 5).map((row, rowIndex) => (
                        <div key={rowIndex} className="grid gap-4 p-3 border-t border-white/10 text-sm text-muted-foreground" style={{ gridTemplateColumns: `repeat(${headers.length}, 1fr)` }}>
                          {headers.map((header, cellIndex) => {
                            const value = row[header]
                            let displayValue = String(value)
                            
                            // 특별한 포맷팅
                            if (header === 'timestamp' || header.includes('date')) {
                              try {
                                displayValue = new Date(value).toLocaleString('ko-KR', { 
                                  month: '2-digit', 
                                  day: '2-digit', 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })
                              } catch {
                                displayValue = String(value)
                              }
                            } else if (typeof value === 'number') {
                              if (header.includes('purity') || header.includes('yield') || header.includes('Purity') || header.includes('Yield')) {
                                displayValue = value.toFixed(1)
                              } else if (header.includes('cost') || header.includes('Cost') || header.includes('total')) {
                                displayValue = value.toLocaleString('ko-KR', { maximumFractionDigits: 0 })
                              } else {
                                displayValue = value.toLocaleString('ko-KR')
                              }
                            }
                            
                            return (
                              <div key={cellIndex}>{displayValue}</div>
                            )
                          })}
                        </div>
                      ))}
                    </>
                  )
                })()}
              </div>
            </div>
          )}

          <div className="mt-4 p-3 bg-glass-50 rounded-glass">
            <p className="text-sm text-muted-foreground">
              파일이 서버에 저장되었습니다: `{result.filename || 'Unknown'}`
            </p>
            <p className="text-sm text-muted-foreground">
              총 {result.summary.totalRecords || result.summary.totalLots || 0} 개의 데이터 행이 생성되었습니다.
            </p>
          </div>

          {/* LOT 생성 섹션 */}
          <div className="mt-6 p-4 bg-gradient-to-r from-accent-blue/10 to-accent-cyan/10 rounded-glass border border-accent-blue/20">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-foreground flex items-center">
                <Factory className="w-5 h-5 mr-2 text-accent-blue" />
                LOT 관리
              </h4>
              <button
                onClick={generateLotNumbers}
                disabled={isGeneratingLot || !result.filename}
                className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              >
                {isGeneratingLot ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    LOT 생성 중...
                  </>
                ) : (
                  <>
                    <Activity className="w-4 h-4 mr-2" />
                    LOT 생성
                  </>
                )}
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              생성된 데이터를 8개씩 그룹으로 나누어 LOT 번호를 자동 생성합니다.
            </p>

            {/* LOT 생성 결과 */}
            {lotResult && (
              <div className="bg-card/50 backdrop-blur-sm rounded-glass p-4 border border-border/50">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                    <span className="font-medium text-foreground">LOT 생성 완료</span>
                  </div>
                  <button
                    onClick={downloadLotCSV}
                    className="flex items-center px-3 py-1.5 bg-accent-cyan hover:bg-accent-cyan/80 text-white rounded-lg text-sm transition-colors"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    LOT 파일 다운로드
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-glass-50 p-3 rounded-glass">
                    <div className="text-lg font-bold text-foreground">
                      {lotResult.total_lots || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">생성된 LOT 수</div>
                  </div>
                  <div className="bg-glass-50 p-3 rounded-glass">
                    <div className="text-lg font-bold text-foreground">
                      {lotResult.total_records || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">총 데이터 수</div>
                  </div>
                </div>

                <div className="bg-glass-50 rounded-glass p-3">
                  <h5 className="text-sm font-medium text-foreground mb-2">LOT 목록</h5>
                  <div className="max-h-32 overflow-y-auto">
                    <div className="grid grid-cols-1 gap-1 text-xs">
                      {lotResult.lot_summary?.slice(0, 10).map((lot: any, index: number) => (
                        <div key={index} className="flex justify-between items-center py-1 px-2 bg-glass-100 rounded">
                          <span className="font-mono text-muted-foreground">{lot.lot_number}</span>
                          <span className="text-muted-foreground">
                            #{lot.start_index}~{lot.end_index} ({lot.record_count}개)
                          </span>
                        </div>
                      ))}
                      {lotResult.lot_summary?.length > 10 && (
                        <div className="text-center py-1 text-muted-foreground">
                          ... 외 {lotResult.lot_summary.length - 10}개 LOT
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground mt-3">
                  LOT 파일: `{lotResult.filename}`
                </p>

                {/* LOT 데이터 미리보기 */}
                {lotResult.preview_data && lotResult.preview_data.length > 0 && (
                  <div className="mt-4 bg-card/30 rounded-glass p-3 border border-border/30">
                    <h5 className="text-sm font-medium text-foreground mb-3 flex items-center">
                      <Database className="w-4 h-4 mr-2 text-accent-cyan" />
                      LOT 데이터 미리보기 (처음 10행)
                    </h5>
                    <div className="overflow-x-auto">
                      <div className="bg-glass-50 rounded-glass overflow-hidden">
                        {(() => {
                          const firstRow = lotResult.preview_data[0]
                          const headers = Object.keys(firstRow)
                          
                          return (
                            <>
                              <div className="grid gap-2 p-2 bg-glass-100 text-xs font-medium text-muted-foreground" style={{ gridTemplateColumns: `repeat(${headers.length}, minmax(80px, 1fr))` }}>
                                {headers.map((header, index) => (
                                  <div key={index} className="truncate" title={header}>
                                    {header === 'lot_number' ? 'LOT 번호' : header}
                                  </div>
                                ))}
                              </div>
                              {lotResult.preview_data.slice(0, 10).map((row: any, rowIndex: number) => (
                                <div key={rowIndex} className="grid gap-2 p-2 border-t border-white/10 text-xs text-muted-foreground" style={{ gridTemplateColumns: `repeat(${headers.length}, minmax(80px, 1fr))` }}>
                                  {headers.map((header, cellIndex) => {
                                    const value = row[header]
                                    let displayValue = String(value)
                                    
                                    // 특별한 포맷팅
                                    if (header === 'timestamp' || header.includes('date')) {
                                      try {
                                        displayValue = new Date(value).toLocaleString('ko-KR', { 
                                          month: '2-digit', 
                                          day: '2-digit', 
                                          hour: '2-digit', 
                                          minute: '2-digit' 
                                        })
                                      } catch {
                                        displayValue = String(value)
                                      }
                                    } else if (typeof value === 'number' && header !== 'lot_number') {
                                      if (header.includes('purity') || header.includes('yield') || header.includes('Purity') || header.includes('Yield')) {
                                        displayValue = value.toFixed(1)
                                      } else if (header.includes('cost') || header.includes('Cost') || header.includes('total')) {
                                        displayValue = value.toLocaleString('ko-KR', { maximumFractionDigits: 0 })
                                      } else {
                                        displayValue = value.toLocaleString('ko-KR', { maximumFractionDigits: 2 })
                                      }
                                    }
                                    
                                    return (
                                      <div key={cellIndex} className={`truncate ${header === 'lot_number' ? 'font-mono text-accent-blue font-medium' : ''}`} title={displayValue}>
                                        {displayValue}
                                      </div>
                                    )
                                  })}
                                </div>
                              ))}
                            </>
                          )
                        })()}
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      💡 LOT 번호가 각 데이터 행에 자동으로 할당되었습니다 (8개씩 그룹)
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ============================
// 저장된 데이터 관리 패널 컴포넌트
// ============================

interface DataManagementPanelProps {
  files: DataFile[]
  isLoading: boolean
  onRefresh: () => void
  onFileDelete: (filename: string) => void
  activeTab: number
}

function DataManagementPanel({ files, isLoading, onRefresh, onFileDelete, activeTab }: DataManagementPanelProps) {
  const [selectedFile, setSelectedFile] = useState<DataFile | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  // 활성 탭에 따른 데이터 필터링
  const getFilteredFiles = () => {
    if (!Array.isArray(files)) return []
    const tabTypes = ['production', 'sensor', 'experimental', 'cost']
    const currentType = tabTypes[activeTab]
    return files.filter(file => file.dataType === currentType)
  }

  const filteredFiles = getFilteredFiles()

  const getDataTypeIcon = (dataType: string) => {
    switch (dataType) {
      case 'production': return <Factory className="w-4 h-4" />
      case 'sensor': return <Activity className="w-4 h-4" />
      case 'experimental': return <FlaskConical className="w-4 h-4" />
      case 'cost': return <DollarSign className="w-4 h-4" />
      default: return <Database className="w-4 h-4" />
    }
  }

  const getDataTypeLabel = (dataType: string) => {
    switch (dataType) {
      case 'production': return '생산 데이터'
      case 'sensor': return '센서 데이터'
      case 'experimental': return '실험 데이터'
      case 'cost': return '원가 데이터'
      default: return '데이터'
    }
  }

  const getCurrentTabLabel = () => {
    const tabLabels = ['생산 데이터', '센서 데이터', '실험 데이터', '원가 데이터']
    return tabLabels[activeTab]
  }

  const formatFileSize = (sizeKb: number) => {
    if (sizeKb < 1024) {
      return `${sizeKb.toFixed(1)} KB`
    } else {
      return `${(sizeKb / 1024).toFixed(1)} MB`
    }
  }

  const downloadFile = async (file: DataFile) => {
    try {
      // 실제 백엔드에서 파일 다운로드
      const response = await fetch(`${API_BASE_URL}/api/data/download/${encodeURIComponent(file.filename)}`)
      
      if (!response.ok) {
        throw new Error(`다운로드 실패: ${response.statusText}`)
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = file.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('파일 다운로드 실패:', error)
      alert(`파일 다운로드에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`)
    }
  }

  const deleteFile = async (file: DataFile) => {
    if (!confirm(`"${file.filename}" 파일을 삭제하시겠습니까?`)) return
    
    try {
      // 실제 백엔드 API로 파일 삭제
      await deleteFileAPI(file.filename)
      
      // 로컬 상태에서도 제거
      onFileDelete(file.filename)
      
      // 파일 목록 새로고침
      onRefresh()
      
      alert('파일이 성공적으로 삭제되었습니다.')
    } catch (error) {
      console.error('파일 삭제 실패:', error)
      alert(`파일 삭제에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`)
    }
  }

  const openPreview = async (file: DataFile) => {
    try {
      // 실제 파일 미리보기 데이터 로드
      const previewData = await getFilePreviewAPI(file.filename)
      
      // 파일 객체에 실제 미리보기 데이터 추가
      const fileWithPreview = {
        ...file,
        previewData: previewData.data || file.previewData
      }
      
      setSelectedFile(fileWithPreview)
      setShowPreview(true)
    } catch (error) {
      console.error('미리보기 로드 실패:', error)
      // API 실패 시 기존 데이터 사용
      setSelectedFile(file)
      setShowPreview(true)
    }
  }

  return (
    <div className="bg-card border border-border rounded-glass-2xl p-8 shadow-glass-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-foreground flex items-center">
          <Database className="w-6 h-6 mr-3 text-accent-blue" />
          저장된 {getCurrentTabLabel()} 관리
        </h2>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 text-white rounded-glass text-sm transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          새로고침
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center text-muted-foreground">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent-blue mr-3"></div>
            파일 목록을 불러오는 중...
          </div>
        </div>
             ) : filteredFiles.length === 0 ? (
         <div className="text-center py-12">
           <Database className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
           <p className="text-muted-foreground text-lg">저장된 {getCurrentTabLabel()} 파일이 없습니다.</p>
           <p className="text-muted-foreground/70 text-sm mt-2">위에서 {getCurrentTabLabel()}을 생성하면 여기에 표시됩니다.</p>
         </div>
       ) : (
         <>
           <div className="grid gap-4">
             {filteredFiles.map((file, index) => (
              <div key={index} className="bg-muted/50 border border-border rounded-glass p-4 hover:bg-muted transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="flex items-center text-accent-cyan">
                      {getDataTypeIcon(file.dataType)}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-foreground font-medium text-lg">{file.filename}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {file.createTime.toLocaleString('ko-KR')}
                        </span>
                        <span>{getDataTypeLabel(file.dataType)}</span>
                        <span>{formatFileSize(file.fileSizeKb)}</span>
                        {file.rowCount && <span>{file.rowCount.toLocaleString()}행</span>}
                        {file.colCount && <span>{file.colCount}열</span>}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {file.previewData && (
                      <button
                        onClick={() => openPreview(file)}
                        className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-glass transition-colors"
                        title="미리보기"
                      >
                                                 <Play className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => downloadFile(file)}
                      className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-glass transition-colors"
                      title="다운로드"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteFile(file)}
                      className="p-2 text-destructive/70 hover:text-destructive hover:bg-destructive/10 rounded-glass transition-colors"
                      title="삭제"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

                     {/* 파일 통계 */}
           <div className="mt-16 grid grid-cols-1 md:grid-cols-4 gap-4">
             <div className="bg-muted/50 p-4 rounded-glass">
               <div className="text-2xl font-bold text-foreground">{filteredFiles?.length || 0}</div>
               <div className="text-sm text-muted-foreground">총 파일 수</div>
             </div>
             <div className="bg-muted/50 p-4 rounded-glass">
               <div className="text-2xl font-bold text-foreground">
                 {(filteredFiles || []).reduce((sum, file) => sum + (file.rowCount || 0), 0).toLocaleString()}
               </div>
               <div className="text-sm text-muted-foreground">총 레코드 수</div>
             </div>
             <div className="bg-muted/50 p-4 rounded-glass">
               <div className="text-2xl font-bold text-foreground">
                 {formatFileSize((filteredFiles || []).reduce((sum, file) => sum + (file.fileSizeKb || 0), 0))}
               </div>
               <div className="text-sm text-muted-foreground">총 파일 크기</div>
             </div>
             <div className="bg-muted/50 p-4 rounded-glass">
               <div className="text-2xl font-bold text-foreground">
                 {(filteredFiles || []).filter(f => f.createTime && new Date(f.createTime) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length}
               </div>
               <div className="text-sm text-muted-foreground">최근 7일 생성</div>
             </div>
           </div>
        </>
      )}

      {/* 미리보기 모달 */}
      {showPreview && selectedFile && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-glass-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-foreground">데이터 미리보기: {selectedFile.filename}</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-glass transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-auto">
              {selectedFile.previewData ? (
                <div className="bg-muted/30 rounded-glass overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50">
                        <tr>
                          {Object.keys(selectedFile.previewData[0]).map((key) => (
                            <th key={key} className="px-4 py-3 text-left text-muted-foreground font-medium border-b border-border">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {selectedFile.previewData.map((row, index) => (
                          <tr key={index} className="border-b border-border">
                            {Object.values(row).map((value, cellIndex) => (
                              <td key={cellIndex} className="px-4 py-3 text-muted-foreground">
                                {typeof value === 'number' ? value.toLocaleString() : String(value)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">미리보기 데이터가 없습니다.</p>
                </div>
              )}
            </div>
            
            <div className="flex justify-end mt-4 space-x-3">
              <button
                onClick={() => downloadFile(selectedFile)}
                className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 text-white rounded-glass text-sm transition-colors"
              >
                <Download className="w-4 h-4 mr-2" />
                다운로드
              </button>
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-glass text-sm transition-colors"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}