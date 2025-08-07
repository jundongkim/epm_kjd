'use client'

import { useState, useEffect, useCallback, useRef, forwardRef } from 'react'
import {
    Database, Upload, Settings, TrendingUp, Activity,
    FileText, Calendar, Clock, CheckCircle, AlertCircle,
    ChevronDown, ChevronUp, X, Info, RefreshCw, Play,
    BarChart3, Box, Move, Trash2
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { Slider, Select, MultiSelect, Checkbox, TabNavigation } from '@/components/ui'
import dynamic from 'next/dynamic'

// Plotly를 동적 import (SSR 방지)
const Plot = dynamic(() => import('react-plotly.js').then(mod => mod.default), { ssr: false })

// Plotly modebar 스타일링
const plotlyModebarStyles = `
  .modebar {
    height: 32px !important;
    display: flex !important;
    align-items: center !important;
    gap: 4px !important;
  }
  .modebar-group {
    display: flex !important;
    background-color: rgba(0, 0, 0, 0.3) !important;
    border-radius: 6px !important;
    padding: 2px !important;
    margin: 0 2px !important;
    border: none !important;
  }
  .modebar-btn {
    width: 28px !important;
    height: 28px !important;
    margin: 0 !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
  }
  .modebar-btn:hover {
    background: rgba(0, 0, 0, 0.6) !important;
  }
  .modebar-btn svg {
    width: 18px !important;
    height: 18px !important;
  }
`

// ============================
// 타입 정의
// ============================

interface CSVData {
    filename: string
    columns: string[]
    data: Record<string, any>[]
    rowCount: number
    colCount: number
}

type ChartType = 'line' | 'box' | 'scatter'
type ViewMode = 'individual' | 'overlay'
type TimeUnit = 'hour' | 'day' | 'week' | 'month'

interface ChartConfig {
    type: ChartType
    viewMode: ViewMode
    timeUnit: TimeUnit
}

interface DataConfig {
    timestampColumn: string
    visualizationColumns: string[]
    excludeColumns: string[]
}

interface ComparisonSegment {
    id: string
    column: string
    startTime: Date
    endTime: Date
    data: any[]
    xOffset: number
    color: string
}

interface AIAnalysisResult {
    id: string
    chartName: string
    chartType: ChartType
    analysisText: string
    timestamp: string
    confidence?: number
}

interface AIAnalysisState {
    [chartId: string]: {
        isAnalyzing: boolean
        result: AIAnalysisResult | null
        error: string | null
    }
}

// ============================
// StatusCard 컴포넌트 (data-generation 페이지와 동일)
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
// Expander 컴포넌트 (data-generation 페이지와 동일)
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

// ============================
// 파일 업로드 컴포넌트
// ============================

interface FileUploadProps {
    onFileLoad: (data: CSVData) => void
    isLoading: boolean
}

function FileUpload({ onFileLoad, isLoading }: FileUploadProps) {
    const { t } = useTranslation()
    const [dragOver, setDragOver] = useState(false)

    const parseCSV = (text: string): any[] => {
        const lines = text.split('\n').filter(line => line.trim())
        if (lines.length === 0) return []

        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
        const data = lines.slice(1).map(line => {
            const values = line.split(',').map(v => v.trim().replace(/"/g, ''))
            const row: Record<string, any> = {}

            headers.forEach((header, index) => {
                const value = values[index] || ''
                // 숫자 변환 시도
                const numValue = Number(value)
                if (!isNaN(numValue) && isFinite(numValue)) {
                    row[header] = numValue
                } else {
                    // 날짜 변환 시도
                    const dateValue = new Date(value)
                    if (!isNaN(dateValue.getTime()) && value.length > 8) {
                        row[header] = dateValue
                    } else {
                        row[header] = value
                    }
                }
            })
            return row
        })

        return data
    }

    const handleFileSelect = useCallback((file: File) => {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            alert(t('iotPrismDemo.errors.fileNotSupported'))
            return
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB
            alert(t('iotPrismDemo.errors.fileTooLarge'))
            return
        }

        const reader = new FileReader()
        reader.onload = (e) => {
            try {
                const text = e.target?.result as string
                const data = parseCSV(text)
                const columns = data.length > 0 ? Object.keys(data[0]) : []

                onFileLoad({
                    filename: file.name,
                    columns,
                    data,
                    rowCount: data.length,
                    colCount: columns.length
                })
            } catch (error) {
                console.error('CSV 파싱 오류:', error)
                alert(t('iotPrismDemo.errors.parseError'))
            }
        }
        reader.readAsText(file)
    }, [onFileLoad, t])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setDragOver(false)

        const files = Array.from(e.dataTransfer.files)
        if (files.length > 0) {
            handleFileSelect(files[0])
        }
    }, [handleFileSelect])

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files
        if (files && files.length > 0) {
            handleFileSelect(files[0])
        }
    }, [handleFileSelect])

    return (
        <div className="space-y-4">
            <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragOver
                    ? 'border-accent-blue bg-accent-blue/10'
                    : 'border-border hover:border-accent-blue/50'
                    }`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
            >
                <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-foreground text-lg mb-2">{t('iotPrismDemo.upload.dragDrop')}</p>
                <p className="text-muted-foreground text-sm mb-4">{t('iotPrismDemo.upload.supportedFormats')}</p>
                <p className="text-muted-foreground text-xs mb-4">{t('iotPrismDemo.upload.maxSize')}</p>

                <label className="inline-block">
                    <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileInput}
                        className="hidden"
                        disabled={isLoading}
                    />
                    <span className="inline-flex items-center px-6 py-3 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 text-white font-medium rounded-lg cursor-pointer transition-colors">
                        {isLoading ? (
                            <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                {t('iotPrismDemo.upload.processing')}
                            </>
                        ) : (
                            <>
                                <FileText className="w-4 h-4 mr-2" />
                                {t('iotPrismDemo.upload.uploadButton')}
                            </>
                        )}
                    </span>
                </label>
            </div>
        </div>
    )
}

// ============================
// 시계열 시각화 컴포넌트
// ============================

interface TimeSeriesVisualizationProps {
    data: Array<{
        column: string
        data: any[]
        x: Date[]
        y: number[]
    }>
    config: ChartConfig
    onSelectionMade?: (column: string, startTime: Date, endTime: Date) => void
    selectedColumn: string
    onImageCapture?: (chartElement: HTMLElement, chartName: string) => void
    onAIAnalysis?: (chartElement: HTMLElement, chartName: string, chartType: ChartType) => void
    aiAnalysisState: AIAnalysisState
}

function TimeSeriesVisualization({
    data,
    config,
    onSelectionMade,
    selectedColumn,
    onImageCapture,
    onAIAnalysis,
    aiAnalysisState
}: TimeSeriesVisualizationProps) {
    const { t } = useTranslation()
    // 무한 루프 방지용 플래그 - 라인 차트 개별 모드에서만 사용
    const syncInProgress = useRef(false)

    // x축 범위 변경 핸들러 - 모든 차트에 동기화 (컴포넌트 최상위에서 정의)
    const handleRelayout = useCallback((eventData: any, chartIndex: number) => {
        // 라인 차트 개별 모드가 아니면 동기화하지 않음
        if (config.type !== 'line' || config.viewMode !== 'individual') {
            return
        }

        // 동기화 중이면 무시 (무한 루프 방지)
        if (syncInProgress.current) {
            return
        }

        // 1. 기본 x축 범위 동기화 (줌인/줌아웃, 패닝)
        if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
            const start = eventData['xaxis.range[0]']
            const end = eventData['xaxis.range[1]']

            syncInProgress.current = true
            // 다른 모든 차트의 x축 범위를 동기화
            data.forEach((_, index) => {
                if (index !== chartIndex) {
                    const chartElement = document.getElementById(`line-chart-${index}`)
                    if (chartElement && (window as any).Plotly) {
                        (window as any).Plotly.relayout(chartElement, {
                            'xaxis.range': [start, end]
                        })
                    }
                }
            })
            setTimeout(() => {
                syncInProgress.current = false
            }, 100)
            return
        }

        // 2. 오토스케일/리셋 이벤트 동기화 (더블클릭, 홈 버튼, 오토스케일 버튼)
        if (eventData['xaxis.autorange'] === true ||
            (eventData.hasOwnProperty('xaxis.autorange') && !eventData['xaxis.range[0]'])) {

            syncInProgress.current = true
            // 다른 모든 차트에 오토스케일 적용
            data.forEach((_, index) => {
                if (index !== chartIndex) {
                    const chartElement = document.getElementById(`line-chart-${index}`)
                    if (chartElement && (window as any).Plotly) {
                        (window as any).Plotly.relayout(chartElement, {
                            'xaxis.autorange': true
                        })
                    }
                }
            })
            setTimeout(() => {
                syncInProgress.current = false
            }, 100)
            return
        }
    }, [config.type, config.viewMode, data])

    if (data.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-muted-foreground">{t('iotPrismDemo.visualization.noData')}</p>
            </div>
        )
    }

            // 라인차트 - 개별 모드
    if (config.type === 'line' && config.viewMode === 'individual') {

        return (
            <div className="space-y-4">
                {data.map((series, index) => {
                    const isSelected = selectedColumn === series.column
                    const isDisabled = selectedColumn && selectedColumn !== series.column

                    return (
                        <div
                            key={series.column}
                            className={`border rounded-lg p-4 transition-all duration-300 ${isSelected
                                ? 'border-accent-blue bg-accent-blue/5'
                                : isDisabled
                                    ? 'border-muted bg-muted/20 opacity-50'
                                    : 'border-border hover:border-accent-blue/50'
                                }`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <h4 className={`font-medium ${isDisabled ? 'text-muted-foreground' : 'text-foreground'}`}>
                                    {series.column}
                                </h4>
                                {onSelectionMade && isSelected && (
                                    <span className="text-xs text-accent-blue bg-accent-blue/10 px-2 py-1 rounded">
                                        {t('iotPrismDemo.shapeComparison.selectedTarget')}
                                    </span>
                                )}
                                {onSelectionMade && isDisabled && (
                                    <span className="text-xs text-muted-foreground bg-muted/30 px-2 py-1 rounded">
                                        {t('iotPrismDemo.shapeComparison.disabled')}
                                    </span>
                                )}
                            </div>
                            <div style={{ height: '300px' }}>
                                                            <Plot
                                divId={`line-chart-${index}`}
                                    data={[{
                                        x: series.x,
                                        y: series.y,
                                        type: 'scatter',
                                        mode: 'lines',
                                        name: series.column,
                                        line: { color: `hsl(${index * 137.5}, 70%, 50%)` }
                                    }]}
                                    layout={{
                                        autosize: true,
                                        margin: { t: 20, r: 20, b: 40, l: 60 },
                                        plot_bgcolor: 'transparent',
                                        paper_bgcolor: 'transparent',
                                        font: { color: '#94a3b8' },
                                        dragmode: onSelectionMade && (!selectedColumn || selectedColumn === series.column) ? 'select' : 'zoom',
                                        selectdirection: 'h',
                                        xaxis: {
                                            title: { text: t('iotPrismDemo.visualization.xAxis') },
                                            gridcolor: '#374151',
                                            color: '#94a3b8'
                                        },
                                        yaxis: {
                                            title: { text: t('iotPrismDemo.visualization.yAxis') },
                                            gridcolor: '#374151',
                                            color: '#94a3b8'
                                        }
                                    }}
                                    config={{
                                        displayModeBar: true,
                                        displaylogo: false,
                                        modeBarButtonsToRemove: onSelectionMade && (!selectedColumn || selectedColumn === series.column) 
                                            ? ['pan2d', 'lasso2d', 'toImage'] 
                                            : ['pan2d', 'lasso2d', 'select2d', 'toImage'],
                                        modeBarButtonsToAdd: [{
                                            name: 'saveToServer',
                                            icon: {
                                                width: 24,
                                                height: 24,
                                                path: 'M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z',
                                                transform: 'translate(0, 0)'
                                            },
                                            title: '차트 이미지 저장',
                                            click: () => {
                                                const chartElement = document.getElementById(`line-chart-${index}`)
                                                if (chartElement && onImageCapture) {
                                                    onImageCapture(chartElement, series.column)
                                                }
                                            }
                                        }]
                                    }}
                                    style={{ width: '100%', height: '100%' }}
                                    onRelayout={(eventData: any) => handleRelayout(eventData, index)}
                                    onSelected={onSelectionMade && (!selectedColumn || selectedColumn === series.column) ? (eventData: any) => {
                                        if (eventData?.range?.x && eventData.range.x.length === 2) {
                                            const [start, end] = eventData.range.x.map((x: any) => new Date(x))
                                            onSelectionMade(series.column, start, end)
                                        }
                                    } : undefined}
                                />
                            </div>
                            
                            {/* AI 분석 섹션 */}
                            <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-border">
                                <div className="flex items-start space-x-4">
                                    <button 
                                        onClick={() => {
                                            const chartElement = document.getElementById(`line-chart-${index}`)
                                            if (chartElement && onAIAnalysis) {
                                                onAIAnalysis(chartElement, series.column, 'line')
                                            }
                                        }}
                                        disabled={aiAnalysisState[`line-chart-${index}`]?.isAnalyzing}
                                        className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
                                    >
                                        {aiAnalysisState[`line-chart-${index}`]?.isAnalyzing ? (
                                            <>
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                분석 중...
                                            </>
                                        ) : (
                                            <>
                                                <Activity className="w-4 h-4 mr-2" />
                                                {t('iotPrismDemo.aiAnalysis.title')}
                                            </>
                                        )}
                                    </button>
                                    <div className="flex-1 min-h-[3rem] flex items-center">
                                        {aiAnalysisState[`line-chart-${index}`]?.result ? (
                                            <div className="w-full">
                                                <div className="text-sm text-foreground mb-2 font-medium">
                                                    ✨ AI 분석 결과
                                                </div>
                                                <div className="text-sm text-muted-foreground leading-relaxed bg-accent-blue/5 p-3 rounded border border-accent-blue/20 whitespace-pre-wrap">
                                                    {aiAnalysisState[`line-chart-${index}`]?.result?.analysisText}
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-2">
                                                    {new Date(aiAnalysisState[`line-chart-${index}`]?.result?.timestamp || '').toLocaleString()}
                                                </div>
                                            </div>
                                        ) : aiAnalysisState[`line-chart-${index}`]?.error ? (
                                            <div className="w-full">
                                                <div className="text-sm text-accent-orange mb-2 font-medium">
                                                    ⚠️ 분석 오류
                                                </div>
                                                <div className="text-sm text-accent-orange bg-accent-orange/10 p-3 rounded border border-accent-orange/20 whitespace-pre-wrap">
                                                    {aiAnalysisState[`line-chart-${index}`]?.error}
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-muted-foreground text-sm leading-relaxed">
                                                {t('iotPrismDemo.aiAnalysis.description')}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        )
    }

    // 라인차트 - 겹침 모드
    if (config.type === 'line' && config.viewMode === 'overlay') {
        return (
            <div>
                <div style={{ height: '500px' }}>
                    <Plot
                        divId="line-overlay-chart"
                        data={data.map((series, index) => ({
                            x: series.x,
                            y: series.y,
                            type: 'scatter',
                            mode: 'lines',
                            name: series.column,
                            line: {
                                color: `hsl(${index * 137.5}, 70%, 50%)`,
                                width: 2
                            }
                        }))}
                        layout={{
                            autosize: true,
                            margin: { t: 40, r: 40, b: 60, l: 80 },
                            plot_bgcolor: 'transparent',
                            paper_bgcolor: 'transparent',
                            font: { color: '#94a3b8' },
                            xaxis: {
                                title: { text: t('iotPrismDemo.visualization.xAxis') },
                                gridcolor: '#374151',
                                color: '#94a3b8'
                            },
                            yaxis: {
                                title: { text: t('iotPrismDemo.visualization.yAxis') },
                                gridcolor: '#374151',
                                color: '#94a3b8'
                            },
                            legend: {
                                font: { color: '#94a3b8' }
                            }
                        }}
                        config={{
                            displayModeBar: true,
                            displaylogo: false,
                            modeBarButtonsToRemove: ['lasso2d', 'toImage'],
                            modeBarButtonsToAdd: [{
                                name: 'saveToServer',
                                icon: {
                                    width: 24,
                                    height: 24,
                                    path: 'M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z',
                                    transform: 'translate(0, 0)'
                                },
                                title: '차트 이미지 저장',
                                click: () => {
                                    const chartElement = document.getElementById('line-overlay-chart')
                                    if (chartElement && onImageCapture) {
                                        onImageCapture(chartElement, 'overlay-chart')
                                    }
                                }
                            }]
                        }}
                        style={{ width: '100%', height: '100%' }}
                    />
                </div>
                
                {/* AI 분석 섹션 */}
                <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-border">
                    <div className="flex items-start space-x-4">
                        <button 
                            onClick={() => {
                                const chartElement = document.getElementById('line-overlay-chart')
                                if (chartElement && onAIAnalysis) {
                                    onAIAnalysis(chartElement, 'overlay-chart', 'line')
                                }
                            }}
                            disabled={aiAnalysisState['line-overlay-chart']?.isAnalyzing}
                            className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
                        >
                            {aiAnalysisState['line-overlay-chart']?.isAnalyzing ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                    분석 중...
                                </>
                            ) : (
                                <>
                                    <Activity className="w-4 h-4 mr-2" />
                                    {t('iotPrismDemo.aiAnalysis.title')}
                                </>
                            )}
                        </button>
                        <div className="flex-1 min-h-[3rem] flex items-center">
                            {aiAnalysisState['line-overlay-chart']?.result ? (
                                <div className="w-full">
                                    <div className="text-sm text-foreground mb-2 font-medium">
                                        ✨ AI 분석 결과
                                    </div>
                                    <div className="text-sm text-muted-foreground leading-relaxed bg-accent-blue/5 p-3 rounded border border-accent-blue/20 whitespace-pre-wrap">
                                        {aiAnalysisState['line-overlay-chart']?.result?.analysisText}
                                    </div>
                                    <div className="text-xs text-muted-foreground mt-2">
                                        {new Date(aiAnalysisState['line-overlay-chart']?.result?.timestamp || '').toLocaleString()}
                                    </div>
                                </div>
                            ) : aiAnalysisState['line-overlay-chart']?.error ? (
                                <div className="w-full">
                                    <div className="text-sm text-accent-orange mb-2 font-medium">
                                        ⚠️ 분석 오류
                                    </div>
                                    <div className="text-sm text-accent-orange bg-accent-orange/10 p-3 rounded border border-accent-orange/20 whitespace-pre-wrap">
                                        {aiAnalysisState['line-overlay-chart']?.error}
                                    </div>
                                </div>
                            ) : (
                                <p className="text-muted-foreground text-sm leading-relaxed">
                                    {t('iotPrismDemo.aiAnalysis.description')}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    // 박스플롯 - 컬럼별 개별 차트 (시간 단위별 그룹화)
    if (config.type === 'box') {
        // 시간 단위별 데이터 그룹화 함수
        const groupDataByTimeUnit = (xData: any[], yData: number[], timeUnit: TimeUnit) => {
            const groups: { [key: string]: number[] } = {}
            const groupLabels: string[] = []

            xData.forEach((timestamp, index) => {
                const date = new Date(timestamp)
                let groupKey: string

                switch (timeUnit) {
                    case 'hour':
                        groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}시`
                        break
                    case 'day':
                        groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
                        break
                    case 'week':
                        const weekStart = new Date(date)
                        weekStart.setDate(date.getDate() - date.getDay())
                        groupKey = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')} 주`
                        break
                    case 'month':
                        groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
                        break
                    default:
                        groupKey = date.toISOString().split('T')[0]
                }

                if (!groups[groupKey]) {
                    groups[groupKey] = []
                    groupLabels.push(groupKey)
                }
                groups[groupKey].push(yData[index])
            })

            return { groups, groupLabels: groupLabels.sort() }
        }

        return (
            <div className="space-y-4">
                {data.map((series, index) => {
                    const { groups, groupLabels } = groupDataByTimeUnit(series.x, series.y, config.timeUnit)

                    // 각 시간 그룹별로 박스플롯 데이터 생성
                    const boxData = groupLabels.map(label => ({
                        y: groups[label],
                        name: label,
                        type: 'box' as const,
                        boxpoints: 'outliers' as const,
                        marker: { color: `hsl(${index * 137.5}, 70%, 50%)` },
                        line: { color: `hsl(${index * 137.5}, 70%, 50%)` }
                    }))

                    return (
                        <div key={series.column} className="border border-border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="font-medium text-foreground">{series.column}</h4>
                                <span className="text-xs text-muted-foreground">
                                    {t(`iotPrismDemo.chartSettings.timeUnits.${config.timeUnit}`)} ({groupLabels.length}{t('iotPrismDemo.chartSettings.timeUnits.groupSuffix')})
                                </span>
                            </div>
                            <div style={{ height: '400px' }}>
                                <Plot
                                    divId={`box-chart-${index}`}
                                    data={boxData}
                                    layout={{
                                        autosize: true,
                                        margin: { t: 20, r: 20, b: 80, l: 60 },
                                        plot_bgcolor: 'transparent',
                                        paper_bgcolor: 'transparent',
                                        font: { color: '#94a3b8' },
                                        xaxis: {
                                            title: { text: t(`iotPrismDemo.chartSettings.timeUnits.${config.timeUnit}Label`) },
                                            gridcolor: '#374151',
                                            color: '#94a3b8',
                                            tickangle: groupLabels.length > 10 ? -45 : 0
                                        },
                                        yaxis: {
                                            title: { text: series.column },
                                            gridcolor: '#374151',
                                            color: '#94a3b8'
                                        },
                                        showlegend: false
                                    }}
                                    config={{
                                        displayModeBar: true,
                                        displaylogo: false,
                                        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
                                        modeBarButtonsToAdd: [{
                                            name: 'saveToServer',
                                            icon: {
                                                width: 24,
                                                height: 24,
                                                path: 'M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z',
                                                transform: 'translate(0, 0)'
                                            },
                                            title: '차트 이미지 저장',
                                            click: () => {
                                                const chartElement = document.getElementById(`box-chart-${index}`)
                                                if (chartElement && onImageCapture) {
                                                    onImageCapture(chartElement, series.column)
                                                }
                                            }
                                        }]
                                    }}
                                    style={{ width: '100%', height: '100%' }}
                                />
                            </div>
                            
                            {/* AI 분석 섹션 */}
                            <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-border">
                                <div className="flex items-start space-x-4">
                                    <button 
                                        onClick={() => {
                                            const chartElement = document.getElementById(`box-chart-${index}`)
                                            if (chartElement && onAIAnalysis) {
                                                onAIAnalysis(chartElement, series.column, 'box')
                                            }
                                        }}
                                        disabled={aiAnalysisState[`box-chart-${index}`]?.isAnalyzing}
                                        className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
                                    >
                                        {aiAnalysisState[`box-chart-${index}`]?.isAnalyzing ? (
                                            <>
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                분석 중...
                                            </>
                                        ) : (
                                            <>
                                                <Activity className="w-4 h-4 mr-2" />
                                                {t('iotPrismDemo.aiAnalysis.title')}
                                            </>
                                        )}
                                    </button>
                                    <div className="flex-1 min-h-[3rem] flex items-center">
                                        {aiAnalysisState[`box-chart-${index}`]?.result ? (
                                            <div className="w-full">
                                                <div className="text-sm text-foreground mb-2 font-medium">
                                                    ✨ AI 분석 결과
                                                </div>
                                                <div className="text-sm text-muted-foreground leading-relaxed bg-accent-blue/5 p-3 rounded border border-accent-blue/20 whitespace-pre-wrap">
                                                    {aiAnalysisState[`box-chart-${index}`]?.result?.analysisText}
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-2">
                                                    {new Date(aiAnalysisState[`box-chart-${index}`]?.result?.timestamp || '').toLocaleString()}
                                                </div>
                                            </div>
                                        ) : aiAnalysisState[`box-chart-${index}`]?.error ? (
                                            <div className="w-full">
                                                <div className="text-sm text-accent-orange mb-2 font-medium">
                                                    ⚠️ 분석 오류
                                                </div>
                                                <div className="text-sm text-accent-orange bg-accent-orange/10 p-3 rounded border border-accent-orange/20 whitespace-pre-wrap">
                                                    {aiAnalysisState[`box-chart-${index}`]?.error}
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-muted-foreground text-sm leading-relaxed">
                                                {t('iotPrismDemo.aiAnalysis.description')}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        )
    }

    // 산점도 - 컬럼별 개별 차트
    if (config.type === 'scatter') {
        return (
            <div className="space-y-4">
                {data.map((series, index) => {
                    // 성능 최적화: 데이터 포인트가 너무 많으면 샘플링
                    const maxPoints = 2000
                    let sampledX = series.x
                    let sampledY = series.y

                    if (series.x.length > maxPoints) {
                        const step = Math.ceil(series.x.length / maxPoints)
                        sampledX = series.x.filter((_, i) => i % step === 0)
                        sampledY = series.y.filter((_, i) => i % step === 0)
                    }

                    return (
                        <div key={series.column} className="border border-border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="font-medium text-foreground">{series.column}</h4>
                                {series.x.length > maxPoints && (
                                    <span className="text-xs text-muted-foreground">
                                        {sampledX.length}{t('iotPrismDemo.chartSettings.performance.pointsDisplayed')} ({t('iotPrismDemo.chartSettings.performance.totalPoints')} {series.x.length}{t('iotPrismDemo.chartSettings.performance.pointsSuffix')})
                                    </span>
                                )}
                            </div>
                            <div style={{ height: '300px' }}>
                                <Plot
                                    divId={`scatter-chart-${index}`}
                                    data={[{
                                        x: sampledX,
                                        y: sampledY,
                                        type: 'scatter',
                                        mode: 'markers',
                                        name: series.column,
                                        marker: {
                                            size: 6,
                                            color: `hsl(${index * 137.5}, 70%, 50%)`
                                        }
                                    }]}
                                    layout={{
                                        autosize: true,
                                        margin: { t: 20, r: 20, b: 40, l: 60 },
                                        plot_bgcolor: 'transparent',
                                        paper_bgcolor: 'transparent',
                                        font: { color: '#94a3b8' },
                                        xaxis: {
                                            title: { text: t('iotPrismDemo.visualization.xAxis') },
                                            gridcolor: '#374151',
                                            color: '#94a3b8'
                                        },
                                        yaxis: {
                                            title: { text: t('iotPrismDemo.visualization.yAxis') },
                                            gridcolor: '#374151',
                                            color: '#94a3b8'
                                        },
                                        showlegend: false
                                    }}
                                    config={{
                                        displayModeBar: true,
                                        displaylogo: false,
                                        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
                                        modeBarButtonsToAdd: [{
                                            name: 'saveToServer',
                                            icon: {
                                                width: 24,
                                                height: 24,
                                                path: 'M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z',
                                                transform: 'translate(0, 0)'
                                            },
                                            title: '차트 이미지 저장',
                                            click: () => {
                                                const chartElement = document.getElementById(`scatter-chart-${index}`)
                                                if (chartElement && onImageCapture) {
                                                    onImageCapture(chartElement, series.column)
                                                }
                                            }
                                        }]
                                    }}
                                    style={{ width: '100%', height: '100%' }}
                                />
                            </div>
                            
                            {/* AI 분석 섹션 */}
                            <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-border">
                                <div className="flex items-start space-x-4">
                                    <button 
                                        onClick={() => {
                                            const chartElement = document.getElementById(`scatter-chart-${index}`)
                                            if (chartElement && onAIAnalysis) {
                                                onAIAnalysis(chartElement, series.column, 'scatter')
                                            }
                                        }}
                                        disabled={aiAnalysisState[`scatter-chart-${index}`]?.isAnalyzing}
                                        className="flex items-center px-4 py-2 bg-accent-blue hover:bg-accent-blue/80 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
                                    >
                                        {aiAnalysisState[`scatter-chart-${index}`]?.isAnalyzing ? (
                                            <>
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                분석 중...
                                            </>
                                        ) : (
                                            <>
                                                <Activity className="w-4 h-4 mr-2" />
                                                {t('iotPrismDemo.aiAnalysis.title')}
                                            </>
                                        )}
                                    </button>
                                    <div className="flex-1 min-h-[3rem] flex items-center">
                                        {aiAnalysisState[`scatter-chart-${index}`]?.result ? (
                                            <div className="w-full">
                                                <div className="text-sm text-foreground mb-2 font-medium">
                                                    ✨ AI 분석 결과
                                                </div>
                                                <div className="text-sm text-muted-foreground leading-relaxed bg-accent-blue/5 p-3 rounded border border-accent-blue/20 whitespace-pre-wrap">
                                                    {aiAnalysisState[`scatter-chart-${index}`]?.result?.analysisText}
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-2">
                                                    {new Date(aiAnalysisState[`scatter-chart-${index}`]?.result?.timestamp || '').toLocaleString()}
                                                </div>
                                            </div>
                                        ) : aiAnalysisState[`scatter-chart-${index}`]?.error ? (
                                            <div className="w-full">
                                                <div className="text-sm text-accent-orange mb-2 font-medium">
                                                    ⚠️ 분석 오류
                                                </div>
                                                <div className="text-sm text-accent-orange bg-accent-orange/10 p-3 rounded border border-accent-orange/20 whitespace-pre-wrap">
                                                    {aiAnalysisState[`scatter-chart-${index}`]?.error}
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-muted-foreground text-sm leading-relaxed">
                                                {t('iotPrismDemo.aiAnalysis.description')}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        )
    }

    // 기본 케이스 (혹시 모를 경우를 위한 fallback)
    return (
        <div className="text-center py-8">
            <p className="text-muted-foreground">{t('iotPrismDemo.visualization.noData')}</p>
        </div>
    )
}

// ============================
// 형태 비교 시각화 컴포넌트
// ============================

interface ComparisonVisualizationProps {
    segments: ComparisonSegment[]
    onSegmentUpdate: (segments: ComparisonSegment[]) => void
    onImageCapture?: (chartElement: HTMLElement, chartName: string) => void
}

function ComparisonVisualization({ segments, onSegmentUpdate, onImageCapture }: ComparisonVisualizationProps) {
    const { t } = useTranslation()
    const [hoveredSegmentIndex, setHoveredSegmentIndex] = useState<number | null>(null)
    const [selectedSegmentIndex, setSelectedSegmentIndex] = useState<number | null>(null)
    const [isDragging, setIsDragging] = useState(false)
    const [dragStartX, setDragStartX] = useState<number | null>(null)

    if (segments.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-muted-foreground">{t('iotPrismDemo.shapeComparison.instructions')}</p>
            </div>
        )
    }

    // 호버 이벤트 핸들러
    const handleHover = (eventData: any) => {
        if (eventData?.points && eventData.points.length > 0) {
            const curveNumber = eventData.points[0].curveNumber
            setHoveredSegmentIndex(curveNumber)
            console.log('Hovered segment:', curveNumber, segments[curveNumber])
        }
    }

    // 언호버 이벤트 핸들러
    const handleUnhover = () => {
        setHoveredSegmentIndex(null)
    }

    // 클릭 이벤트 핸들러 (드래그를 위한 선택)
    const handleClick = (eventData: any) => {
        if (eventData?.points && eventData.points.length > 0) {
            const curveNumber = eventData.points[0].curveNumber
            setSelectedSegmentIndex(curveNumber === selectedSegmentIndex ? null : curveNumber)
            setIsDragging(false) // 클릭 시 드래그 상태 초기화
            console.log('Selected segment:', curveNumber, segments[curveNumber])
        }
    }

    // 세그먼트 xOffset 업데이트 함수
    const updateSegmentOffset = useCallback((segmentIndex: number, newOffset: number) => {
        const updatedSegments = segments.map((segment, index) =>
            index === segmentIndex
                ? { ...segment, xOffset: newOffset }
                : segment
        )
        onSegmentUpdate(updatedSegments)
        console.log('Updated segment offset:', segmentIndex, newOffset)
    }, [segments, onSegmentUpdate])

    // 드래그 시작 핸들러
    const handleDragStart = (eventData: any) => {
        if (eventData?.points && eventData.points.length > 0) {
            const curveNumber = eventData.points[0].curveNumber
            if (curveNumber === selectedSegmentIndex) {
                setIsDragging(true)
                setDragStartX(eventData.points[0].x)
                console.log('Drag started for segment:', curveNumber, 'at x:', eventData.points[0].x)
            }
        }
    }

    // 드래그 중 핸들러 (Plotly의 onRelayout을 사용)
    const handleRelayout = useCallback((eventData: any) => {
        // Pan 이벤트를 감지하여 선택된 그래프의 위치 업데이트
        if (selectedSegmentIndex !== null && eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
            // x축 범위 변화량을 계산하여 그래프 오프셋에 반영
            const rangeStart = eventData['xaxis.range[0]']
            const rangeEnd = eventData['xaxis.range[1]']

            // 이전 범위와 비교하여 이동량 계산 (간단한 구현)
            // 실제로는 더 정교한 계산이 필요할 수 있습니다
            console.log('Chart panned, new range:', [rangeStart, rangeEnd])

            // 드래그가 감지되면 선택된 그래프의 xOffset을 조금씩 업데이트
            // 이 부분은 사용자의 Pan 동작에 따라 더 정교하게 구현할 수 있습니다
        }
    }, [selectedSegmentIndex])

    // 마우스 업 핸들러 (드래그 종료)
    const handleMouseUp = () => {
        if (isDragging) {
            setIsDragging(false)
            setDragStartX(null)
            console.log('Drag ended')
        }
    }

    // 키보드 드래그 핸들러 (더 정확한 제어)
    const handleKeyboardDrag = useCallback((direction: 'left' | 'right', step: number = 1) => {
        if (selectedSegmentIndex !== null) {
            const currentOffset = segments[selectedSegmentIndex].xOffset
            const newOffset = direction === 'left' ? currentOffset - step : currentOffset + step
            updateSegmentOffset(selectedSegmentIndex, newOffset)
        }
    }, [selectedSegmentIndex, segments, updateSegmentOffset])

    // 키보드 이벤트 리스너
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (selectedSegmentIndex !== null) {
                const step = event.shiftKey ? 10 : 1 // Shift 키로 큰 단위 이동

                switch (event.key) {
                    case 'ArrowLeft':
                        event.preventDefault()
                        handleKeyboardDrag('left', step)
                        break
                    case 'ArrowRight':
                        event.preventDefault()
                        handleKeyboardDrag('right', step)
                        break
                    case 'r':
                    case 'R':
                        if (event.ctrlKey || event.metaKey) {
                            event.preventDefault()
                            updateSegmentOffset(selectedSegmentIndex, 0)
                        }
                        break
                }
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        window.addEventListener('mouseup', handleMouseUp)

        return () => {
            window.removeEventListener('keydown', handleKeyDown)
            window.removeEventListener('mouseup', handleMouseUp)
        }
    }, [selectedSegmentIndex, handleKeyboardDrag, updateSegmentOffset, isDragging])



    // 마우스 휠을 이용한 미세 조정 (선택된 그래프만)
    const handleWheel = useCallback((event: WheelEvent) => {
        if (selectedSegmentIndex !== null) {
            event.preventDefault()
            const delta = event.deltaY > 0 ? 1 : -1
            const step = event.shiftKey ? 5 : 1
            const currentOffset = segments[selectedSegmentIndex].xOffset
            const newOffset = currentOffset + (delta * step)
            updateSegmentOffset(selectedSegmentIndex, newOffset)
        }
    }, [selectedSegmentIndex, segments, updateSegmentOffset])

    // 마우스 휠 이벤트 리스너 추가
    useEffect(() => {
        const chartElement = document.getElementById('comparison-chart')
        if (chartElement && selectedSegmentIndex !== null) {
            chartElement.addEventListener('wheel', handleWheel, { passive: false })
            return () => {
                chartElement.removeEventListener('wheel', handleWheel)
            }
        }
    }, [selectedSegmentIndex, handleWheel])

    return (
        <div className="space-y-4">
            {/* 선택된 세그먼트 컨트롤 (향후 드래그 기능의 기반) */}
            {selectedSegmentIndex !== null && (
                <div className="bg-accent-blue/5 border border-accent-blue/20 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div
                                className="w-4 h-4 rounded"
                                style={{ backgroundColor: segments[selectedSegmentIndex].color }}
                            />
                            <div>
                                <p className="text-sm font-medium text-accent-blue">
                                    {t('iotPrismDemo.shapeComparison.selectedGraph')}: {segments[selectedSegmentIndex].column}
                                    {isDragging && <span className="ml-2 text-xs bg-accent-blue text-white px-2 py-1 rounded">{t('iotPrismDemo.shapeComparison.dragging')}</span>}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {segments[selectedSegmentIndex].startTime.toLocaleString()} ~ {segments[selectedSegmentIndex].endTime.toLocaleString()}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {t('iotPrismDemo.shapeComparison.keyboardInstructions')}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2">
                            <span className="text-xs text-muted-foreground">{t('iotPrismDemo.shapeComparison.positionAdjust')}:</span>
                            <button
                                onClick={() => updateSegmentOffset(selectedSegmentIndex, segments[selectedSegmentIndex].xOffset - 5)}
                                className="px-2 py-1 text-xs bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue rounded transition-colors"
                            >
                                ←
                            </button>
                            <span className="text-xs text-foreground min-w-[3rem] text-center">
                                {segments[selectedSegmentIndex].xOffset}
                            </span>
                            <button
                                onClick={() => updateSegmentOffset(selectedSegmentIndex, segments[selectedSegmentIndex].xOffset + 5)}
                                className="px-2 py-1 text-xs bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue rounded transition-colors"
                            >
                                →
                            </button>
                            <button
                                onClick={() => updateSegmentOffset(selectedSegmentIndex, 0)}
                                className="px-2 py-1 text-xs bg-muted/30 hover:bg-muted/50 text-muted-foreground rounded transition-colors"
                            >
                                {t('iotPrismDemo.shapeComparison.reset')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div style={{ height: '400px' }}>
            <Plot
                divId="comparison-chart"
                data={segments.map((segment, index) => {
                    // 상대적 시간으로 변환 (시작점을 0으로)
                    const relativeX = segment.data.map((_, i) => i + segment.xOffset)
                    const y = segment.data.map(row => row[segment.column])

                    // 호버 및 선택 상태에 따른 스타일 결정
                    const isHovered = hoveredSegmentIndex === index
                    const isSelected = selectedSegmentIndex === index
                    const isOtherHovered = hoveredSegmentIndex !== null && hoveredSegmentIndex !== index
                    const isOtherSelected = selectedSegmentIndex !== null && selectedSegmentIndex !== index

                    return {
                        x: relativeX,
                        y: y,
                        type: 'scatter',
                        mode: 'lines',
                        name: `${segment.column} (${segment.startTime.toLocaleString()})`,
                        line: {
                            color: segment.color,
                            width: isSelected ? 5 : isHovered ? 4 : 2, // 선택 > 호버 > 기본 순으로 두께
                        },
                        opacity: isOtherHovered || isOtherSelected ? 0.2 : isSelected ? 1 : 0.8 // 선택된 그래프 강조
                    }
                })}
                layout={{
                    autosize: true,
                    margin: { t: 40, r: 40, b: 60, l: 80 },
                    plot_bgcolor: 'transparent',
                    paper_bgcolor: 'transparent',
                    font: { color: '#94a3b8' },
                    dragmode: selectedSegmentIndex !== null ? 'pan' : 'zoom', // 선택된 그래프가 있으면 pan 모드
                    xaxis: {
                        title: { text: t('iotPrismDemo.shapeComparison.relativeTime') },
                        gridcolor: '#374151',
                        color: '#94a3b8'
                    },
                    yaxis: {
                        title: { text: t('iotPrismDemo.visualization.yAxis') },
                        gridcolor: '#374151',
                        color: '#94a3b8'
                    },
                    legend: {
                        font: { color: '#94a3b8' }
                    },
                    hovermode: 'closest' // 가장 가까운 포인트에 호버
                }}
                config={{
                    displayModeBar: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage'],
                    modeBarButtonsToAdd: [{
                        name: 'saveToServer',
                        icon: {
                            width: 24,
                            height: 24,
                            path: 'M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z',
                            transform: 'translate(0, 0)'
                        },
                        title: '차트 이미지 저장',
                        click: () => {
                            const chartElement = document.getElementById('comparison-chart')
                            if (chartElement && onImageCapture) {
                                onImageCapture(chartElement, 'comparison-chart')
                            }
                        }
                    }]
                }}
                style={{ width: '100%', height: '100%' }}
                onHover={handleHover}
                onUnhover={handleUnhover}
                onClick={handleClick}
                onRelayout={handleRelayout}
            />
        </div>
        </div>
    )
}

// ============================
// 메인 컴포넌트
// ============================

export default function IoTPrismDemoPage() {
  const { t, language } = useTranslation()
    const [csvData, setCsvData] = useState<CSVData | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [dataConfig, setDataConfig] = useState<DataConfig>({
        timestampColumn: '',
        visualizationColumns: [],
        excludeColumns: []
    })
    const [chartConfig, setChartConfig] = useState<ChartConfig>({
        type: 'line',
        viewMode: 'individual',
        timeUnit: 'hour'
    })
    const [comparisonEnabled, setComparisonEnabled] = useState(false)
    const [comparisonSegments, setComparisonSegments] = useState<ComparisonSegment[]>([])
    const [selectedColumn, setSelectedColumn] = useState<string>('')
    const [aiAnalysisState, setAiAnalysisState] = useState<AIAnalysisState>({})

    // 데이터 통계
    const dataStats = {
        totalRows: csvData?.rowCount || 0,
        totalColumns: csvData?.colCount || 0,
        timeRange: csvData && dataConfig.timestampColumn ? getTimeRange(csvData, dataConfig.timestampColumn) : 'N/A',
        selectedColumns: dataConfig.visualizationColumns.length
    }

    // 시간 범위 계산 함수
    function getTimeRange(data: CSVData, timestampColumn: string): string {
        if (!data.data.length || !timestampColumn) return 'N/A'

        const timestamps = data.data
            .map(row => new Date(row[timestampColumn]))
            .filter(date => !isNaN(date.getTime()))
            .sort((a, b) => a.getTime() - b.getTime())

        if (timestamps.length === 0) return 'N/A'

        const start = timestamps[0].toLocaleDateString('ko-KR')
        const end = timestamps[timestamps.length - 1].toLocaleDateString('ko-KR')
        return `${start} ~ ${end}`
    }

    // 파일 로드 핸들러
    const handleFileLoad = useCallback((data: CSVData) => {
        setIsLoading(true)

        setTimeout(() => {
            setCsvData(data)
            setDataConfig({
                timestampColumn: '',
                visualizationColumns: [],
                excludeColumns: []
            })
            setComparisonSegments([])
            setIsLoading(false)
        }, 1000)
    }, [])

    // 타임스탬프 컬럼이 설정되면 데이터를 시간 순으로 정렬
    useEffect(() => {
        if (csvData && dataConfig.timestampColumn) {
            console.log('타임스탬프 컬럼 설정됨, 데이터 정렬 중:', dataConfig.timestampColumn)

            // 타임스탬프 컬럼을 기준으로 데이터 정렬
            const sortedData = [...csvData.data].sort((a, b) => {
                const dateA = new Date(a[dataConfig.timestampColumn])
                const dateB = new Date(b[dataConfig.timestampColumn])

                // 유효하지 않은 날짜는 맨 뒤로
                if (isNaN(dateA.getTime()) && isNaN(dateB.getTime())) return 0
                if (isNaN(dateA.getTime())) return 1
                if (isNaN(dateB.getTime())) return -1

                return dateA.getTime() - dateB.getTime()
            })

            // 정렬된 데이터로 csvData 업데이트
            setCsvData(prev => prev ? {
                ...prev,
                data: sortedData
            } : null)

            console.log('데이터 정렬 완료. 총', sortedData.length, '개 행 정렬됨')
        }
    }, [csvData?.filename, dataConfig.timestampColumn]) // csvData 전체가 아닌 filename으로 파일 변경 감지

    // 차트 설정 변경 시 형태 비교 상태 초기화
    useEffect(() => {
        // 라인 차트 개별 모드가 아닌 경우 형태 비교 기능 비활성화
        if (chartConfig.type !== 'line' || chartConfig.viewMode !== 'individual') {
            if (comparisonEnabled) {
                console.log('차트 유형/모드 변경으로 인한 형태 비교 비활성화:', chartConfig.type, chartConfig.viewMode)
                setComparisonEnabled(false)
                setSelectedColumn('')
                setComparisonSegments([])
            }
        }
    }, [chartConfig.type, chartConfig.viewMode, comparisonEnabled])

    // 시각화 가능한 컬럼 목록 (숫자 타입만)
    const getVisualizableColumns = useCallback(() => {
        if (!csvData) return []

        return csvData.columns.filter(column => {
            if (column === dataConfig.timestampColumn) return false
            if (dataConfig.excludeColumns.includes(column)) return false

            // 첫 번째 데이터 행에서 숫자 타입 확인
            const firstValue = csvData.data[0]?.[column]
            return typeof firstValue === 'number'
        })
    }, [csvData, dataConfig.timestampColumn, dataConfig.excludeColumns])

    // 시간 기준 컬럼 목록 (날짜/시간 타입)
    const getTimestampColumns = useCallback(() => {
        if (!csvData) return []

        return csvData.columns.filter(column => {
            const firstValue = csvData.data[0]?.[column]
            return firstValue instanceof Date ||
                (typeof firstValue === 'string' && !isNaN(new Date(firstValue).getTime()))
        })
    }, [csvData])

    // 차트 데이터 준비 (이미 정렬된 데이터 사용)
    const prepareChartData = useCallback(() => {
        if (!csvData || !dataConfig.timestampColumn || dataConfig.visualizationColumns.length === 0) {
            return []
        }

        // 유효한 타임스탬프를 가진 데이터만 필터링 (이미 정렬되어 있음)
        const filteredData = csvData.data.filter(row => {
            const timestamp = new Date(row[dataConfig.timestampColumn])
            return !isNaN(timestamp.getTime())
        })

        return dataConfig.visualizationColumns.map(column => ({
            column,
            data: filteredData,
            x: filteredData.map(row => new Date(row[dataConfig.timestampColumn])),
            y: filteredData.map(row => row[column])
        }))
    }, [csvData, dataConfig])

    // 형태 비교 세그먼트 추가
    // Plotly modebar 스타일 적용 (useEffect 방식)
    useEffect(() => {
        const styleId = 'plotly-modebar-custom-styles'
        if (!document.getElementById(styleId)) {
            const style = document.createElement('style')
            style.id = styleId
            style.textContent = plotlyModebarStyles
            document.head.appendChild(style)
        }
        
        return () => {
            const existingStyle = document.getElementById(styleId)
            if (existingStyle) {
                document.head.removeChild(existingStyle)
            }
        }
    }, [])

    const addComparisonSegment = useCallback((column: string, startTime: Date, endTime: Date) => {
        if (!csvData || !comparisonEnabled) return

        // 첫 번째 드래그 선택 시 해당 컬럼을 비교 대상으로 자동 선택
        if (!selectedColumn) {
            setSelectedColumn(column)
            console.log('비교 대상 컬럼 자동 선택:', column)
        }

        // 선택된 컬럼과 다른 컬럼에서 드래그 시도 시 무시
        if (selectedColumn && selectedColumn !== column) {
            console.log('비교 대상 컬럼이 아닌 컬럼에서 선택 시도됨. 무시됨:', column)
            return
        }

        const segmentData = csvData.data.filter(row => {
            const timestamp = new Date(row[dataConfig.timestampColumn])
            return timestamp >= startTime && timestamp <= endTime
        })

        const newSegment: ComparisonSegment = {
            id: `${column}-${Date.now()}`,
            column,
            startTime,
            endTime,
            data: segmentData,
            xOffset: 0,
            color: `hsl(${Math.random() * 360}, 70%, 50%)`
        }

        setComparisonSegments(prev => [...prev, newSegment])
    }, [csvData, dataConfig.timestampColumn, comparisonEnabled, selectedColumn])

    // AI 분석 함수 - 차트 이미지를 LLM에 전달
    const analyzeChartWithAI = useCallback(async (chartElement: HTMLElement, chartName: string, chartType: ChartType) => {
        if (!csvData || !chartElement || !(window as any).Plotly) return null

        const chartId = chartElement.id || `chart-${Date.now()}`
        
        // 분석 시작 상태 설정
        setAiAnalysisState(prev => ({
            ...prev,
            [chartId]: {
                isAnalyzing: true,
                result: null,
                error: null
            }
        }))

        try {
            // 1. 차트 이미지 캡처
            const imageData = await (window as any).Plotly.toImage(chartElement, {
                format: 'png',
                width: 1200,
                height: 600,
                scale: 2
            })

            // 2. 차트 메타데이터 준비 (축 범위 정보 포함)
            // ✅ 실제 차트와 동일한 데이터 처리 적용
            const rawChartData = prepareChartData()
            
            // 차트 타입에 따른 실제 데이터 처리 (groupDataByTimeUnit 적용)
            const processChartDataForAnalysis = (data: any[], chartType: ChartType, timeUnit: TimeUnit) => {
                if (!data || data.length === 0) return data

                return data.map(series => {
                    if (chartType === 'box' || (chartType === 'line' && timeUnit !== 'hour')) {
                        // 시간 단위별 그룹화 적용 (실제 차트와 동일한 처리)
                        const groups: { [key: string]: number[] } = {}
                        const groupLabels: string[] = []

                        series.x.forEach((timestamp: Date, index: number) => {
                            const date = new Date(timestamp)
                            let groupKey: string

                            switch (timeUnit) {
                                case 'hour':
                                    groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}시`
                                    break
                                case 'day':
                                    groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
                                    break
                                case 'week':
                                    const weekStart = new Date(date)
                                    weekStart.setDate(date.getDate() - date.getDay())
                                    groupKey = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')} 주`
                                    break
                                case 'month':
                                    groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
                                    break
                                default:
                                    groupKey = date.toISOString().split('T')[0]
                            }

                            if (!groups[groupKey]) {
                                groups[groupKey] = []
                                groupLabels.push(groupKey)
                            }
                            groups[groupKey].push(series.y[index])
                        })

                        // 그룹화된 데이터를 시간 순서로 정렬
                        const sortedLabels = groupLabels.sort()
                        
                        return {
                            ...series,
                            // 그룹별 대표값 생성 (박스플롯은 중앙값, 라인차트는 평균값)
                            x: sortedLabels.map(label => {
                                // 그룹의 첫 번째 타임스탬프를 대표값으로 사용
                                const firstIndex = series.x.findIndex((ts: Date) => {
                                    const date = new Date(ts)
                                    let checkKey: string
                                    switch (timeUnit) {
                                        case 'hour':
                                            checkKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}시`
                                            break
                                        case 'day':
                                            checkKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
                                            break
                                        case 'week':
                                            const weekStart = new Date(date)
                                            weekStart.setDate(date.getDate() - date.getDay())
                                            checkKey = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')} 주`
                                            break
                                        case 'month':
                                            checkKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
                                            break
                                        default:
                                            checkKey = date.toISOString().split('T')[0]
                                    }
                                    return checkKey === label
                                })
                                return firstIndex >= 0 ? series.x[firstIndex] : new Date()
                            }),
                            y: sortedLabels.map(label => {
                                const groupValues = groups[label]
                                if (chartType === 'box') {
                                    // 박스플롯: 중앙값 사용
                                    const sorted = [...groupValues].sort((a, b) => a - b)
                                    const mid = Math.floor(sorted.length / 2)
                                    return sorted.length % 2 === 0 
                                        ? (sorted[mid - 1] + sorted[mid]) / 2 
                                        : sorted[mid]
                                } else {
                                    // 라인차트: 평균값 사용
                                    return groupValues.reduce((sum, val) => sum + val, 0) / groupValues.length
                                }
                            }),
                            groupedData: groups  // 그룹화된 원본 데이터도 포함
                        }
                    }
                    
                    return series  // 원본 데이터 반환 (scatter plot 등)
                })
            }
            
            const chartData = processChartDataForAnalysis(rawChartData, chartType, chartConfig.timeUnit)
            
            // 디버깅: 실제 차트 데이터와 AI 분석용 데이터 비교
            console.log('📊 AI 분석용 데이터 처리 완료:')
            console.log('  🎯 분석 대상 컬럼:', chartName)
            console.log('  📋 원본 데이터:', rawChartData.map(s => ({ column: s.column, points: s.x.length })))
            console.log('  🔄 처리된 데이터:', chartData.map(s => ({ column: s.column, points: s.x.length, hasGroupedData: !!s.groupedData })))
            console.log('  📐 차트 설정:', { type: chartType, timeUnit: chartConfig.timeUnit })

            
            // 실제 데이터에서 축 범위 계산 (시간 단위 정보 포함)
            const calculateAxisRanges = (data: any[]) => {
                if (data.length === 0) return null
                
                const allXValues: Date[] = []
                const allYValues: number[] = []
                
                data.forEach(series => {
                    allXValues.push(...series.x)
                    allYValues.push(...series.y.filter((val: any) => typeof val === 'number' && !isNaN(val)))
                })
                
                if (allXValues.length === 0 || allYValues.length === 0) return null
                
                // X축 범위 (시간)
                const xMin = new Date(Math.min(...allXValues.map(d => d.getTime())))
                const xMax = new Date(Math.max(...allXValues.map(d => d.getTime())))
                
                // Y축 범위 (값)
                const yMin = Math.min(...allYValues)
                const yMax = Math.max(...allYValues)
                const yMean = allYValues.reduce((sum, val) => sum + val, 0) / allYValues.length
                
                // 시간 단위별 분석 정보 계산 (실제 사용된 데이터 기반)
                const timeUnitInfo = calculateTimeUnitInfo(data.length > 0 ? data[0].x : allXValues, chartConfig.timeUnit, chartType)
                
                // 정밀한 시간 범위 계산
                const formatDetailedDateTime = (date: Date) => {
                    return date.toLocaleString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit', 
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false
                    })
                }
                
                // 정밀한 기간 계산
                const calculatePreciseDuration = (startTime: Date, endTime: Date) => {
                    const totalMs = endTime.getTime() - startTime.getTime()
                    
                    const days = Math.floor(totalMs / (1000 * 60 * 60 * 24))
                    const hours = Math.floor((totalMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
                    const minutes = Math.floor((totalMs % (1000 * 60 * 60)) / (1000 * 60))
                    const seconds = Math.floor((totalMs % (1000 * 60)) / 1000)
                    
                    const parts = []
                    if (days > 0) parts.push(`${days}일`)
                    if (hours > 0) parts.push(`${hours}시간`)
                    if (minutes > 0) parts.push(`${minutes}분`)
                    if (seconds > 0 || parts.length === 0) parts.push(`${seconds}초`)
                    
                    return parts.join(' ')
                }
                
                return {
                    xAxis: {
                        min: xMin.toISOString(),
                        max: xMax.toISOString(),
                        range: `${formatDetailedDateTime(xMin)} ~ ${formatDetailedDateTime(xMax)}`,
                        totalDuration: calculatePreciseDuration(xMin, xMax),
                        // ✅ 새로 추가: 정밀 시간 정보
                        preciseInfo: {
                            startDateTime: formatDetailedDateTime(xMin),
                            endDateTime: formatDetailedDateTime(xMax),
                            totalMilliseconds: xMax.getTime() - xMin.getTime(),
                            totalSeconds: Math.floor((xMax.getTime() - xMin.getTime()) / 1000),
                            totalMinutes: Math.floor((xMax.getTime() - xMin.getTime()) / (1000 * 60)),
                            totalHours: Math.floor((xMax.getTime() - xMin.getTime()) / (1000 * 60 * 60)),
                            totalDays: Math.floor((xMax.getTime() - xMin.getTime()) / (1000 * 60 * 60 * 24))
                        }
                    },
                    yAxis: {
                        min: Math.round(yMin * 100) / 100,
                        max: Math.round(yMax * 100) / 100,
                        mean: Math.round(yMean * 100) / 100,
                        range: Math.round((yMax - yMin) * 100) / 100,
                        unit: "수치값"
                    },
                    dataDistribution: {
                        totalPoints: allYValues.length,
                        variance: Math.round(allYValues.reduce((sum, val) => sum + Math.pow(val - yMean, 2), 0) / allYValues.length * 100) / 100
                    },
                    // ✅ 새로 추가: 시간 단위 분석 정보
                    timeUnitAnalysis: timeUnitInfo
                }
            }
            
            // 시간 단위별 분석 정보 계산 함수
            const calculateTimeUnitInfo = (xValues: Date[], timeUnit: string, chartType: string) => {
                if (xValues.length === 0) return null
                
                const sortedTimes = xValues.sort((a, b) => a.getTime() - b.getTime())
                const firstTime = sortedTimes[0]
                const lastTime = sortedTimes[sortedTimes.length - 1]
                
                // 정밀한 시간 단위별 그룹 수 계산
                const calculateGroups = () => {
                    const totalMs = lastTime.getTime() - firstTime.getTime()
                    let unitMs: number
                    let unitName: string
                    let expectedGroups: number
                    let actualDataInterval: number = 0
                    
                    // 실제 데이터 간격 계산 (샘플링을 통한 추정)
                    if (sortedTimes.length > 1) {
                        const sampleSize = Math.min(10, sortedTimes.length - 1)
                        let totalInterval = 0
                        for (let i = 0; i < sampleSize; i++) {
                            totalInterval += sortedTimes[i + 1].getTime() - sortedTimes[i].getTime()
                        }
                        actualDataInterval = totalInterval / sampleSize
                    }
                    
                    switch (timeUnit) {
                        case 'second':
                            unitMs = 1000
                            unitName = '초'
                            expectedGroups = Math.ceil(totalMs / unitMs)
                            break
                        case 'minute':
                            unitMs = 60 * 1000
                            unitName = '분'
                            expectedGroups = Math.ceil(totalMs / unitMs)
                            break
                        case 'hour':
                            unitMs = 60 * 60 * 1000
                            unitName = '시간'
                            expectedGroups = Math.ceil(totalMs / unitMs)
                            break
                        case 'day':
                            unitMs = 24 * 60 * 60 * 1000
                            unitName = '일'
                            expectedGroups = Math.ceil(totalMs / unitMs)
                            break
                        case 'week':
                            unitMs = 7 * 24 * 60 * 60 * 1000
                            unitName = '주'
                            expectedGroups = Math.ceil(totalMs / unitMs)
                            break
                        case 'month':
                            // 실제 월 단위 계산 (정확한 월 수)
                            const startDate = new Date(firstTime)
                            const endDate = new Date(lastTime)
                            expectedGroups = (endDate.getFullYear() - startDate.getFullYear()) * 12 + 
                                           (endDate.getMonth() - startDate.getMonth()) + 1
                            unitMs = totalMs / expectedGroups // 평균 월 길이
                            unitName = '월'
                            break
                        default:
                            unitMs = 24 * 60 * 60 * 1000
                            unitName = '일'
                            expectedGroups = Math.ceil(totalMs / unitMs)
                    }
                    
                    // 데이터 간격 분석
                    const formatInterval = (intervalMs: number) => {
                        if (intervalMs < 1000) return `${Math.round(intervalMs)}ms`
                        if (intervalMs < 60000) return `${Math.round(intervalMs / 1000)}초`
                        if (intervalMs < 3600000) return `${Math.round(intervalMs / 60000)}분`
                        if (intervalMs < 86400000) return `${Math.round(intervalMs / 3600000)}시간`
                        return `${Math.round(intervalMs / 86400000)}일`
                    }
                    
                    return {
                        unit: timeUnit,
                        unitName: unitName,
                        expectedGroups: expectedGroups,
                        avgPointsPerGroup: Math.round(xValues.length / expectedGroups * 100) / 100,
                        // ✅ 새로 추가: 정밀한 시간 간격 정보
                        actualDataInterval: actualDataInterval,
                        actualDataIntervalFormatted: formatInterval(actualDataInterval),
                        unitMs: unitMs,
                        totalTimeSpanMs: totalMs,
                        dataResolution: actualDataInterval > 0 ? Math.round(unitMs / actualDataInterval * 100) / 100 : 'N/A'
                    }
                }
                
                const groupInfo = calculateGroups()
                
                // 정밀한 차트 타입별 분석 힌트
                const getAnalysisHint = () => {
                    const resolutionInfo = groupInfo.actualDataInterval > 0 
                        ? ` (실제 데이터 간격: ${groupInfo.actualDataIntervalFormatted})` 
                        : ''
                    
                    switch (chartType) {
                        case 'line':
                            return `시계열 데이터를 ${groupInfo.unitName} 단위로 분석 - 트렌드 및 시간대별 패턴 중심${resolutionInfo}`
                        case 'box':
                            return `${groupInfo.unitName} 단위 박스플롯 - 각 ${groupInfo.unitName}별 분포 특성 및 이상치 분석 중심${resolutionInfo}`
                        case 'scatter':
                            return `${groupInfo.unitName} 단위 산점도 - 시간 경과에 따른 값 분산 패턴 분석 중심${resolutionInfo}`
                        default:
                            return `${groupInfo.unitName} 단위 데이터 분석${resolutionInfo}`
                    }
                }
                
                return {
                    timeUnit: timeUnit,
                    unitName: groupInfo.unitName,
                    expectedGroups: groupInfo.expectedGroups,
                    avgPointsPerGroup: groupInfo.avgPointsPerGroup,
                    analysisHint: getAnalysisHint(),
                    chartType: chartType,
                    // ✅ 새로 추가: 정밀한 시간 분석 정보
                    preciseTimeInfo: {
                        actualDataInterval: groupInfo.actualDataInterval,
                        actualDataIntervalFormatted: groupInfo.actualDataIntervalFormatted,
                        unitMs: groupInfo.unitMs,
                        totalTimeSpanMs: groupInfo.totalTimeSpanMs,
                        dataResolution: groupInfo.dataResolution,
                        samplingRate: groupInfo.actualDataInterval > 0 
                            ? `${Math.round(1000 / groupInfo.actualDataInterval * 100) / 100}/초` 
                            : 'N/A'
                    }
                }
            }
            
            // ✅ 특정 컬럼(차트)에 대한 축 범위 계산 (컬럼별 개별 분석)
            const targetColumnData = chartData.find(series => series.column === chartName)
            
            // 대상 컬럼 데이터 확인 로그
            if (targetColumnData) {
                const yValues = targetColumnData.y.filter((val: any) => typeof val === 'number' && !isNaN(val))
                const yMin = Math.min(...yValues)
                const yMax = Math.max(...yValues)
                const yMean = yValues.reduce((sum: number, val: number) => sum + val, 0) / yValues.length
                const variance = yValues.reduce((sum: number, val: number) => sum + Math.pow(val - yMean, 2), 0) / yValues.length
                
                console.log('  ✅ 대상 컬럼 데이터 발견:', { 
                    column: targetColumnData.column, 
                    points: targetColumnData.x.length,
                    yMin: Math.round(yMin * 100) / 100,
                    yMax: Math.round(yMax * 100) / 100,
                    yMean: Math.round(yMean * 100) / 100,
                    yRange: Math.round((yMax - yMin) * 100) / 100,
                    variance: Math.round(variance * 100) / 100
                })
            } else {
                console.log('  ⚠️ 대상 컬럼을 찾지 못함, 전체 데이터 사용')
            }
            
            const axisRanges = calculateAxisRanges(targetColumnData ? [targetColumnData] : chartData)
            
            const metadata = {
                chartName,
                chartType,
                filename: csvData.filename,
                // ✅ 분석 대상 컬럼 정보 추가
                targetColumn: chartName,
                dataConfig: {
                    timestampColumn: dataConfig.timestampColumn,
                    visualizationColumns: dataConfig.visualizationColumns,
                    targetColumn: chartName, // 실제 분석 대상 컬럼
                    timeUnit: chartConfig.timeUnit
                },
                statistics: {
                    originalDataPointsCount: rawChartData.reduce((total, series) => total + series.x.length, 0),
                    processedDataPointsCount: chartData.reduce((total, series) => total + series.x.length, 0),
                    columnCount: dataConfig.visualizationColumns.length,
                    timeRange: dataStats.timeRange,
                    dataProcessingApplied: chartType === 'box' || (chartType === 'line' && chartConfig.timeUnit !== 'hour')
                },
                // ✅ 새로 추가: 실제 축 범위 정보
                axisRanges: axisRanges,
                // ✅ 새로 추가: 데이터 처리 방식 정보
                dataProcessing: {
                    chartType: chartType,
                    timeUnit: chartConfig.timeUnit,
                    isGrouped: chartType === 'box' || (chartType === 'line' && chartConfig.timeUnit !== 'hour'),
                    groupingMethod: (() => {
                        if (chartType === 'box') return 'statistical_aggregation';
                        if (chartType === 'line' && chartConfig.timeUnit !== 'hour') return 'average_aggregation';
                        return 'none';
                    })(),
                    description: (() => {
                        if (chartType === 'box') return `Data grouped by ${chartConfig.timeUnit} units for statistical analysis`;
                        if (chartType === 'line' && chartConfig.timeUnit !== 'hour') return `Data grouped by ${chartConfig.timeUnit} units with average values`;
                        return 'Original data points displayed individually';
                    })()
                }
            }
            
            // 디버깅용 로그 - 정밀한 시간 정보 포함
            console.log('📊 차트 축 범위 정보:', axisRanges)
            if (axisRanges?.xAxis?.preciseInfo) {
                console.log('⏰ 정밀한 시간 정보:', {
                    시작시간: axisRanges.xAxis.preciseInfo.startDateTime,
                    종료시간: axisRanges.xAxis.preciseInfo.endDateTime,
                    총시간ms: axisRanges.xAxis.preciseInfo.totalMilliseconds,
                    총시간초: axisRanges.xAxis.preciseInfo.totalSeconds,
                    총시간분: axisRanges.xAxis.preciseInfo.totalMinutes,
                    총시간시간: axisRanges.xAxis.preciseInfo.totalHours,
                    총시간일: axisRanges.xAxis.preciseInfo.totalDays
                })
            }
            if (axisRanges?.timeUnitAnalysis?.preciseTimeInfo) {
                console.log('🔍 데이터 정밀도:', {
                    실제간격: axisRanges.timeUnitAnalysis.preciseTimeInfo.actualDataIntervalFormatted,
                    샘플링레이트: axisRanges.timeUnitAnalysis.preciseTimeInfo.samplingRate,
                    데이터해상도: axisRanges.timeUnitAnalysis.preciseTimeInfo.dataResolution
                })
            }

            // 3. LLM API 호출
            const formData = new FormData()
            const base64Data = imageData.split(',')[1]
            const blob = new Blob([atob(base64Data)], { type: 'image/png' })
            
            formData.append('image', blob, `${chartName}-analysis.png`)
            formData.append('metadata', JSON.stringify(metadata))
            
            const promptData = {
                type: 'chart_analysis',
                language: language, // 현재 언어 설정 사용
                analysisType: 'comprehensive' // trend, anomaly, pattern, comprehensive
            }
            
            formData.append('prompt', JSON.stringify(promptData))

            // 프록시 우회하고 직접 백엔드 호출 (socket hang up 방지)
            const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            
            // 수동 타임아웃 설정 (5분)
            const controller = new AbortController()
            const timeoutId = setTimeout(() => {
                controller.abort()
            }, 300000) // 5분
            
            const response = await fetch(`${backendUrl}/api/v1/ai/analyze-chart`, {
                method: 'POST',
                body: formData,
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json',
                }
            })
            
            clearTimeout(timeoutId)

            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`)
            }

            const result = await response.json()
            
            if (result.success) {
                const analysisResult: AIAnalysisResult = {
                    id: `analysis-${Date.now()}`,
                    chartName,
                    chartType,
                    analysisText: result.analysis,
                    timestamp: new Date().toISOString(),
                    confidence: result.confidence
                }

                // 분석 완료 상태 설정
                setAiAnalysisState(prev => ({
                    ...prev,
                    [chartId]: {
                        isAnalyzing: false,
                        result: analysisResult,
                        error: null
                    }
                }))

                return analysisResult
            } else {
                throw new Error(result.error || 'Analysis failed')
            }

        } catch (error: any) {
            console.error('Chart AI analysis failed:', error)
            
            // 에러 상태 설정
            setAiAnalysisState(prev => ({
                ...prev,
                [chartId]: {
                    isAnalyzing: false,
                    result: null,
                    error: error.message || 'AI 분석 중 오류가 발생했습니다.'
                }
            }))

            return null
        }
    }, [csvData, chartConfig, dataConfig, dataStats, prepareChartData, language])

    // 개별 차트 이미지 캡처 및 서버 저장 함수
    const captureAndSaveChart = useCallback(async (chartElement: HTMLElement, chartName: string) => {
        if (!csvData || !chartElement || !(window as any).Plotly) return null

        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
            
            // Plotly.toImage를 사용하여 이미지 생성
            const imageData = await (window as any).Plotly.toImage(chartElement, {
                format: 'png',
                width: 1200,
                height: 600,
                scale: 2
            })

            // base64 데이터에서 헤더 제거
            const base64Data = imageData.split(',')[1]
            
            // 서버에 이미지 업로드
            const formData = new FormData()
            const blob = new Blob([atob(base64Data)], { type: 'image/png' })
            
            const chartId = chartElement.id || `chart-${Date.now()}`
            const filename = `${csvData.filename.replace('.csv', '')}-${chartName}-${timestamp}.png`
            
            formData.append('image', blob, filename)
            formData.append('metadata', JSON.stringify({
                originalFilename: csvData.filename,
                chartType: chartConfig.type,
                viewMode: chartConfig.viewMode,
                chartName: chartName,
                timestamp: new Date().toISOString(),
                chartId: chartId
            }))

            // 서버 업로드
            const response = await fetch('/api/upload-chart-image', {
                method: 'POST',
                body: formData
            })

            if (response.ok) {
                const result = await response.json()
                console.log('이미지 서버 저장 완료:', result.imagePath)

                // 메타데이터 DB 저장
                const metadataPayload = [{
                    originalFilename: csvData.filename,
                    imagePath: result.imagePath,
                    chartType: chartConfig.type,
                    viewMode: chartConfig.viewMode,
                    chartName: chartName,
                    chartId: chartId,
                    uploadedAt: result.uploadedAt,
                    fileSize: result.size,
                    analysisConfig: {
                        timestampColumn: dataConfig.timestampColumn,
                        visualizationColumns: dataConfig.visualizationColumns,
                        excludeColumns: dataConfig.excludeColumns,
                        timeUnit: chartConfig.timeUnit
                    },
                    statistics: {
                        dataPointsCount: prepareChartData().reduce((total, series) => total + series.x.length, 0),
                        columnCount: dataConfig.visualizationColumns.length,
                        timeRange: dataStats.timeRange
                    },
                    comparisonSegments: comparisonSegments.map(segment => ({
                        id: segment.id,
                        column: segment.column,
                        startTime: segment.startTime.toISOString(),
                        endTime: segment.endTime.toISOString(),
                        dataPointsCount: segment.data.length
                    }))
                }]

                // 메타데이터 저장
                try {
                    const metadataResponse = await fetch('/api/chart-metadata', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(metadataPayload)
                    })

                    if (metadataResponse.ok) {
                        console.log('메타데이터 저장 완료')
                    }
                } catch (error) {
                    console.error('메타데이터 저장 실패:', error)
                }

                // 클라이언트 다운로드
                const link = document.createElement('a')
                link.href = imageData
                link.download = filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                
                return result.imagePath
            } else {
                console.error('서버 업로드 실패:', response.statusText)
                return null
            }

        } catch (error) {
            console.error('차트 캡처 실패:', error)
            return null
        }
    }, [csvData, chartConfig, dataConfig, dataStats, comparisonSegments, prepareChartData])



    return (
        <div className="p-6">
            <div className="w-full">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-foreground mb-4 flex items-center">
                        <TrendingUp className="w-8 h-8 mr-3 text-accent-blue" />
                        {t('iotPrismDemo.title')}
                    </h1>
                    <p className="text-muted-foreground text-lg">
                        {t('iotPrismDemo.subtitle')}
                    </p>
                </div>

                {/* 파일 업로드 및 데이터 현황/설정 */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
                    {/* 왼쪽: 파일 업로드 카드 (2행 스팬) */}
                    <div className="lg:row-span-2 bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                            <Upload className="w-5 h-5 mr-2 text-accent-blue" />
                            {t('iotPrismDemo.upload.title')}
                        </h3>
                        <FileUpload onFileLoad={handleFileLoad} isLoading={isLoading} />

                        {csvData && (
                            <div className="mt-3 p-3 bg-green-400/10 border border-green-400/20 rounded-lg">
                                <p className="text-green-300 text-xs items-center flex">
                                    <CheckCircle className="w-3 h-3 mr-1 flex-shrink-0" />
                                   <span className="overflow-hidden text-ellipsis whitespace-nowrap">{csvData.filename}
                                   </span>
                                </p>
                            </div>
                        )}
                    </div>

                    {/* 오른쪽 상단: 데이터 현황 카드들 */}
                    <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <StatusCard
                            title={t('iotPrismDemo.stats.totalRows')}
                            value={dataStats.totalRows.toLocaleString()}
                            icon={<Database className="w-6 h-6 text-white" />}
                            color="#3b82f6"
                        />
                        <StatusCard
                            title={t('iotPrismDemo.stats.totalColumns')}
                            value={dataStats.totalColumns}
                            icon={<BarChart3 className="w-6 h-6 text-white" />}
                            color="#f97316"
                        />
                        <StatusCard
                            title={t('iotPrismDemo.stats.selectedColumns')}
                            value={dataStats.selectedColumns}
                            icon={<Activity className="w-6 h-6 text-white" />}
                            color="#8b5cf6"
                        />
                    </div>

                    {/* 오른쪽 하단: 데이터 설정 */}
                    {csvData && (
                        <div className="lg:col-span-3 bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                            <h3 className="text-xl font-semibold text-foreground mb-6 flex items-center">
                                <Settings className="w-6 h-6 mr-2 text-accent-blue" />
                                {t('iotPrismDemo.configuration.title')}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <Select
                                    value={dataConfig.timestampColumn}
                                    onChange={(value) => setDataConfig(prev => ({ ...prev, timestampColumn: value }))}
                                    options={getTimestampColumns()}
                                    label={t('iotPrismDemo.configuration.timestampColumn')}
                                    placeholder={t('iotPrismDemo.configuration.timestampColumnPlaceholder')}
                                />

                                <MultiSelect
                                    value={dataConfig.visualizationColumns}
                                    onChange={(value) => setDataConfig(prev => ({ ...prev, visualizationColumns: value }))}
                                    options={getVisualizableColumns()}
                                    label={t('iotPrismDemo.configuration.visualizationColumns')}
                                    placeholder={t('iotPrismDemo.configuration.visualizationColumnsPlaceholder')}
                                />

                                <MultiSelect
                                    value={dataConfig.excludeColumns}
                                    onChange={(value) => setDataConfig(prev => ({ ...prev, excludeColumns: value }))}
                                    options={csvData.columns.filter(col => col !== dataConfig.timestampColumn)}
                                    label={t('iotPrismDemo.configuration.excludeColumns')}
                                    placeholder={t('iotPrismDemo.configuration.excludeColumnsPlaceholder')}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* 차트 설정 */}
                {csvData && dataConfig.timestampColumn && dataConfig.visualizationColumns.length > 0 && (
                    <div className="mb-8">
                        <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                            <h3 className="text-xl font-semibold text-foreground mb-6 flex items-center">
                                <BarChart3 className="w-6 h-6 mr-2 text-accent-blue" />
                                {t('iotPrismDemo.chartSettings.title')}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <Select
                                    value={chartConfig.type}
                                    onChange={(value: string) => setChartConfig(prev => ({ ...prev, type: value as ChartType }))}
                                    options={[
                                        { value: 'line', label: t('iotPrismDemo.chartSettings.lineChart') },
                                        { value: 'box', label: t('iotPrismDemo.chartSettings.boxPlot') },
                                        { value: 'scatter', label: t('iotPrismDemo.chartSettings.scatterPlot') }
                                    ]}
                                    label={t('iotPrismDemo.chartSettings.chartType')}
                                />

                                {chartConfig.type === 'line' && (
                                    <div className="space-y-2">
                                        <label className="block text-sm font-medium text-foreground">
                                            {t('iotPrismDemo.chartSettings.viewMode')}
                                        </label>
                                        <div className="flex space-x-4">
                                            <label className="flex items-center">
                                                <input
                                                    type="radio"
                                                    name="viewMode"
                                                    value="individual"
                                                    checked={chartConfig.viewMode === 'individual'}
                                                    onChange={(e) => setChartConfig(prev => ({ ...prev, viewMode: e.target.value as ViewMode }))}
                                                    className="mr-2"
                                                />
                                                <span className="text-sm text-foreground">{t('iotPrismDemo.chartSettings.individual')}</span>
                                            </label>
                                            <label className="flex items-center">
                                                <input
                                                    type="radio"
                                                    name="viewMode"
                                                    value="overlay"
                                                    checked={chartConfig.viewMode === 'overlay'}
                                                    onChange={(e) => setChartConfig(prev => ({ ...prev, viewMode: e.target.value as ViewMode }))}
                                                    className="mr-2"
                                                />
                                                <span className="text-sm text-foreground">{t('iotPrismDemo.chartSettings.overlay')}</span>
                                            </label>
                                        </div>
                                    </div>
                                )}

                                {chartConfig.type === 'box' && (
                                    <Select
                                        value={chartConfig.timeUnit}
                                        onChange={(value: string) => setChartConfig(prev => ({ ...prev, timeUnit: value as TimeUnit }))}
                                        options={[
                                            { value: 'hour', label: t('iotPrismDemo.chartSettings.hourly') },
                                            { value: 'day', label: t('iotPrismDemo.chartSettings.daily') },
                                            { value: 'week', label: t('iotPrismDemo.chartSettings.weekly') },
                                            { value: 'month', label: t('iotPrismDemo.chartSettings.monthly') }
                                        ]}
                                        label={t('iotPrismDemo.chartSettings.timeUnit')}
                                    />
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* 시각화 영역 */}
                <div className="mb-8">
                    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-semibold text-foreground flex items-center">
                                <TrendingUp className="w-6 h-6 mr-2 text-accent-blue" />
                                {t('iotPrismDemo.visualization.title')}
                            </h3>
                        </div>

                        {!csvData ? (
                            <div className="text-center py-12">
                                <Database className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                                <p className="text-muted-foreground">{t('iotPrismDemo.visualization.noData')}</p>
                            </div>
                        ) : !dataConfig.timestampColumn || dataConfig.visualizationColumns.length === 0 ? (
                            <div className="text-center py-12">
                                <Settings className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                                <p className="text-muted-foreground">
                                    {!dataConfig.timestampColumn
                                        ? t('iotPrismDemo.errors.noTimestampColumn')
                                        : t('iotPrismDemo.errors.noVisualizationColumns')
                                    }
                                </p>
                            </div>
                        ) : (
                            <TimeSeriesVisualization
                                data={prepareChartData()}
                                config={chartConfig}
                                onSelectionMade={comparisonEnabled ? addComparisonSegment : undefined}
                                selectedColumn={selectedColumn}
                                onImageCapture={captureAndSaveChart}
                                onAIAnalysis={analyzeChartWithAI}
                                aiAnalysisState={aiAnalysisState}
                            />
                        )}
                    </div>

                </div>

                {/* 형태 비교 설정 */}
                {csvData && dataConfig.timestampColumn && dataConfig.visualizationColumns.length > 0 && chartConfig.type === 'line' && chartConfig.viewMode === 'individual' && (
                    <div className="mb-8">
                        <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                            <h3 className="text-xl font-semibold text-foreground mb-6 flex items-center">
                                <Box className="w-6 h-6 mr-2 text-accent-blue" />
                                {t('iotPrismDemo.shapeComparison.title')}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <div className="space-y-4">
                                    <Checkbox
                                        checked={comparisonEnabled}
                                        onChange={(enabled) => {
                                            setComparisonEnabled(enabled)
                                            if (!enabled) {
                                                setSelectedColumn('')
                                                setComparisonSegments([])
                                            }
                                        }}
                                        label={t('iotPrismDemo.shapeComparison.enable')}
                                    />

                                    {comparisonEnabled && (
                                        <>
                                            {selectedColumn ? (
                                                <div className="bg-accent-blue/5 border border-accent-blue/20 rounded-lg p-3">
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                                                                        <p className="text-sm font-medium text-accent-blue">
                                                {t('iotPrismDemo.shapeComparison.targetColumn')}: {selectedColumn}
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {t('iotPrismDemo.shapeComparison.dragInstruction')}
                                            </p>
                                                        </div>
                                                        <button
                                                            onClick={() => {
                                                                setSelectedColumn('')
                                                                setComparisonSegments([])
                                                            }}
                                                                                                        className="text-accent-blue hover:text-accent-blue/80 p-1"
                                            title={t('iotPrismDemo.shapeComparison.resetTarget')}
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <p className="text-muted-foreground text-sm">
                                                    {t('iotPrismDemo.shapeComparison.description')}
                                                </p>
                                            )}
                                        </>
                                    )}
                                </div>

                                {comparisonEnabled && comparisonSegments.length > 0 && (
                                    <div className="col-span-1 md:col-span-2 space-y-2">
                                        <h4 className="text-sm font-medium text-foreground mb-3">{t('iotPrismDemo.shapeComparison.selectedTimeRanges')}</h4>
                                        {comparisonSegments.map((segment) => (
                                            <div key={segment.id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                                                <div className="flex items-center space-x-3">
                                                    <div
                                                        className="w-4 h-4 rounded"
                                                        style={{ backgroundColor: segment.color }}
                                                    />
                                                    <div>
                                                        <span className="text-sm font-medium text-foreground">{segment.column}</span>
                                                        <p className="text-xs text-muted-foreground">
                                                            {segment.startTime.toLocaleString()} ~ {segment.endTime.toLocaleString()}
                                                        </p>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => setComparisonSegments(prev => prev.filter(s => s.id !== segment.id))}
                                                    className="text-destructive hover:text-destructive/80 p-1"
                                                    title={t('iotPrismDemo.shapeComparison.removeTimeRange')}
                                                >
                                                    <X className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                        <button
                                            onClick={() => setComparisonSegments([])}
                                            className="w-full text-sm text-muted-foreground hover:text-foreground p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                                        >
                                            {t('iotPrismDemo.shapeComparison.clear')}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* 형태 비교 시각화 */}
                {comparisonEnabled && comparisonSegments.length > 0 && (
                    <div className="mb-8">
                        <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center">
                                <TrendingUp className="w-6 h-6 mr-2 text-accent-blue" />
                                {t('iotPrismDemo.shapeComparison.comparisonVisualization')}
                            </h3>
                            <ComparisonVisualization
                                segments={comparisonSegments}
                                onSegmentUpdate={setComparisonSegments}
                                onImageCapture={captureAndSaveChart}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}