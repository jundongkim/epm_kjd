'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

import { 
  Factory, Settings, RefreshCw, Search, Filter, TrendingUp, 
  AlertTriangle, CheckCircle, Clock, Activity, Cpu,
  BarChart3, Calendar, ChevronDown, Play, Pause, Database,
  Wrench, Bell, Zap, Target, AlertCircle
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { FloatingChatbot } from '@/components/FloatingChatbot'
import { Slider, RangeSlider, Select, TabNavigation } from '@/components/ui'

// ============================
// API 호출 함수들
// ============================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const getLotsAPI = async (dateFilter: string, startDate?: string, endDate?: string) => {
  const response = await fetch(`${API_BASE_URL}/api/process/lots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      date_filter: dateFilter,
      start_date: startDate,
      end_date: endDate
    })
  })
  return await response.json()
}

const getEquipmentStatusAPI = async (dateFilter: string, startDate?: string, endDate?: string) => {
  const response = await fetch(`${API_BASE_URL}/api/process/equipment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      date_filter: dateFilter,
      start_date: startDate,
      end_date: endDate
    })
  })
  return await response.json()
}

const getAnomalyDetectionAPI = async (params: any) => {
  const response = await fetch(`${API_BASE_URL}/api/process/anomaly`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
  return await response.json()
}

// ============================
// 타입 정의
// ============================

interface LotData {
  Lot_ID: string
  상태: string
  설비: string
  시작시간: string
  작업일자: string
  진행률: string
  순도: string
  수율: string
  예상완료: string
}

interface EquipmentStatus {
  ID: string
  상태: string
  가동률: number
  마지막점검: string
  총Lot: number
}

interface AnomalyAlert {
  lot_id: string
  설비: string
  상태: string
  내용: string
}

// ============================
// 컴포넌트들
// ============================

// 재사용 가능한 컴포넌트들 (데이터 생성 페이지와 동일)
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
          <ChevronDown className="w-5 h-5 text-muted-foreground transform rotate-180" />
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

interface DateFilterProps {
  value: string
  onChange: (value: string) => void
  customStartDate?: string
  customEndDate?: string
  onCustomStartDateChange?: (date: string) => void
  onCustomEndDateChange?: (date: string) => void
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function DateFilter({ value, onChange, customStartDate, customEndDate, onCustomStartDateChange, onCustomEndDateChange }: DateFilterProps) {
  const { t } = useTranslation()
  
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Select
          value={value}
          onChange={onChange}
          options={[
            t('processAnalysis.dateFilters.today'),
            t('processAnalysis.dateFilters.yesterday'),
            t('processAnalysis.dateFilters.last3Days'),
            t('processAnalysis.dateFilters.lastWeek'),
            t('processAnalysis.dateFilters.lastMonth'),
            t('processAnalysis.dateFilters.all'),
            t('processAnalysis.dateFilters.custom')
          ]}
          label="날짜 범위"
          placeholder="날짜 선택"
        />
      </div>
      
      {value === t('processAnalysis.dateFilters.custom') && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">{t('processAnalysis.dateFilters.startDate')}</label>
            <input
              type="date"
              value={customStartDate || ''}
              onChange={(e) => onCustomStartDateChange?.(e.target.value)}
              className="w-full px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">{t('processAnalysis.dateFilters.endDate')}</label>
            <input
              type="date"
              value={customEndDate || ''}
              onChange={(e) => onCustomEndDateChange?.(e.target.value)}
              className="w-full px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default function ProcessAnalysisPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState(0)
  const [dateFilter, setDateFilter] = useState(t('processAnalysis.dateFilters.last3Days'))
  const [customStartDate, setCustomStartDate] = useState('')
  const [customEndDate, setCustomEndDate] = useState('')
  const [realtimeMode, setRealtimeMode] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // 데이터 상태
  const [lotData, setLotData] = useState<LotData[]>([])
  const [lotStats, setLotStats] = useState({ active_count: 0, completed_count: 0, waiting_count: 0, total_count: 0 })
  const [equipmentData, setEquipmentData] = useState<EquipmentStatus[]>([])
  const [equipmentStats, setEquipmentStats] = useState<any>({})
  const [anomalyAlerts, setAnomalyAlerts] = useState<AnomalyAlert[]>([])
  const [anomalyStats, setAnomalyStats] = useState<any>({})
  const [loading, setLoading] = useState(false)
  const [isSampleData, setIsSampleData] = useState(false)

  // 이상탐지 설정
  const [tempThreshold, setTempThreshold] = useState(200)
  const [pressureThreshold, setPressureThreshold] = useState(3.0)
  const [purityThreshold, setPurityThreshold] = useState(95.0)
  const [yieldThreshold, setYieldThreshold] = useState(85.0)

  // 실시간 모드 타이머
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // 데이터 로드 함수
  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      // 날짜 파라미터 설정
      const startDate = dateFilter === '사용자 정의' ? customStartDate : undefined
      const endDate = dateFilter === '사용자 정의' ? customEndDate : undefined

      // 모든 데이터 병렬 로드
      const [lotsResponse, equipmentResponse, anomalyResponse] = await Promise.all([
        getLotsAPI(dateFilter, startDate, endDate),
        getEquipmentStatusAPI(dateFilter, startDate, endDate),
        getAnomalyDetectionAPI({
          date_filter: dateFilter,
          start_date: startDate,
          end_date: endDate,
          temp_threshold: tempThreshold,
          pressure_threshold: pressureThreshold,
          purity_threshold: purityThreshold,
          yield_threshold: yieldThreshold
        })
      ])

      if (lotsResponse.success) {
        setLotData(lotsResponse.lots)
        setLotStats(lotsResponse.statistics)
        setIsSampleData(lotsResponse.is_sample_data || false)
      }

      if (equipmentResponse.success) {
        setEquipmentData(equipmentResponse.equipment_status)
        setEquipmentStats(equipmentResponse.equipment_stats)
        // 설비 데이터의 샘플 여부도 확인 (추가 안전장치)
        if (equipmentResponse.is_sample_data) {
          setIsSampleData(true)
        }
      }

      if (anomalyResponse.success) {
        setAnomalyAlerts(anomalyResponse.anomaly_alerts)
        setAnomalyStats(anomalyResponse.anomaly_stats)
        // 이상탐지 데이터의 샘플 여부도 확인 (추가 안전장치)
        if (anomalyResponse.is_sample_data) {
          setIsSampleData(true)
        }
      }

    } catch (error) {
      console.error('데이터 로드 오류:', error)
    } finally {
      setLoading(false)
    }
  }, [dateFilter, customStartDate, customEndDate, tempThreshold, pressureThreshold, purityThreshold, yieldThreshold])

  // 새로고침 핸들러
  const handleRefresh = async () => {
    setIsRefreshing(true)
    await loadData()
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  // 실시간 모드 효과
  useEffect(() => {
    if (realtimeMode) {
      intervalRef.current = setInterval(() => {
        loadData()
      }, 30000) // 30초마다 갱신
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [realtimeMode, dateFilter, customStartDate, customEndDate, tempThreshold, pressureThreshold, purityThreshold, yieldThreshold])

  // 초기 데이터 로드
  useEffect(() => {
    loadData()
  }, [loadData])

  // 이상탐지 설정 변경 시 데이터 갱신
  useEffect(() => {
    if (activeTab === 2) {
      const timer = setTimeout(() => {
        loadData()
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [activeTab, loadData])

  return (
    <div className="p-6 space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center">
            <Factory className="w-8 h-8 mr-3 text-accent-purple" />
            {t('processAnalysis.title')}
          </h1>
          <p className="text-muted-foreground text-lg">{t('processAnalysis.subtitle')}</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* 조회 조건 */}
          <div className="flex items-center space-x-2 min-w-[140px]">
            <Calendar className="w-4 h-4 text-accent-cyan" />
            <div className="min-w-[120px]">
              <Select
                value={dateFilter}
                onChange={setDateFilter}
                options={[
                  t('processAnalysis.dateFilters.today'),
                  t('processAnalysis.dateFilters.yesterday'),
                  t('processAnalysis.dateFilters.last3Days'),
                  t('processAnalysis.dateFilters.lastWeek'),
                  t('processAnalysis.dateFilters.lastMonth'),
                  t('processAnalysis.dateFilters.all'),
                  t('processAnalysis.dateFilters.custom')
                ]}
                label=""
                placeholder="날짜 선택"
              />
            </div>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center px-4 py-2 bg-card hover:bg-muted/50 border border-border rounded-lg text-foreground text-sm transition-all duration-200 shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            {t('processAnalysis.refresh')}
          </button>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={realtimeMode}
              onChange={(e) => setRealtimeMode(e.target.checked)}
              className="sr-only"
            />
            <div className={`w-12 h-6 rounded-full transition-colors ${realtimeMode ? 'bg-gradient-primary' : 'bg-muted'}`}>
              <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${realtimeMode ? 'translate-x-6' : 'translate-x-0.5'} mt-0.5`} />
            </div>
            <span className="text-foreground text-sm">{t('processAnalysis.realtimeMode')}</span>
          </label>
        </div>
      </div>

      {/* 샘플 데이터 알림 배너 */}
      {isSampleData && (
        <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
              <div>
                <h3 className="text-amber-100 font-semibold text-lg">
                  샘플 데이터를 사용 중입니다
                </h3>
                <p className="text-amber-200/90 text-sm">
                  실제 생산 데이터가 없어 데모용 샘플 데이터를 표시하고 있습니다.
                </p>
              </div>
            </div>
            <a 
              href="/copilot/data-generation"
              className="flex items-center px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm rounded-lg transition-all duration-200 shadow-sm"
            >
              <Database className="w-4 h-4 mr-2" />
              데이터 생성하기
            </a>
          </div>
        </div>
      )}

      {/* 커스텀 날짜 선택 (사용자 정의가 선택된 경우에만 표시) */}
      {dateFilter === t('processAnalysis.dateFilters.custom') && (
        <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-accent-cyan" />
            {t('processAnalysis.searchConditions')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">{t('processAnalysis.dateFilters.startDate')}</label>
              <input
                type="date"
                value={customStartDate || ''}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="w-full px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">{t('processAnalysis.dateFilters.endDate')}</label>
              <input
                type="date"
                value={customEndDate || ''}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="w-full px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
              />
            </div>
          </div>
          {realtimeMode && (
            <div className="mt-4 p-3 bg-accent-blue/10 border border-accent-blue/30 rounded-lg">
              <p className="text-accent-blue text-sm flex items-center">
                <Activity className="w-4 h-4 mr-2" />
                {t('processAnalysis.realtimeModeActive')}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 실시간 모드 알림 (커스텀 날짜가 아닌 경우에만 표시) */}
      {realtimeMode && dateFilter !== t('processAnalysis.dateFilters.custom') && (
        <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-4 shadow-sm">
          <p className="text-accent-blue text-sm flex items-center">
            <Activity className="w-4 h-4 mr-2" />
            {t('processAnalysis.realtimeModeActive')}
          </p>
        </div>
      )}

      {/* 전체 현황 대시보드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title={t('processAnalysis.statusCards.activeLots')}
          value={lotStats.active_count}
          icon={<Play className="w-6 h-6 text-white" />}
          color="#3b82f6"
        />
        <StatusCard
          title={t('processAnalysis.statusCards.completedLots')}
          value={lotStats.completed_count}
          icon={<CheckCircle className="w-6 h-6 text-white" />}
          color="#22c55e"
        />
        <StatusCard
          title={t('processAnalysis.statusCards.waitingLots')}
          value={lotStats.waiting_count}
          icon={<Clock className="w-6 h-6 text-white" />}
          color="#f97316"
        />
        <StatusCard
          title={t('processAnalysis.statusCards.anomalyCount')}
          value={anomalyStats.anomaly_count || 0}
          icon={<AlertTriangle className="w-6 h-6 text-white" />}
          color="#ef4444"
        />
      </div>

      {/* 탭 네비게이션 */}
      <TabNavigation
        tabs={[
          { id: 0, name: t('processAnalysis.tabs.lotTracking'), icon: Database },
          { id: 1, name: t('processAnalysis.tabs.equipmentMonitoring'), icon: Cpu },
          { id: 2, name: t('processAnalysis.tabs.anomalyDetection'), icon: AlertTriangle }
        ]}
        activeTab={activeTab}
        onTabChange={(tabId) => setActiveTab(tabId as number)}
      />

      {/* 탭 컨텐츠 */}
      <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm min-h-[600px]">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-blue"></div>
          </div>
        ) : (
          <>
            {activeTab === 0 && <LotTrackingTab lots={lotData || []} stats={lotStats || {}} />}
            {activeTab === 1 && <EquipmentMonitoringTab equipment={equipmentData || []} stats={equipmentStats || {}} />}
            {activeTab === 2 && (
              <AnomalyDetectionTab
                alerts={anomalyAlerts || []}
                stats={anomalyStats || {}}
                tempThreshold={tempThreshold}
                setTempThreshold={setTempThreshold}
                pressureThreshold={pressureThreshold}
                setPressureThreshold={setPressureThreshold}
                purityThreshold={purityThreshold}
                setPurityThreshold={setPurityThreshold}
                yieldThreshold={yieldThreshold}
                setYieldThreshold={setYieldThreshold}
              />
            )}
          </>
        )}
      </div>

      {/* 플로팅 챗봇 위젯 */}
      <FloatingChatbot
        topic="process_analysis"
        sessionId="process_analysis_session"
        enableStreaming={true}
        simulationParams={{
          activeTab: activeTab === 0 ? 'lot_tracking' : activeTab === 1 ? 'equipment_monitoring' : 'anomaly_detection',
          dateFilter: dateFilter,
          realtimeMode: realtimeMode,
          lotStats: {
            total: lotStats.total_count || 0,
            active: lotStats.active_count || 0,
            completed: lotStats.completed_count || 0,
            waiting: lotStats.waiting_count || 0
          },
          equipmentStats: {
            total: equipmentStats.total_equipment || 0,
            active: equipmentStats.active_equipment || 0,
            maintenance: equipmentStats.maintenance_equipment || 0
          },
          anomalySettings: {
            tempThreshold: tempThreshold,
            pressureThreshold: pressureThreshold,
            purityThreshold: purityThreshold,
            yieldThreshold: yieldThreshold,
            totalAlerts: anomalyStats.anomaly_count || 0
          },
          isSampleData: isSampleData
        }}
        position="bottom-right"
        theme="dark"
        accentColor="blue"
        minimizedText="AI 공정 전문가"
        placeholder="공정 분석에 대해 질문하세요..."
        maxHeight={800}
        width={600}
        showSessionInfo={false}
        onToggle={(isOpen) => {
          // 챗봇이 열리거나 닫힐 때의 로직 (선택사항)
          console.log('Chatbot toggle:', isOpen);
        }}
      />
    </div>
  )
}

// ============================
// 탭 컴포넌트들
// ============================

function LotTrackingTab({ lots, stats }: { lots: LotData[], stats: any }) {
  const { t } = useTranslation()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState(t('processAnalysis.common.all'))
  const [equipmentFilter, setEquipmentFilter] = useState(t('processAnalysis.common.all'))
  const [purityRange, setPurityRange] = useState<[number, number]>([0, 100])
  const [yieldRange, setYieldRange] = useState<[number, number]>([0, 100])

  const getStatusIcon = (status: string) => {
    // null/undefined 체크 추가
    if (!status) {
      return <AlertCircle className="w-4 h-4 text-muted-foreground" />
    }
    
    switch (status) {
      case t('processAnalysis.lotTracking.statuses.active'): 
      case '활성': return <Play className="w-4 h-4 text-accent-blue" />
      case t('processAnalysis.lotTracking.statuses.completed'): 
      case '완료': return <CheckCircle className="w-4 h-4 text-accent-cyan" />
      case t('processAnalysis.lotTracking.statuses.waiting'): 
      case '대기': return <Clock className="w-4 h-4 text-accent-orange" />
      default: return <AlertCircle className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case t('processAnalysis.lotTracking.statuses.active'): 
      case '활성': return 'bg-accent-blue/20 text-accent-blue border-accent-blue/30'
      case t('processAnalysis.lotTracking.statuses.completed'): 
      case '완료': return 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30'
      case t('processAnalysis.lotTracking.statuses.waiting'): 
      case '대기': return 'bg-accent-orange/20 text-accent-orange border-accent-orange/30'
      default: return 'bg-muted/20 text-muted-foreground border-border'
    }
  }

  // 안전하게 lots 배열 처리
  const safeLots = Array.isArray(lots) ? lots : []
  
  // 설비 목록 추출
  const equipmentList = [t('processAnalysis.common.all'), ...Array.from(new Set(safeLots.map(lot => lot?.설비).filter(Boolean)))]
  
  const filteredLots = safeLots.filter(lot => {
    if (!lot || !lot.Lot_ID) return false
    const matchesSearch = lot.Lot_ID.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === t('processAnalysis.common.all') || lot.상태 === statusFilter
    const matchesEquipment = equipmentFilter === t('processAnalysis.common.all') || lot.설비 === equipmentFilter
    
    // 순도/수율 범위 필터링
    const purity = parseFloat(lot.순도?.replace('%', '')) || 0
    const yield_ = parseFloat(lot.수율?.replace('%', '')) || 0
    const matchesPurity = purity >= purityRange[0] && purity <= purityRange[1]
    const matchesYield = yield_ >= yieldRange[0] && yield_ <= yieldRange[1]
    
    return matchesSearch && matchesStatus && matchesEquipment && matchesPurity && matchesYield
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-foreground flex items-center">
          <Database className="w-6 h-6 mr-2 text-accent-blue" />
          {t('processAnalysis.lotTracking.title')}
        </h3>
      </div>

      {/* 기본 검색 및 필터 */}
      <Expander 
        title={t('processAnalysis.lotTracking.searchAndBasicFilter')} 
        defaultExpanded={true}
        icon={<Search className="w-5 h-5 text-accent-blue" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">{t('processAnalysis.lotTracking.lotIdSearch')}</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder={t('processAnalysis.lotTracking.lotIdSearchPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
              />
            </div>
          </div>
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              t('processAnalysis.lotTracking.statuses.all'), 
              t('processAnalysis.lotTracking.statuses.active'), 
              t('processAnalysis.lotTracking.statuses.completed'), 
              t('processAnalysis.lotTracking.statuses.waiting')
            ]}
            label={t('processAnalysis.lotTracking.statusFilter')}
          />
          <Select
            value={equipmentFilter}
            onChange={setEquipmentFilter}
            options={equipmentList}
            label={t('processAnalysis.lotTracking.equipmentFilter')}
          />
        </div>
      </Expander>

      {/* 고급 필터 */}
      <Expander 
        title={t('processAnalysis.lotTracking.advancedFilter')} 
        defaultExpanded={false}
        icon={<Filter className="w-5 h-5 text-accent-purple" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <RangeSlider
            min={0}
            max={100}
            value={purityRange}
            onChange={setPurityRange}
            label={t('processAnalysis.lotTracking.purityRange')}
            unit={t('processAnalysis.common.percentage')}
          />
          <RangeSlider
            min={0}
            max={100}
            value={yieldRange}
            onChange={setYieldRange}
            label={t('processAnalysis.lotTracking.yieldRange')}
            unit={t('processAnalysis.common.percentage')}
          />
        </div>
      </Expander>

      {/* Lot 목록 */}
      <Expander 
        title={`${t('processAnalysis.lotTracking.lotList')} (${filteredLots.length}${t('processAnalysis.common.count')})`}
        defaultExpanded={true}
        icon={<Database className="w-5 h-5 text-accent-blue" />}
      >
        {filteredLots.length > 0 ? (
          <div className="grid gap-4 max-h-96 overflow-y-auto">
            {filteredLots.map((lot, index) => (
              <div key={`${lot.Lot_ID || 'lot'}-${index}`} className="bg-muted/50 backdrop-blur-sm border border-border rounded-lg p-4 hover:bg-muted/70 transition-all duration-300">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <h4 className="text-lg font-semibold text-foreground">{lot.Lot_ID || 'Unknown'}</h4>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm border ${getStatusColor(lot.상태 || '')}`}>
                      {getStatusIcon(lot.상태 || '')}
                      <span className="ml-1">{lot.상태 || '상태 없음'}</span>
                    </span>
                  </div>
                  <div className="text-muted-foreground text-sm">
                    {lot.작업일자 || ''} {lot.시작시간 || ''}
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">설비:</span>
                    <span className="text-foreground ml-2">{lot.설비 || '-'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">진행률:</span>
                    <span className="text-foreground ml-2">{lot.진행률 || '-'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">순도:</span>
                    <span className="text-foreground ml-2">{lot.순도 || '-'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">수율:</span>
                    <span className="text-foreground ml-2">{lot.수율 || '-'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">예상완료:</span>
                    <span className="text-foreground ml-2">{lot.예상완료 || '-'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Database className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">조건에 맞는 Lot이 없습니다.</p>
          </div>
        )}
      </Expander>
    </div>
  )
}

function EquipmentMonitoringTab({ equipment, stats }: { equipment: EquipmentStatus[], stats: any }) {
  const { t } = useTranslation()
  const [statusFilter, setStatusFilter] = useState(t('processAnalysis.equipmentMonitoring.statuses.all'))
  const [utilizationRange, setUtilizationRange] = useState<[number, number]>([0, 100])
  const [sortBy, setSortBy] = useState(t('processAnalysis.equipmentMonitoring.sortOptions.utilization'))
  const [sortOrder, setSortOrder] = useState(t('processAnalysis.equipmentMonitoring.sortOrders.descending'))

  const getUtilizationColor = (utilization: number) => {
    if (utilization >= 80) return 'text-accent-cyan'
    if (utilization >= 60) return 'text-accent-blue'
    if (utilization >= 40) return 'text-accent-orange'
    return 'text-accent-pink'
  }

  const getStatusIcon = (status: string) => {
    // null/undefined 체크 추가
    if (!status) {
      return <AlertCircle className="w-4 h-4 text-muted-foreground" />
    }
    
    switch (status) {
      case t('processAnalysis.equipmentMonitoring.statuses.running'):
      case '가동 중': return <Activity className="w-4 h-4 text-accent-cyan" />
      case t('processAnalysis.equipmentMonitoring.statuses.waiting'):
      case '대기': return <Pause className="w-4 h-4 text-accent-orange" />
      case t('processAnalysis.equipmentMonitoring.statuses.maintenanceRequired'):
      case '점검 필요': return <Wrench className="w-4 h-4 text-accent-pink" />
      default: return <AlertCircle className="w-4 h-4 text-muted-foreground" />
    }
  }

  // 안전하게 equipment 배열 처리
  const safeEquipment = Array.isArray(equipment) ? equipment : []

  // 필터링 및 정렬
  const filteredEquipment = safeEquipment
    .filter(eq => {
      if (!eq) return false
      const matchesStatus = statusFilter === t('processAnalysis.equipmentMonitoring.statuses.all') || eq.상태 === statusFilter
      const matchesUtilization = eq.가동률 >= utilizationRange[0] && eq.가동률 <= utilizationRange[1]
      return matchesStatus && matchesUtilization
    })
    .sort((a, b) => {
      let valueA, valueB
      switch (sortBy) {
        case t('processAnalysis.equipmentMonitoring.sortOptions.utilization'):
        case '가동률':
          valueA = a.가동률 || 0
          valueB = b.가동률 || 0
          break
        case t('processAnalysis.equipmentMonitoring.sortOptions.lotCount'):
        case 'Lot 수':
          valueA = a.총Lot || 0
          valueB = b.총Lot || 0
          break
        case t('processAnalysis.equipmentMonitoring.sortOptions.id'):
        case 'ID':
          valueA = a.ID || ''
          valueB = b.ID || ''
          break
        default:
          return 0
      }
      
      if (sortOrder === t('processAnalysis.equipmentMonitoring.sortOrders.ascending') || sortOrder === '오름차순') {
        return valueA > valueB ? 1 : -1
      } else {
        return valueA < valueB ? 1 : -1
      }
    })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-foreground flex items-center">
          <Cpu className="w-6 h-6 mr-2 text-accent-purple" />
          {t('processAnalysis.equipmentMonitoring.title')}
        </h3>
      </div>

      {/* 필터링 설정 */}
      <Expander 
        title={t('processAnalysis.equipmentMonitoring.filterAndSort')} 
        defaultExpanded={true}
        icon={<Filter className="w-5 h-5 text-accent-purple" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              t('processAnalysis.equipmentMonitoring.statuses.all'), 
              t('processAnalysis.equipmentMonitoring.statuses.running'), 
              t('processAnalysis.equipmentMonitoring.statuses.waiting'), 
              t('processAnalysis.equipmentMonitoring.statuses.maintenanceRequired')
            ]}
            label={t('processAnalysis.lotTracking.statusFilter')}
          />
          <Select
            value={sortBy}
            onChange={setSortBy}
            options={[
              t('processAnalysis.equipmentMonitoring.sortOptions.utilization'), 
              t('processAnalysis.equipmentMonitoring.sortOptions.lotCount'), 
              t('processAnalysis.equipmentMonitoring.sortOptions.id')
            ]}
            label={t('processAnalysis.equipmentMonitoring.sortBy')}
          />
          <Select
            value={sortOrder}
            onChange={setSortOrder}
            options={[
              t('processAnalysis.equipmentMonitoring.sortOrders.descending'), 
              t('processAnalysis.equipmentMonitoring.sortOrders.ascending')
            ]}
            label={t('processAnalysis.equipmentMonitoring.sortOrder')}
          />
        </div>
        <div className="mt-4">
          <RangeSlider
            min={0}
            max={100}
            value={utilizationRange}
            onChange={setUtilizationRange}
            label={t('processAnalysis.equipmentMonitoring.utilizationRange')}
            unit={t('processAnalysis.common.percentage')}
          />
        </div>
      </Expander>

      {/* 설비 통계 요약 */}
      <Expander 
        title={t('processAnalysis.equipmentMonitoring.equipmentStatsSummary')} 
        defaultExpanded={false}
        icon={<BarChart3 className="w-5 h-5 text-accent-cyan" />}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-muted/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-accent-cyan">{filteredEquipment.length}</div>
            <div className="text-sm text-muted-foreground">{t('processAnalysis.equipmentMonitoring.totalEquipment')}</div>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-accent-blue">
              {filteredEquipment.filter(eq => eq?.상태 === '가동 중' || eq?.상태 === t('processAnalysis.equipmentMonitoring.statuses.running')).length}
            </div>
            <div className="text-sm text-muted-foreground">{t('processAnalysis.equipmentMonitoring.running')}</div>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-accent-orange">
              {(filteredEquipment.reduce((sum, eq) => sum + (eq?.가동률 || 0), 0) / filteredEquipment.length || 0).toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">{t('processAnalysis.equipmentMonitoring.averageUtilization')}</div>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-accent-pink">
              {filteredEquipment.reduce((sum, eq) => sum + (eq?.총Lot || 0), 0)}
            </div>
            <div className="text-sm text-muted-foreground">{t('processAnalysis.equipmentMonitoring.totalLots')}</div>
          </div>
        </div>
      </Expander>

      {/* 설비 현황 카드 */}
      <Expander 
        title={`${t('processAnalysis.equipmentMonitoring.equipmentStatus')} (${filteredEquipment.length}${t('processAnalysis.common.count')})`}
        defaultExpanded={true}
        icon={<Cpu className="w-5 h-5 text-accent-purple" />}
      >
        {filteredEquipment.length > 0 ? (
          <div className="grid gap-4 max-h-96 overflow-y-auto">
            {filteredEquipment.map((eq, index) => (
              <div key={`${eq?.ID || 'equipment'}-${index}`} className="bg-muted/50 backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/70 transition-all duration-300">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <h4 className="text-lg font-semibold text-foreground">{eq?.ID || t('processAnalysis.common.unknown')}</h4>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-muted border border-border">
                      {getStatusIcon(eq?.상태 || '')}
                      <span className="ml-1 text-foreground">{eq?.상태 || t('processAnalysis.equipmentMonitoring.statuses.noStatus')}</span>
                    </span>
                  </div>
                  <div className={`text-2xl font-bold ${getUtilizationColor(eq?.가동률 || 0)}`}>
                    {eq?.가동률 || 0}%
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.totalLotsLabel')}:</span>
                    <span className="text-foreground ml-2">{eq?.총Lot || 0}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.lastInspection')}:</span>
                    <span className="text-foreground ml-2">{eq?.마지막점검 || '-'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.utilization')}:</span>
                    <div className="mt-1">
                      <div className="w-full bg-muted rounded-full h-2">
                        <div 
                          className="bg-gradient-primary h-2 rounded-full transition-all duration-300"
                          style={{ width: `${eq?.가동률 || 0}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* 상세 통계 (있는 경우) */}
                {stats && eq?.ID && stats[eq.ID] && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.averagePurity')}:</span>
                        <span className="text-foreground ml-2">{stats[eq.ID].avg_purity?.toFixed(1) || 0}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.averageYield')}:</span>
                        <span className="text-foreground ml-2">{stats[eq.ID].avg_yield?.toFixed(1) || 0}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.completionRate')}:</span>
                        <span className="text-foreground ml-2">{stats[eq.ID].completion_rate?.toFixed(1) || 0}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">{t('processAnalysis.equipmentMonitoring.totalWork')}:</span>
                        <span className="text-foreground ml-2">{stats[eq.ID].total_lots || 0}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Cpu className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              {safeEquipment.length === 0 ? t('processAnalysis.equipmentMonitoring.noEquipmentData') : t('processAnalysis.equipmentMonitoring.noFilteredEquipmentData')}
            </p>
          </div>
        )}
      </Expander>
    </div>
  )
}

interface AnomalyDetectionTabProps {
  alerts: AnomalyAlert[]
  stats: any
  tempThreshold: number
  setTempThreshold: (value: number) => void
  pressureThreshold: number
  setPressureThreshold: (value: number) => void
  purityThreshold: number
  setPurityThreshold: (value: number) => void
  yieldThreshold: number
  setYieldThreshold: (value: number) => void
}

function AnomalyDetectionTab({
  alerts, stats, tempThreshold, setTempThreshold, pressureThreshold, setPressureThreshold,
  purityThreshold, setPurityThreshold, yieldThreshold, setYieldThreshold
}: AnomalyDetectionTabProps) {
  const { t } = useTranslation()
  
  const getAlertIcon = (status: string) => {
    switch (status) {
      case t('processAnalysis.anomalyDetection.statuses.normal'):
      case '정상': return <CheckCircle className="w-5 h-5 text-accent-cyan" />
      case t('processAnalysis.anomalyDetection.statuses.warning'):
      case '주의': return <AlertTriangle className="w-5 h-5 text-accent-orange" />
      case t('processAnalysis.anomalyDetection.statuses.critical'):
      case '위험': return <AlertCircle className="w-5 h-5 text-accent-pink" />
      default: return <Bell className="w-5 h-5 text-muted-foreground" />
    }
  }

  const getAlertColor = (status: string) => {
    switch (status) {
      case t('processAnalysis.anomalyDetection.statuses.normal'):
      case '정상': return 'bg-accent-cyan/10 border-accent-cyan/30'
      case t('processAnalysis.anomalyDetection.statuses.warning'):
      case '주의': return 'bg-accent-orange/10 border-accent-orange/30'
      case t('processAnalysis.anomalyDetection.statuses.critical'):
      case '위험': return 'bg-accent-pink/10 border-accent-pink/30'
      default: return 'bg-muted/10 border-border'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-foreground flex items-center">
          <AlertTriangle className="w-6 h-6 mr-2 text-accent-orange" />
          {t('processAnalysis.anomalyDetection.title')}
        </h3>
      </div>

      {/* 이상탐지 설정 */}
      <Expander 
        title={t('processAnalysis.anomalyDetection.thresholdSettings')} 
        defaultExpanded={true}
        icon={<Settings className="w-5 h-5 text-accent-blue" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Slider
            min={100}
            max={250}
            value={tempThreshold}
            onChange={setTempThreshold}
            label={t('processAnalysis.anomalyDetection.temperatureThreshold')}
            unit={t('processAnalysis.common.celsius')}
          />
          <Slider
            min={1.0}
            max={5.0}
            step={0.1}
            value={pressureThreshold}
            onChange={setPressureThreshold}
            label={t('processAnalysis.anomalyDetection.pressureThreshold')}
            unit={` ${t('processAnalysis.common.bar')}`}
          />
          <Slider
            min={70}
            max={99}
            value={purityThreshold}
            onChange={setPurityThreshold}
            label={t('processAnalysis.anomalyDetection.purityThreshold')}
            unit={t('processAnalysis.common.percentage')}
          />
          <Slider
            min={70}
            max={95}
            value={yieldThreshold}
            onChange={setYieldThreshold}
            label={t('processAnalysis.anomalyDetection.yieldThreshold')}
            unit={t('processAnalysis.common.percentage')}
          />
        </div>
      </Expander>

      {/* 고급 이상탐지 설정 */}
      <Expander 
        title={t('settings.advanced.title')}
        defaultExpanded={false}
        icon={<Zap className="w-5 h-5 text-accent-orange" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Select
            value="연속 이상"
            onChange={() => {}}
            options={["연속 이상", "임계값 초과", "급격한 변화", "패턴 이상"]}
            label="이상탐지 모드"
          />
          <Slider
            min={1}
            max={10}
            value={3}
            onChange={() => {}}
            label="연속 이상 횟수"
            unit="회"
          />
          <Slider
            min={0.1}
            max={2.0}
            step={0.1}
            value={1.0}
            onChange={() => {}}
            label="민감도"
            unit="x"
          />
          <Select
            value="중간"
            onChange={() => {}}
            options={["낮음", "중간", "높음", "매우 높음"]}
            label="알림 레벨"
          />
        </div>
      </Expander>

      {/* 이상탐지 통계 */}
      <Expander 
        title={t('processAnalysis.anomalyDetection.alertSummary')}
        defaultExpanded={true}
        icon={<Target className="w-5 h-5 text-accent-blue" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatusCard
            title={t('processAnalysis.anomalyDetection.totalAlerts')}
            value={stats.total_lots || 0}
            icon={<Target className="w-6 h-6 text-white" />}
            color="#3b82f6"
          />
          <StatusCard
            title={t('processAnalysis.anomalyDetection.criticalAlerts')}
            value={stats.anomaly_count || 0}
            icon={<AlertTriangle className="w-6 h-6 text-white" />}
            color="#ef4444"
            trend={`${(stats.anomaly_rate || 0).toFixed(1)}%`}
          />
          <StatusCard
            title={t('processAnalysis.anomalyDetection.warningAlerts')}
            value={stats.temp_anomalies || 0}
            icon={<Zap className="w-6 h-6 text-white" />}
            color="#eab308"
          />
          <StatusCard
            title={t('processAnalysis.anomalyDetection.normalAlerts')}
            value={stats.pressure_anomalies || 0}
            icon={<TrendingUp className="w-6 h-6 text-white" />}
            color="#06b6d4"
          />
        </div>
      </Expander>

      {/* 실시간 이상 알림 */}
      <Expander 
        title={`${t('processAnalysis.anomalyDetection.realtimeAlerts')} (${Array.isArray(alerts) ? alerts.length : 0}${t('processAnalysis.common.count')})`}
        defaultExpanded={true}
        icon={<Bell className="w-5 h-5 text-accent-cyan" />}
      >
        {Array.isArray(alerts) && alerts.length > 0 ? (
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {alerts.map((alert, index) => (
              <div key={`${alert?.lot_id || 'alert'}-${alert?.설비 || 'unknown'}-${index}`} className={`p-4 rounded-lg border ${getAlertColor(alert?.상태 || '')} backdrop-blur-sm`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getAlertIcon(alert?.상태 || '')}
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-foreground">{alert?.lot_id || t('processAnalysis.common.unknown')}</span>
                        <span className="text-muted-foreground">({alert?.설비 || t('processAnalysis.common.unknown')})</span>
                      </div>
                      <p className="text-foreground mt-1">{alert?.내용 || t('processAnalysis.common.noData')}</p>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">{alert?.상태 || t('processAnalysis.common.noData')}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-muted/50 rounded-lg border border-border">
            <CheckCircle className="w-12 h-12 text-accent-cyan mx-auto mb-4" />
            <p className="text-foreground text-lg font-medium">{t('processAnalysis.anomalyDetection.noAnomalyData')}</p>
            <p className="text-muted-foreground mt-2">{t('processAnalysis.anomalyDetection.noFilteredAnomalyData')}</p>
          </div>
        )}
      </Expander>
    </div>
  )
} 