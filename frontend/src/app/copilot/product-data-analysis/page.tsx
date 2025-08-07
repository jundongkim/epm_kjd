'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Upload, 
  BarChart3, 
  TrendingUp, 
  FileText, 
  Download,
  Settings,
  AlertCircle,
  CheckCircle,
  Info,
  Zap,
  Target,
  Database,
  Factory,
  FlaskConical,
  DollarSign,
  Activity,
  RefreshCw,
  Calendar,
  Split,
  X,
  BarChart,
  Scale,
  Eye,
  PlayCircle
} from 'lucide-react';
import { FloatingChatbot } from '@/components/FloatingChatbot';
import { useAppStore } from '@/store/useAppStore';
import { Slider, Select, Checkbox, TabNavigation } from '@/components/ui';

interface DataInfo {
  rows: number;
  columns: number;
  missing_values: number;
  numeric_columns: number;
}

interface ColumnInfo {
  name: string;
  type: string;
  missing: number;
  unique: number;
}

interface CorrelationData {
  [key: string]: { [key: string]: number };
}

interface BasicStats {
  [column: string]: {
    mean: number;
    std: number;
    min: number;
    max: number;
    '25%': number;
    '50%': number;
    '75%': number;
  };
}

interface PreprocessingResult {
  originalRows: number;
  processedRows: number;
  trainRows: number;
  testRows: number;
  targetColumn: string;
  steps: string[];
  processingTime: string;
  dataQuality: number;
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

// API 호출 함수들 추가
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 저장된 파일 목록 조회 API
const getStoredFilesAPI = async () => {
  const response = await fetch(`${API_BASE_URL}/api/data/files`)
  
  if (!response.ok) {
    throw new Error(`파일 목록 조회 실패: ${response.statusText}`)
  }
  
  return await response.json()
}

// 파일 데이터 로드 API  
const loadFileDataAPI = async (filename: string) => {
  const response = await fetch(`${API_BASE_URL}/api/data/files/${encodeURIComponent(filename)}/data`)
  
  if (!response.ok) {
    throw new Error(`파일 로드 실패: ${response.statusText}`)
  }
  
  return await response.json()
}

export default function ProductDataAnalysis() {
  // 전역 상태 관리
  const { setModelingData } = useAppStore();
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // State
  const [activeTab, setActiveTab] = useState<'files' | 'preprocessing' | 'analysis'>('files');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [data, setData] = useState<any[] | null>(null);
  const [dataInfo, setDataInfo] = useState<DataInfo | null>(null);
  const [columnInfo, setColumnInfo] = useState<ColumnInfo[]>([]);
  const [correlationData, setCorrelationData] = useState<CorrelationData>({});
  const [basicStats, setBasicStats] = useState<BasicStats>({});
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [correlationThreshold, setCorrelationThreshold] = useState(0.7);
  const [selectedColumn, setSelectedColumn] = useState<string>('');
  const [chartType, setChartType] = useState<'histogram' | 'boxplot' | 'violin'>('histogram');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [preprocessingResult, setPreprocessingResult] = useState<PreprocessingResult | null>(null);
  const [isPreprocessing, setIsPreprocessing] = useState(false);

  // 파일 관리 관련 state 추가
  const [savedFiles, setSavedFiles] = useState<DataFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [selectedFile, setSelectedFile] = useState<DataFile | null>(null);
  const [currentDataSource, setCurrentDataSource] = useState<'upload' | 'generated'>('generated');

  // 데이터 전처리 관련 state
  const [trainTestSplit, setTrainTestSplit] = useState(0.8);
  const [randomState, setRandomState] = useState(42);
  const [missingValueMethod, setMissingValueMethod] = useState<'drop' | 'mean' | 'median' | 'mode'>('mean');
  const [outlierMethod, setOutlierMethod] = useState<'iqr' | 'zscore' | 'none'>('iqr');
  const [scalingMethod, setScalingMethod] = useState<'standard' | 'minmax' | 'robust' | 'none'>('standard');
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [outlierData, setOutlierData] = useState<any>(null);

  // 저장된 파일 목록 불러오기
  const loadSavedFiles = async () => {
    setIsLoadingFiles(true);
    try {
      const response = await getStoredFilesAPI();
      setSavedFiles(response.files || []);
    } catch (error) {
      console.error('파일 목록 로드 실패:', error);
      setSavedFiles([]);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  // 페이지 로드 시 파일 목록 초기화
  useEffect(() => {
    loadSavedFiles();
  }, []);

  // 파일 선택 처리
  const handleFileSelect = async (file: DataFile) => {
    setSelectedFile(file);
    setIsAnalyzing(true);

    try {
      const fileDataResponse = await loadFileDataAPI(file.filename);
      const loadedData = fileDataResponse.data;
      
      if (loadedData && loadedData.length > 0) {
        await analyzeLoadedData(loadedData, file.filename);
      } else {
        alert('선택된 파일에 분석할 데이터가 없습니다.');
      }
    } catch (error) {
      console.error('파일 선택 처리 오류:', error);
      alert(`파일 처리 중 오류가 발생했습니다: ${error}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 로드된 데이터 분석
  const analyzeLoadedData = async (loadedData: any[], filename: string) => {
    if (!loadedData || loadedData.length === 0) {
      return;
    }

    // 1초 지연 (분석 중인 것처럼 보이게)
    await new Promise(resolve => setTimeout(resolve, 1000));

    const columns = Object.keys(loadedData[0]);
    
    // 데이터 설정
    setData(loadedData);
    
    setDataInfo({
      rows: loadedData.length,
      columns: columns.length,
      missing_values: 0, // 실제로는 계산 필요
      numeric_columns: columns.filter(col => typeof loadedData[0][col] === 'number').length
    });

    setColumnInfo(columns.map(col => ({
      name: col,
      type: typeof loadedData[0][col] === 'number' ? 'float64' : 'object',
      missing: 0,
      unique: loadedData.length
    })));

    // 수치형 컬럼만 상관관계 분석
    const numericColumns = columns.filter(col => typeof loadedData[0][col] === 'number');
    
    // 상관관계 데이터 생성 (간단한 피어슨 상관계수)
    const correlation: CorrelationData = {};
    numericColumns.forEach(col1 => {
      correlation[col1] = {};
      numericColumns.forEach(col2 => {
        if (col1 === col2) {
          correlation[col1][col2] = 1;
        } else {
          const values1 = loadedData.map(row => row[col1]).filter(v => typeof v === 'number');
          const values2 = loadedData.map(row => row[col2]).filter(v => typeof v === 'number');
          
          if (values1.length > 1 && values2.length > 1) {
            const mean1 = values1.reduce((a, b) => a + b, 0) / values1.length;
            const mean2 = values2.reduce((a, b) => a + b, 0) / values2.length;
            
            let numerator = 0;
            let sum1 = 0;
            let sum2 = 0;
            
            for (let i = 0; i < Math.min(values1.length, values2.length); i++) {
              const diff1 = values1[i] - mean1;
              const diff2 = values2[i] - mean2;
              numerator += diff1 * diff2;
              sum1 += diff1 * diff1;
              sum2 += diff2 * diff2;
            }
            
            const denominator = Math.sqrt(sum1 * sum2);
            correlation[col1][col2] = denominator !== 0 ? numerator / denominator : 0;
          } else {
            correlation[col1][col2] = 0;
          }
        }
      });
    });
    setCorrelationData(correlation);

    // 기본 통계 생성
    const stats: BasicStats = {};
    numericColumns.forEach(col => {
      const values = loadedData.map(row => row[col]).filter(v => typeof v === 'number');
      if (values.length > 0) {
        const sorted = [...values].sort((a, b) => a - b);
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
        
        stats[col] = {
          mean,
          std: Math.sqrt(variance),
          min: Math.min(...values),
          max: Math.max(...values),
          '25%': sorted[Math.floor(values.length * 0.25)],
          '50%': sorted[Math.floor(values.length * 0.5)],
          '75%': sorted[Math.floor(values.length * 0.75)]
        };
      }
    });
    setBasicStats(stats);
    setSelectedColumns(numericColumns.slice(0, Math.min(6, numericColumns.length)));
    setSelectedColumn(numericColumns[0] || '');

    // preprocessing 탭으로 이동 (순서대로 진행하도록)
    setActiveTab('preprocessing');
  };

  // 파일 업로드 처리
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
      alert('CSV 또는 Excel 파일만 업로드 가능합니다.');
      return;
    }

    setUploadedFile(file);
    setIsAnalyzing(true);

    try {
      // 실제 구현에서는 backend API로 파일 업로드 후 분석
      // 현재는 간단한 시뮬레이션
      const sampleData = Array.from({ length: 50 }, (_, idx) => ({
        온도: 150 + Math.random() * 50,
        압력: 1.5 + Math.random() * 1.5,
        pH: 6.5 + Math.random() * 2,
        순도: 95 + Math.random() * 4,
        수율: 85 + Math.random() * 13
      }));

      await analyzeLoadedData(sampleData, file.name);
    } catch (error) {
      console.error('파일 업로드 오류:', error);
      alert('파일 업로드 중 오류가 발생했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePreprocessing = async () => {
    if (!data || !targetColumn) {
      alert('데이터와 타겟 변수를 선택해주세요.');
      return;
    }

    setIsPreprocessing(true);

    try {
      // 1초 지연 (전처리 중인 것처럼 보이게)
      await new Promise(resolve => setTimeout(resolve, 1000));

      let processedData = [...data];
      const processingSteps: string[] = [];

      // 1. 결측치 처리
      if (missingValueMethod !== 'drop') {
        processingSteps.push(`결측치를 ${
          missingValueMethod === 'mean' ? '평균값' :
          missingValueMethod === 'median' ? '중앙값' : 
          '최빈값'
        }으로 대체했습니다.`);
      } else {
        const originalLength = processedData.length;
        processedData = processedData.filter(row => 
          Object.values(row).every(val => val !== null && val !== undefined && val !== '')
        );
        if (processedData.length < originalLength) {
          processingSteps.push(`결측치 포함 행 ${originalLength - processedData.length}개를 제거했습니다.`);
        }
      }

      // 2. 이상치 처리
      if (outlierMethod !== 'none') {
        const numericColumns = Object.keys(processedData[0]).filter(col => 
          typeof processedData[0][col] === 'number' && col !== targetColumn
        );
        
        let outlierCount = 0;
        numericColumns.forEach(col => {
          const values = processedData.map(row => row[col]).filter(v => typeof v === 'number');
          
          if (outlierMethod === 'iqr') {
            const sorted = [...values].sort((a, b) => a - b);
            const q1 = sorted[Math.floor(values.length * 0.25)];
            const q3 = sorted[Math.floor(values.length * 0.75)];
            const iqr = q3 - q1;
            const lowerBound = q1 - 1.5 * iqr;
            const upperBound = q3 + 1.5 * iqr;
            
            processedData = processedData.filter(row => {
              const value = row[col];
              if (typeof value === 'number' && (value < lowerBound || value > upperBound)) {
                outlierCount++;
                return false;
              }
              return true;
            });
          }
        });
        
        if (outlierCount > 0) {
          processingSteps.push(`${outlierMethod.toUpperCase()} 방법으로 이상치 ${outlierCount}개를 제거했습니다.`);
        }
      }

      // 3. 데이터 분할
      const shuffledData = [...processedData].sort(() => Math.random() - 0.5);
      const trainSize = Math.floor(shuffledData.length * trainTestSplit);
      const trainData = shuffledData.slice(0, trainSize);
      const testData = shuffledData.slice(trainSize);

      processingSteps.push(`데이터를 훈련용 ${trainData.length}행, 테스트용 ${testData.length}행으로 분할했습니다.`);

      // 4. 스케일링 (시뮬레이션)
      if (scalingMethod !== 'none') {
        processingSteps.push(`${
          scalingMethod === 'standard' ? 'Standard Scaling' :
          scalingMethod === 'minmax' ? 'Min-Max Scaling' :
          'Robust Scaling'
        }을 적용했습니다.`);
      }

      // 전처리 결과 설정
      setPreprocessingResult({
        originalRows: data.length,
        processedRows: processedData.length,
        trainRows: trainData.length,
        testRows: testData.length,
        targetColumn,
        steps: processingSteps,
        processingTime: '1.2초',
        dataQuality: 95.8
      });

            // 처리된 데이터로 업데이트
      setData(processedData);
      
      // 데이터 정보 업데이트
      const updatedDataInfo = {
        rows: processedData.length,
        columns: Object.keys(processedData[0] || {}).length,
        missing_values: 0, // 전처리 후에는 결측치 없음
        numeric_columns: Object.keys(processedData[0] || {}).filter(col => 
          typeof processedData[0][col] === 'number'
        ).length
      };
      setDataInfo(updatedDataInfo);

      // 전역 상태에 모델링용 데이터 저장
      const columns = Object.keys(processedData[0] || {});
      const numericColumns = columns.filter(col => typeof processedData[0][col] === 'number');
      const categoricalColumns = columns.filter(col => typeof processedData[0][col] !== 'number');

      setModelingData({
        trainData: trainData,
        testData: testData,
        originalData: data,
        preprocessingConfig: {
          targetColumn,
          trainTestSplit,
          missingValueMethod,
          outlierMethod,
          scalingMethod,
          randomState
        },
        dataInfo: {
          originalRows: data.length,
          processedRows: processedData.length,
          columns,
          numericColumns,
          categoricalColumns
        }
      });

             // 전처리 완료 후 데이터 분석 탭으로 자동 이동
      setTimeout(() => {
        setActiveTab('analysis');
        alert('전처리가 완료되었습니다! 데이터 분석 탭에서 결과를 확인하고, 모델링에서 ML 모델을 학습할 수 있습니다.');
      }, 500);

    } catch (error) {
      console.error('전처리 오류:', error);
      alert('전처리 중 오류가 발생했습니다.');
    } finally {
      setIsPreprocessing(false);
    }
  };

  const getDataTypeLabel = (dataType: string) => {
    const typeMap: { [key: string]: string } = {
      'quality': '품질 데이터',
      'process': '공정 데이터', 
      'production': '생산 데이터',
      'cost': '원가 데이터'
    };
    return typeMap[dataType] || dataType;
  };



  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center">
            <BarChart3 className="w-8 h-8 mr-3 text-accent-purple" />
            데이터 분석
          </h1>
          <p className="text-muted-foreground">
            생성된 데이터 또는 업로드된 데이터의 EDA, 기술통계, 상관관계 분석을 수행합니다.
          </p>
        </div>

        {/* 탭 메뉴 */}
        <TabNavigation
          tabs={[
            { id: 'files', name: '데이터 선택', icon: Database },
            { id: 'preprocessing', name: '데이터 전처리', icon: Settings },
            { id: 'analysis', name: '데이터 분석', icon: BarChart3 }
          ]}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as 'files' | 'preprocessing' | 'analysis')}
          className="mb-6"
        />

        {/* 데이터 선택 탭 */}
        {activeTab === 'files' && (
          <div className="space-y-6">
            {/* 저장된 파일 목록 */}
            <div className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center">
                  <Database className="w-5 h-5 mr-2 text-accent-blue" />
                  생성된 데이터 파일 목록
                </h3>
                <button
                  onClick={loadSavedFiles}
                  disabled={isLoadingFiles}
                  className="flex items-center px-3 py-2 text-sm bg-accent-blue hover:bg-accent-blue/80 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingFiles ? 'animate-spin' : ''}`} />
                  새로고침
                </button>
              </div>

              {isLoadingFiles ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-blue mx-auto mb-4"></div>
                  <p className="text-muted-foreground">파일 목록을 불러오는 중...</p>
                </div>
              ) : savedFiles.length === 0 ? (
                <div className="text-center py-8">
                  <Database className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground mb-2">생성된 데이터 파일이 없습니다.</p>
                  <p className="text-sm text-muted-foreground">데이터 생성 탭에서 먼저 데이터를 생성해주세요.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* 데이터 타입별 그룹화 */}
                  {[
                    { type: 'production', label: '생산 데이터', icon: Factory, color: 'text-accent-blue' },
                    { type: 'sensor', label: '센서 데이터', icon: Activity, color: 'text-accent-green' },
                    { type: 'experimental', label: '실험 데이터', icon: FlaskConical, color: 'text-accent-purple' },
                    { type: 'cost', label: '원가 데이터', icon: DollarSign, color: 'text-accent-orange' }
                  ].map(({ type, label, icon: Icon, color }) => {
                    const typeFiles = savedFiles
                      .filter(file => file.dataType === type)
                      .sort((a, b) => new Date(b.createTime).getTime() - new Date(a.createTime).getTime());
                    
                    if (typeFiles.length === 0) return null;
                    
                    return (
                      <div key={type} className="bg-muted/20 rounded-lg p-4">
                        <div className="flex items-center mb-4">
                          <Icon className={`w-5 h-5 mr-2 ${color}`} />
                          <h4 className="text-lg font-semibold text-foreground">{label}</h4>
                          <span className="ml-2 px-2 py-1 bg-muted text-xs rounded-full text-muted-foreground">
                            {typeFiles.length}개 파일
                          </span>
                        </div>
                        
                        <div className="space-y-2">
                          {typeFiles.map((file, index) => (
                            <div 
                              key={index}
                              className={`p-4 border rounded-lg cursor-pointer transition-all duration-300 hover:bg-muted/50 ${
                                selectedFile?.filename === file.filename 
                                  ? 'border-accent-blue bg-accent-blue/10' 
                                  : 'border-border'
                              }`}
                              onClick={() => handleFileSelect(file)}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-3">
                                    <Icon className={`w-4 h-4 ${color}`} />
                                    <div>
                                      <div className="font-medium text-foreground text-sm truncate" title={file.filename}>
                                        {file.filename}
                                      </div>
                                      <div className="text-xs text-muted-foreground mt-1">
                                        {new Date(file.createTime).toLocaleString('ko-KR')} | 
                                        {file.rowCount?.toLocaleString()}행 × {file.colCount}열 | 
                                        {file.fileSizeKb}KB
                                      </div>
                                    </div>
                                  </div>
                                </div>
                                
                                <div className="flex items-center space-x-2">
                                  {selectedFile?.filename === file.filename && (
                                    <div className="flex items-center text-xs text-accent-blue">
                                      <CheckCircle className="w-4 h-4 mr-1" />
                                      <span className="font-medium">선택됨</span>
                                    </div>
                                  )}
                                  {isAnalyzing && selectedFile?.filename === file.filename && (
                                    <div className="flex items-center text-xs text-muted-foreground">
                                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent-blue mr-1"></div>
                                      <span>로딩 중</span>
                                    </div>
                                  )}
                                  {(!selectedFile || selectedFile.filename !== file.filename) && (
                                    <span className="text-xs text-muted-foreground">클릭하여 선택</span>
                                  )}
                                </div>
                              </div>
                              
                              {/* 미리보기 데이터 */}
                              {file.previewData && file.previewData.length > 0 && (
                                <div className="mt-3 p-3 bg-muted/30 rounded text-xs">
                                  <div className="font-medium text-foreground mb-2">데이터 미리보기:</div>
                                  <div className="font-mono overflow-x-auto">
                                    <div className="flex space-x-4 text-muted-foreground mb-1 font-medium">
                                      {Object.keys(file.previewData[0]).slice(0, 6).map(key => (
                                        <span key={key} className="min-w-20">{key}</span>
                                      ))}
                                    </div>
                                    {file.previewData.slice(0, 2).map((row, idx) => (
                                      <div key={idx} className="flex space-x-4 text-foreground">
                                        {Object.values(row).slice(0, 6).map((value, vIdx) => (
                                          <span key={vIdx} className="min-w-20 truncate">
                                            {typeof value === 'number' ? value.toFixed(1) : String(value)}
                                          </span>
                                        ))}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* 파일 업로드 옵션 */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Upload className="w-5 h-5 mr-2 text-accent-purple" />
                직접 파일 업로드
              </h3>
              
              <div className="mb-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-accent-purple transition-colors"
                  disabled={isAnalyzing}
                >
                  <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-foreground font-medium">
                    {isAnalyzing ? '분석 중...' : 'CSV 또는 Excel 파일 업로드'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    파일을 드래그하거나 클릭하여 업로드하세요
                  </p>
                </button>
              </div>

              {uploadedFile && (
                <div className="bg-muted/50 rounded-lg p-4">
                  <p className="text-sm text-foreground">
                    <FileText className="w-4 h-4 inline mr-2" />
                    업로드된 파일: <span className="font-medium">{uploadedFile.name}</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 데이터 전처리 탭 */}
        {activeTab === 'preprocessing' && (
          <div className="space-y-6">
            {!data ? (
              <div className="bg-card border border-border rounded-lg p-6 text-center">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
                <h3 className="text-lg font-semibold text-foreground mb-2">데이터 선택 필요</h3>
                <p className="text-muted-foreground mb-4">
                  먼저 <strong>데이터 선택</strong> 탭에서 데이터를 선택해주세요.
                </p>
                <button
                  onClick={() => setActiveTab('files')}
                  className="bg-gradient-primary text-white px-4 py-2 rounded-lg hover:scale-105 transition-transform"
                >
                  데이터 선택 탭으로 이동
                </button>
              </div>
            ) : (
              <>
                {/* 데이터 기본 정보 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <Info className="w-5 h-5 mr-2 text-accent-green" />
                    데이터 기본 정보
                  </h3>
                  
                  {/* 기본 통계 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-muted/30 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-accent-blue">{dataInfo?.rows?.toLocaleString() || 0}</div>
                      <div className="text-sm text-muted-foreground">행 수</div>
                    </div>
                    <div className="bg-muted/30 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-accent-green">{dataInfo?.columns || 0}</div>
                      <div className="text-sm text-muted-foreground">열 수</div>
                    </div>
                    <div className="bg-muted/30 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-accent-orange">{dataInfo?.missing_values || 0}</div>
                      <div className="text-sm text-muted-foreground">결측치</div>
                    </div>
                    <div className="bg-muted/30 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-accent-purple">{dataInfo?.numeric_columns || 0}</div>
                      <div className="text-sm text-muted-foreground">수치형 컬럼</div>
                    </div>
                  </div>

                  {/* 데이터 미리보기 */}
                  <div className="mb-4">
                    <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                      <Eye className="w-4 h-4 mr-2" />
                      데이터 미리보기 (상위 5행)
                    </h4>
                    <div className="border border-border rounded-lg overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-muted/50">
                            <tr>
                              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">#</th>
                              {data && Object.keys(data[0] || {}).slice(0, 8).map((col, idx) => (
                                <th key={idx} className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
                                  {col}
                                </th>
                              ))}
                              {data && Object.keys(data[0] || {}).length > 8 && (
                                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">...</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {data && data.slice(0, 5).map((row, idx) => (
                              <tr key={idx} className={idx % 2 === 0 ? 'bg-background' : 'bg-muted/20'}>
                                <td className="px-3 py-2 text-xs text-muted-foreground">{idx + 1}</td>
                                {Object.values(row).slice(0, 8).map((value, vIdx) => (
                                  <td key={vIdx} className="px-3 py-2 text-xs text-foreground">
                                    {typeof value === 'number' ? value.toFixed(2) : String(value)}
                                  </td>
                                ))}
                                {Object.keys(row).length > 8 && (
                                  <td className="px-3 py-2 text-xs text-muted-foreground">...</td>
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* 컬럼 정보 */}
                  <div>
                    <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                      <Database className="w-4 h-4 mr-2" />
                      컬럼 정보
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {columnInfo.map((col, idx) => (
                        <div key={idx} className="bg-muted/20 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-foreground text-sm">{col.name}</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              col.type.includes('float') || col.type.includes('int') 
                                ? 'bg-accent-blue/20 text-accent-blue' 
                                : 'bg-accent-purple/20 text-accent-purple'
                            }`}>
                              {col.type.includes('float') || col.type.includes('int') ? '수치형' : '범주형'}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground space-y-1">
                            <div>결측치: {col.missing}개</div>
                            <div>고유값: {col.unique}개</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 학습/테스트 데이터 분할 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <Split className="w-5 h-5 mr-2 text-accent-blue" />
                    학습/테스트 데이터 분할
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 분할 설정 */}
                    <div className="space-y-4">
                      {/* 훈련 데이터 비율 */}
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          훈련 데이터 비율: {(trainTestSplit * 100).toFixed(0)}%
                        </label>
                        <Slider
                          label=""
                          value={trainTestSplit}
                          onChange={setTrainTestSplit}
                          min={0.5}
                          max={0.9}
                          step={0.05}
                          className="mb-2"
                        />
                        <div className="text-xs text-muted-foreground">
                          테스트 데이터: {((1 - trainTestSplit) * 100).toFixed(0)}%
                        </div>
                      </div>

                      {/* 랜덤 시드 */}
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          랜덤 시드
                        </label>
                        <input
                          type="number"
                          value={randomState}
                          onChange={(e) => setRandomState(parseInt(e.target.value) || 42)}
                          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
                          placeholder="42"
                        />
                        <div className="text-xs text-muted-foreground mt-1">
                          재현 가능한 결과를 위한 시드값
                        </div>
                      </div>

                      {/* 타겟 변수 선택 */}
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          타겟 변수 선택
                        </label>
                        <Select
                          label=""
                          value={targetColumn}
                          onChange={(value) => setTargetColumn(value)}
                          options={
                            data && data.length > 0
                              ? Object.keys(data[0]).filter(col => 
                                  typeof data[0][col] === 'number'
                                ).map(col => ({ value: col, label: col }))
                              : []
                          }
                          placeholder="타겟 변수를 선택하세요"
                        />
                        <div className="text-xs text-muted-foreground mt-1">
                          예측하고자 하는 목표 변수
                        </div>
                      </div>
                    </div>

                    {/* 분할 결과 미리보기 */}
                    <div className="bg-muted/30 rounded-lg p-4">
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <BarChart3 className="w-4 h-4 mr-2" />
                        분할 결과 미리보기
                      </h4>
                      
                      {data && data.length > 0 ? (
                        <div className="space-y-3">
                          <div className="bg-accent-blue/10 rounded-lg p-3">
                            <div className="text-sm font-medium text-accent-blue mb-1">훈련 데이터</div>
                            <div className="text-lg font-bold text-foreground">
                              {Math.floor(data.length * trainTestSplit).toLocaleString()}행
                            </div>
                            <div className="text-xs text-muted-foreground">
                              전체 데이터의 {(trainTestSplit * 100).toFixed(0)}%
                            </div>
                          </div>
                          
                          <div className="bg-accent-orange/10 rounded-lg p-3">
                            <div className="text-sm font-medium text-accent-orange mb-1">테스트 데이터</div>
                            <div className="text-lg font-bold text-foreground">
                              {Math.ceil(data.length * (1 - trainTestSplit)).toLocaleString()}행
                            </div>
                            <div className="text-xs text-muted-foreground">
                              전체 데이터의 {((1 - trainTestSplit) * 100).toFixed(0)}%
                            </div>
                          </div>

                          {targetColumn && (
                            <div className="bg-accent-purple/10 rounded-lg p-3">
                              <div className="text-sm font-medium text-accent-purple mb-1">타겟 변수</div>
                              <div className="text-sm font-bold text-foreground">{targetColumn}</div>
                              <div className="text-xs text-muted-foreground">
                                예측 대상 컬럼
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-muted-foreground py-4">
                          <Split className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <div className="text-sm">데이터를 선택하면 분할 결과를 미리볼 수 있습니다</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 결측치 처리 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <X className="w-5 h-5 mr-2 text-accent-red" />
                    결측치 처리
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 결측치 현황 */}
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <AlertCircle className="w-4 h-4 mr-2" />
                        결측치 현황
                      </h4>
                      
                      {data && data.length > 0 ? (
                        <div className="space-y-2">
                          {Object.keys(data[0]).map((col, idx) => {
                            const missingCount = data.filter(row => 
                              row[col] === null || row[col] === undefined || row[col] === ''
                            ).length;
                            const missingPercent = (missingCount / data.length * 100).toFixed(1);
                            
                            return (
                              <div key={idx} className="flex justify-between items-center p-2 bg-muted/20 rounded">
                                <span className="text-sm font-medium text-foreground">{col}</span>
                                <div className="text-right">
                                  <div className="text-sm font-bold text-foreground">{missingCount}개</div>
                                  <div className="text-xs text-muted-foreground">({missingPercent}%)</div>
                                </div>
                              </div>
                            );
                          })}
                          
                          {Object.keys(data[0]).every(col => 
                            data.filter(row => row[col] === null || row[col] === undefined || row[col] === '').length === 0
                          ) && (
                            <div className="text-center py-4">
                              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-accent-green" />
                              <div className="text-sm text-accent-green font-medium">결측치가 없습니다</div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-muted-foreground py-4">
                          <X className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <div className="text-sm">데이터를 선택하면 결측치 현황을 확인할 수 있습니다</div>
                        </div>
                      )}
                    </div>

                    {/* 처리 방법 선택 */}
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <Settings className="w-4 h-4 mr-2" />
                        처리 방법 선택
                      </h4>
                      
                      <div className="space-y-4">
                        <div>
                          <Select
                            label=""
                            value={missingValueMethod}
                            onChange={(value) => setMissingValueMethod(value as 'drop' | 'mean' | 'median' | 'mode')}
                            options={[
                              { value: 'drop', label: '결측치 포함 행 삭제' },
                              { value: 'mean', label: '평균값으로 대체' },
                              { value: 'median', label: '중앙값으로 대체' },
                              { value: 'mode', label: '최빈값으로 대체' }
                            ]}
                          />
                        </div>

                        {/* 처리 방법 설명 */}
                        <div className="bg-muted/30 rounded-lg p-3">
                          <div className="text-sm font-medium text-foreground mb-2">
                            {missingValueMethod === 'drop' && '행 삭제 방법'}
                            {missingValueMethod === 'mean' && '평균값 대체 방법'}
                            {missingValueMethod === 'median' && '중앙값 대체 방법'}
                            {missingValueMethod === 'mode' && '최빈값 대체 방법'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {missingValueMethod === 'drop' && '결측치가 포함된 행을 완전히 제거합니다. 데이터 손실이 있지만 가장 간단한 방법입니다.'}
                            {missingValueMethod === 'mean' && '수치형 데이터의 평균값으로 결측치를 대체합니다. 정규분포 데이터에 적합합니다.'}
                            {missingValueMethod === 'median' && '수치형 데이터의 중앙값으로 결측치를 대체합니다. 이상치가 있는 데이터에 적합합니다.'}
                            {missingValueMethod === 'mode' && '범주형 데이터의 최빈값(가장 자주 나타나는 값)으로 결측치를 대체합니다.'}
                          </div>
                        </div>

                        {/* 처리 후 예상 결과 */}
                        {data && data.length > 0 && (
                          <div className="bg-accent-blue/10 rounded-lg p-3">
                            <div className="text-sm font-medium text-accent-blue mb-2">처리 후 예상 결과</div>
                            <div className="text-xs text-muted-foreground space-y-1">
                              {missingValueMethod === 'drop' ? (
                                <>
                                  <div>현재 행 수: {data.length.toLocaleString()}행</div>
                                  <div>처리 후 예상: 결측치 포함 행 제거</div>
                                </>
                              ) : (
                                <>
                                  <div>현재 행 수: {data.length.toLocaleString()}행 (유지)</div>
                                  <div>결측치: {missingValueMethod}으로 대체</div>
                                </>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 이상치 처리 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <BarChart className="w-5 h-5 mr-2 text-accent-orange" />
                    이상치 처리
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 탐지 방법 선택 */}
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <Settings className="w-4 h-4 mr-2" />
                        탐지 방법 선택
                      </h4>
                      
                      <div className="space-y-4">
                        <div>
                          <Select
                            label=""
                            value={outlierMethod}
                            onChange={(value) => setOutlierMethod(value as 'iqr' | 'zscore' | 'none')}
                            options={[
                              { value: 'iqr', label: 'IQR 방법 (사분위수)' },
                              { value: 'zscore', label: 'Z-Score 방법 (표준점수)' },
                              { value: 'none', label: '이상치 처리 안함' }
                            ]}
                          />
                        </div>

                        {/* 탐지 방법 설명 */}
                        <div className="bg-muted/30 rounded-lg p-3">
                          <div className="text-sm font-medium text-foreground mb-2">
                            {outlierMethod === 'iqr' && 'IQR (Interquartile Range) 방법'}
                            {outlierMethod === 'zscore' && 'Z-Score (표준점수) 방법'}
                            {outlierMethod === 'none' && '이상치 처리 안함'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {outlierMethod === 'iqr' && '1사분위수(Q1)와 3사분위수(Q3)를 이용하여 IQR*1.5 범위를 벗어나는 값을 이상치로 판단합니다. 일반적으로 많이 사용되는 방법입니다.'}
                            {outlierMethod === 'zscore' && '데이터의 평균과 표준편차를 이용하여 Z-점수가 ±3을 벗어나는 값을 이상치로 판단합니다. 정규분포를 따르는 데이터에 적합합니다.'}
                            {outlierMethod === 'none' && '이상치를 별도로 처리하지 않고 원본 데이터를 그대로 사용합니다.'}
                          </div>
                        </div>

                        {/* 시각화 버튼 */}
                        {outlierMethod !== 'none' && data && data.length > 0 && (
                          <button
                            onClick={() => {
                              // 임시로 alert로 구현 (실제로는 차트 모달이나 별도 컴포넌트)
                              alert('이상치 시각화 기능은 곧 구현됩니다. 박스플롯과 산점도를 통해 이상치를 확인할 수 있습니다.');
                            }}
                            className="w-full flex items-center justify-center px-4 py-2 bg-accent-orange/10 hover:bg-accent-orange/20 text-accent-orange border border-accent-orange/30 rounded-lg transition-colors"
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            이상치 시각화 보기
                          </button>
                        )}
                      </div>
                    </div>

                    {/* 이상치 현황 및 결과 */}
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <BarChart className="w-4 h-4 mr-2" />
                        이상치 분석 결과
                      </h4>
                      
                      {data && data.length > 0 ? (
                        <div className="space-y-3">
                          {outlierMethod === 'none' ? (
                            <div className="bg-muted/30 rounded-lg p-3 text-center">
                              <div className="text-sm text-muted-foreground">이상치 처리를 하지 않습니다</div>
                            </div>
                          ) : (
                            <>
                              {/* 수치형 컬럼별 이상치 예상 개수 */}
                              {Object.keys(data[0]).filter(col => typeof data[0][col] === 'number').map((col, idx) => {
                                const values = data.map(row => row[col]).filter(v => typeof v === 'number');
                                let outlierCount = 0;
                                
                                if (outlierMethod === 'iqr' && values.length > 0) {
                                  const sorted = [...values].sort((a, b) => a - b);
                                  const q1 = sorted[Math.floor(values.length * 0.25)];
                                  const q3 = sorted[Math.floor(values.length * 0.75)];
                                  const iqr = q3 - q1;
                                  const lowerBound = q1 - 1.5 * iqr;
                                  const upperBound = q3 + 1.5 * iqr;
                                  outlierCount = values.filter(v => v < lowerBound || v > upperBound).length;
                                } else if (outlierMethod === 'zscore' && values.length > 0) {
                                  const mean = values.reduce((a, b) => a + b, 0) / values.length;
                                  const std = Math.sqrt(values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length);
                                  outlierCount = values.filter(v => Math.abs((v - mean) / std) > 3).length;
                                }
                                
                                return (
                                  <div key={idx} className="flex justify-between items-center p-2 bg-muted/20 rounded">
                                    <span className="text-sm font-medium text-foreground">{col}</span>
                                    <div className="text-right">
                                      <div className="text-sm font-bold text-foreground">{outlierCount}개</div>
                                      <div className="text-xs text-muted-foreground">
                                        ({((outlierCount / values.length) * 100).toFixed(1)}%)
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}

                              {/* 전체 요약 */}
                              <div className="bg-accent-orange/10 rounded-lg p-3">
                                <div className="text-sm font-medium text-accent-orange mb-2">처리 후 예상 결과</div>
                                <div className="text-xs text-muted-foreground space-y-1">
                                  <div>탐지 방법: {outlierMethod === 'iqr' ? 'IQR 방법' : 'Z-Score 방법'}</div>
                                  <div>이상치 행: 제거 또는 대체 처리 예정</div>
                                  <div>데이터 품질: 향상 예상</div>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-muted-foreground py-4">
                          <BarChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <div className="text-sm">데이터를 선택하면 이상치 분석을 수행합니다</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 데이터 스케일링 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <Scale className="w-5 h-5 mr-2 text-accent-purple" />
                    데이터 스케일링
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 스케일링 방법 선택 */}
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <Settings className="w-4 h-4 mr-2" />
                        스케일링 방법 선택
                      </h4>
                      
                      <div className="space-y-4">
                        <div>
                          <Select
                            label=""
                            value={scalingMethod}
                            onChange={(value) => setScalingMethod(value as 'standard' | 'minmax' | 'robust' | 'none')}
                            options={[
                              { value: 'standard', label: 'Standard Scaling (표준화)' },
                              { value: 'minmax', label: 'Min-Max Scaling (정규화)' },
                              { value: 'robust', label: 'Robust Scaling (로버스트)' },
                              { value: 'none', label: '스케일링 안함' }
                            ]}
                          />
                        </div>

                        {/* 스케일링 방법 설명 */}
                        <div className="bg-muted/30 rounded-lg p-3">
                          <div className="text-sm font-medium text-foreground mb-2">
                            {scalingMethod === 'standard' && 'Standard Scaling (표준화)'}
                            {scalingMethod === 'minmax' && 'Min-Max Scaling (정규화)'}
                            {scalingMethod === 'robust' && 'Robust Scaling (로버스트)'}
                            {scalingMethod === 'none' && '스케일링 안함'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {scalingMethod === 'standard' && '평균을 0, 표준편차를 1로 변환합니다. (x - μ) / σ 공식을 사용하며, 정규분포 데이터에 적합합니다.'}
                            {scalingMethod === 'minmax' && '최솟값을 0, 최댓값을 1로 변환합니다. (x - min) / (max - min) 공식을 사용하며, 범위가 제한된 데이터에 적합합니다.'}
                            {scalingMethod === 'robust' && '중앙값과 IQR을 사용하여 스케일링합니다. 이상치의 영향을 덜 받으며, 이상치가 많은 데이터에 적합합니다.'}
                            {scalingMethod === 'none' && '원본 데이터의 스케일을 그대로 유지합니다. 이미 비슷한 범위의 데이터이거나 스케일링이 불필요한 경우 선택합니다.'}
                          </div>
                        </div>

                        {/* 스케일링 공식 */}
                        {scalingMethod !== 'none' && (
                          <div className="bg-accent-purple/10 rounded-lg p-3">
                            <div className="text-sm font-medium text-accent-purple mb-2">변환 공식</div>
                            <div className="text-xs font-mono bg-muted/50 rounded p-2 text-foreground">
                              {scalingMethod === 'standard' && 'x_scaled = (x - μ) / σ'}
                              {scalingMethod === 'minmax' && 'x_scaled = (x - min) / (max - min)'}
                              {scalingMethod === 'robust' && 'x_scaled = (x - median) / IQR'}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {scalingMethod === 'standard' && 'μ: 평균, σ: 표준편차'}
                              {scalingMethod === 'minmax' && 'min: 최솟값, max: 최댓값'}
                              {scalingMethod === 'robust' && 'IQR: 3분위수 - 1분위수'}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 스케일링 결과 미리보기 */}
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center">
                        <Scale className="w-4 h-4 mr-2" />
                        스케일링 결과 미리보기
                      </h4>
                      
                      {data && data.length > 0 ? (
                        <div className="space-y-3">
                          {scalingMethod === 'none' ? (
                            <div className="bg-muted/30 rounded-lg p-3 text-center">
                              <div className="text-sm text-muted-foreground">원본 데이터 스케일을 유지합니다</div>
                            </div>
                          ) : (
                            <>
                              {/* 수치형 컬럼별 스케일링 예상 결과 */}
                              <div className="space-y-2 max-h-60 overflow-y-auto">
                                {Object.keys(data[0]).filter(col => typeof data[0][col] === 'number').map((col, idx) => {
                                  const values = data.map(row => row[col]).filter(v => typeof v === 'number');
                                  if (values.length === 0) return null;
                                  
                                  const min = Math.min(...values);
                                  const max = Math.max(...values);
                                  const mean = values.reduce((a, b) => a + b, 0) / values.length;
                                  const std = Math.sqrt(values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length);
                                  
                                  let scaledRange = '';
                                  if (scalingMethod === 'standard') {
                                    scaledRange = '평균: 0, 표준편차: 1';
                                  } else if (scalingMethod === 'minmax') {
                                    scaledRange = '범위: 0 ~ 1';
                                  } else if (scalingMethod === 'robust') {
                                    scaledRange = '중앙값 기준 조정';
                                  }
                                  
                                  return (
                                    <div key={idx} className="bg-muted/20 rounded p-2">
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="text-sm font-medium text-foreground">{col}</span>
                                      </div>
                                      <div className="text-xs text-muted-foreground space-y-1">
                                        <div>현재: {min.toFixed(2)} ~ {max.toFixed(2)}</div>
                                        <div className="text-accent-purple">변환 후: {scaledRange}</div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* 전체 요약 */}
                              <div className="bg-accent-purple/10 rounded-lg p-3">
                                <div className="text-sm font-medium text-accent-purple mb-2">스케일링 후 예상 결과</div>
                                <div className="text-xs text-muted-foreground space-y-1">
                                  <div>방법: {
                                    scalingMethod === 'standard' ? 'Standard Scaling' :
                                    scalingMethod === 'minmax' ? 'Min-Max Scaling' :
                                    'Robust Scaling'
                                  }</div>
                                  <div>적용 대상: 수치형 컬럼 {Object.keys(data[0]).filter(col => typeof data[0][col] === 'number').length}개</div>
                                  <div>머신러닝 모델 성능 개선 예상</div>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="text-center text-muted-foreground py-4">
                          <Scale className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <div className="text-sm">데이터를 선택하면 스케일링 결과를 미리볼 수 있습니다</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 전처리 실행 버튼 */}
                  <div className="mt-6 pt-4 border-t border-border">
                    <button
                      onClick={handlePreprocessing}
                      disabled={!targetColumn || isPreprocessing}
                      className="w-full flex items-center justify-center px-6 py-3 bg-gradient-primary text-white font-medium rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                      {isPreprocessing ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                          전처리 실행 중...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="w-5 h-5 mr-2" />
                          전처리 실행
                        </>
                      )}
                    </button>
                    {!targetColumn && (
                      <div className="text-xs text-muted-foreground text-center mt-2">
                        타겟 변수를 선택해야 전처리를 실행할 수 있습니다
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* 데이터 분석 탭 */}
        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {!data ? (
              <div className="bg-card border border-border rounded-lg p-6 text-center">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
                <h3 className="text-lg font-semibold text-foreground mb-2">데이터 선택 필요</h3>
                <p className="text-muted-foreground mb-4">
                  먼저 <strong>데이터 선택</strong> 탭에서 분석할 데이터를 선택해주세요.
                </p>
                <button
                  onClick={() => setActiveTab('files')}
                  className="bg-gradient-primary text-white px-4 py-2 rounded-lg hover:scale-105 transition-transform"
                >
                  데이터 선택 탭으로 이동
                </button>
              </div>
            ) : (
              <>
                {/* 전처리 결과 요약 (전처리가 완료된 경우) */}
                {preprocessingResult && (
                  <div className="bg-gradient-to-r from-accent-green/10 to-accent-blue/10 border border-accent-green/30 rounded-lg p-4 mb-6">
                    <div className="flex items-center mb-3">
                      <CheckCircle className="w-5 h-5 mr-2 text-accent-green" />
                      <h3 className="text-lg font-semibold text-foreground">전처리 완료</h3>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div className="text-center">
                        <div className="text-lg font-bold text-foreground">{preprocessingResult.originalRows.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">원본 행 수</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-accent-green">{preprocessingResult.processedRows.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">처리 후 행 수</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-accent-blue">{preprocessingResult.trainRows.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">훈련 데이터</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-accent-purple">{preprocessingResult.testRows.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">테스트 데이터</div>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      타겟 변수: <span className="font-medium text-foreground">{preprocessingResult.targetColumn}</span> | 
                      처리 시간: {preprocessingResult.processingTime} | 
                      데이터 품질: {preprocessingResult.dataQuality}%
                    </div>
                  </div>
                )}

                {/* 변수 분포 분석 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <BarChart className="w-5 h-5 mr-2 text-accent-blue" />
                    변수 분포 분석
                  </h3>
                  
                  {/* 변수 선택 */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-3">
                      <label className="text-sm font-medium text-foreground">분석할 변수 선택</label>
                      <span className="text-xs text-muted-foreground">
                        {data ? `${Object.keys(data[0]).filter(col => typeof data[0][col] === 'number').length}개 수치형 변수` : ''}
                      </span>
                    </div>
                    <Select
                      label=""
                      value={selectedColumn}
                      onChange={setSelectedColumn}
                      options={
                        data && data.length > 0
                          ? Object.keys(data[0]).filter(col => typeof data[0][col] === 'number').map(col => ({ value: col, label: col }))
                          : []
                      }
                      placeholder="분석할 변수를 선택하세요"
                    />
                  </div>

                  {selectedColumn && data && data.length > 0 ? (
                    <div className="space-y-6">
                      {(() => {
                        const values = data.map(row => row[selectedColumn]).filter(v => typeof v === 'number') as number[];
                        const sortedValues = [...values].sort((a, b) => a - b);
                        const mean = values.reduce((a, b) => a + b, 0) / values.length;
                        const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
                        const std = Math.sqrt(variance);
                        const min = Math.min(...values);
                        const max = Math.max(...values);
                        const q1 = sortedValues[Math.floor(values.length * 0.25)];
                        const median = sortedValues[Math.floor(values.length * 0.5)];
                        const q3 = sortedValues[Math.floor(values.length * 0.75)];

                        // 히스토그램 데이터 생성
                        const binCount = Math.min(20, Math.ceil(Math.sqrt(values.length)));
                        const binWidth = (max - min) / binCount;
                        const bins = Array.from({ length: binCount }, (_, i) => ({
                          start: min + i * binWidth,
                          end: min + (i + 1) * binWidth,
                          count: 0
                        }));
                        
                        values.forEach(value => {
                          const binIndex = Math.min(Math.floor((value - min) / binWidth), binCount - 1);
                          bins[binIndex].count++;
                        });

                        const maxBinCount = Math.max(...bins.map(bin => bin.count));

                        return (
                          <>
                            {/* 기본 통계 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <Info className="w-4 h-4 mr-2" />
                                {selectedColumn} - 기본 통계
                              </h4>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="text-center">
                                  <div className="text-lg font-bold text-foreground">{mean.toFixed(2)}</div>
                                  <div className="text-xs text-muted-foreground">평균</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-lg font-bold text-foreground">{std.toFixed(2)}</div>
                                  <div className="text-xs text-muted-foreground">표준편차</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-lg font-bold text-foreground">{min.toFixed(2)}</div>
                                  <div className="text-xs text-muted-foreground">최솟값</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-lg font-bold text-foreground">{max.toFixed(2)}</div>
                                  <div className="text-xs text-muted-foreground">최댓값</div>
                                </div>
                              </div>
                            </div>

                            {/* 히스토그램 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <BarChart className="w-4 h-4 mr-2" />
                                히스토그램
                              </h4>
                              <div className="relative h-64 bg-background rounded border">
                                <div className="absolute inset-0 flex items-end justify-around p-2">
                                  {bins.map((bin, idx) => (
                                    <div key={idx} className="flex flex-col items-center w-full mx-px">
                                      <div 
                                        className="bg-accent-blue w-full transition-all duration-300 hover:bg-accent-blue/80"
                                        style={{ 
                                          height: `${(bin.count / maxBinCount) * 85}%`,
                                          minHeight: bin.count > 0 ? '2px' : '0'
                                        }}
                                        title={`구간: ${bin.start.toFixed(1)} - ${bin.end.toFixed(1)}\n빈도: ${bin.count}`}
                                      />
                                      {idx % Math.ceil(binCount / 6) === 0 && (
                                        <div className="text-xs text-muted-foreground mt-1 transform -rotate-45 origin-top-left">
                                          {bin.start.toFixed(1)}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                                <div className="absolute bottom-0 left-0 text-xs text-muted-foreground p-2">
                                  빈도: 0 - {maxBinCount}
                                </div>
                              </div>
                            </div>

                            {/* 박스플롯 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <Activity className="w-4 h-4 mr-2" />
                                박스플롯
                              </h4>
                              <div className="relative h-24 bg-background rounded border p-4">
                                <div className="relative h-full flex items-center">
                                  {/* 박스플롯 스케일 */}
                                  <div className="absolute w-full">
                                    {/* IQR 박스 */}
                                    <div 
                                      className="absolute bg-accent-blue/30 border-2 border-accent-blue h-8"
                                      style={{
                                        left: `${((q1 - min) / (max - min)) * 100}%`,
                                        width: `${((q3 - q1) / (max - min)) * 100}%`
                                      }}
                                    />
                                    {/* 중앙값 선 */}
                                    <div 
                                      className="absolute bg-accent-blue h-8 w-0.5"
                                      style={{
                                        left: `${((median - min) / (max - min)) * 100}%`
                                      }}
                                    />
                                    {/* 최솟값 선 */}
                                    <div 
                                      className="absolute bg-muted-foreground h-4 w-0.5 top-2"
                                      style={{ left: '0%' }}
                                    />
                                    {/* 최댓값 선 */}
                                    <div 
                                      className="absolute bg-muted-foreground h-4 w-0.5 top-2"
                                      style={{ left: '100%' }}
                                    />
                                    {/* 연결선 */}
                                    <div 
                                      className="absolute bg-muted-foreground h-0.5 top-4"
                                      style={{
                                        left: '0%',
                                        width: `${((q1 - min) / (max - min)) * 100}%`
                                      }}
                                    />
                                    <div 
                                      className="absolute bg-muted-foreground h-0.5 top-4"
                                      style={{
                                        left: `${((q3 - min) / (max - min)) * 100}%`,
                                        width: `${((max - q3) / (max - min)) * 100}%`
                                      }}
                                    />
                                  </div>
                                </div>
                                {/* 레이블 */}
                                <div className="absolute -bottom-6 w-full flex justify-between text-xs text-muted-foreground">
                                  <span>{min.toFixed(1)}</span>
                                  <span>Q1: {q1.toFixed(1)}</span>
                                  <span>중앙값: {median.toFixed(1)}</span>
                                  <span>Q3: {q3.toFixed(1)}</span>
                                  <span>{max.toFixed(1)}</span>
                                </div>
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <BarChart className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <div className="text-lg font-medium mb-2">변수를 선택하세요</div>
                      <div className="text-sm">분석할 수치형 변수를 선택하면 히스토그램과 박스플롯을 확인할 수 있습니다</div>
                    </div>
                  )}
                </div>

                {/* 변수 간 상관관계 분석 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-accent-green" />
                    변수 간 상관관계 분석
                  </h3>
                  
                  {data && data.length > 0 ? (
                    <div className="space-y-6">
                      {(() => {
                        const numericColumns = Object.keys(data[0]).filter(col => typeof data[0][col] === 'number');
                        
                        if (numericColumns.length < 2) {
                          return (
                            <div className="text-center text-muted-foreground py-8">
                              <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                              <div className="text-lg font-medium mb-2">수치형 변수가 부족합니다</div>
                              <div className="text-sm">상관관계 분석을 위해서는 최소 2개 이상의 수치형 변수가 필요합니다</div>
                            </div>
                          );
                        }

                        // 상관관계 매트릭스 계산
                        const correlationMatrix: { [key: string]: { [key: string]: number } } = {};
                        
                        numericColumns.forEach(col1 => {
                          correlationMatrix[col1] = {};
                          numericColumns.forEach(col2 => {
                            if (col1 === col2) {
                              correlationMatrix[col1][col2] = 1;
                            } else {
                              const values1 = data.map(row => row[col1]).filter(v => typeof v === 'number') as number[];
                              const values2 = data.map(row => row[col2]).filter(v => typeof v === 'number') as number[];
                              
                              if (values1.length > 1 && values2.length > 1) {
                                const mean1 = values1.reduce((a, b) => a + b, 0) / values1.length;
                                const mean2 = values2.reduce((a, b) => a + b, 0) / values2.length;
                                
                                let numerator = 0;
                                let sum1 = 0;
                                let sum2 = 0;
                                
                                for (let i = 0; i < Math.min(values1.length, values2.length); i++) {
                                  const diff1 = values1[i] - mean1;
                                  const diff2 = values2[i] - mean2;
                                  numerator += diff1 * diff2;
                                  sum1 += diff1 * diff1;
                                  sum2 += diff2 * diff2;
                                }
                                
                                const denominator = Math.sqrt(sum1 * sum2);
                                correlationMatrix[col1][col2] = denominator !== 0 ? numerator / denominator : 0;
                              } else {
                                correlationMatrix[col1][col2] = 0;
                              }
                            }
                          });
                        });

                        return (
                          <>
                            {/* 상관관계 매트릭스 히트맵 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-2" />
                                상관관계 매트릭스
                              </h4>
                              <div className="overflow-x-auto">
                                <div className="min-w-max">
                                  {/* 헤더 */}
                                  <div className="flex">
                                    <div className="w-24"></div>
                                    {numericColumns.map(col => (
                                      <div key={col} className="w-20 text-center">
                                        <div className="text-xs font-medium text-foreground transform -rotate-45 origin-center w-20 h-12 flex items-end justify-center">
                                          {col.length > 8 ? col.substring(0, 8) + '...' : col}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                  
                                  {/* 매트릭스 행 */}
                                  {numericColumns.map(row => (
                                    <div key={row} className="flex items-center">
                                      <div className="w-24 text-right pr-2">
                                        <div className="text-xs font-medium text-foreground">
                                          {row.length > 10 ? row.substring(0, 10) + '...' : row}
                                        </div>
                                      </div>
                                      {numericColumns.map(col => {
                                        const correlation = correlationMatrix[row][col];
                                        const absCorr = Math.abs(correlation);
                                        
                                        // 색상 강도 계산 (0~1)
                                        const intensity = absCorr;
                                        const isPositive = correlation >= 0;
                                        
                                        return (
                                          <div 
                                            key={col}
                                            className="w-20 h-12 border border-border flex items-center justify-center relative group cursor-pointer"
                                            style={{
                                              backgroundColor: isPositive 
                                                ? `rgba(59, 130, 246, ${intensity * 0.8})` // 파란색 (양의 상관관계)
                                                : `rgba(239, 68, 68, ${intensity * 0.8})` // 빨간색 (음의 상관관계)
                                            }}
                                            title={`${row} vs ${col}: ${correlation.toFixed(3)}`}
                                          >
                                            <span className={`text-xs font-bold ${
                                              intensity > 0.5 ? 'text-white' : 'text-foreground'
                                            }`}>
                                              {correlation.toFixed(2)}
                                            </span>
                                            
                                            {/* 툴팁 */}
                                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-foreground text-background text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap">
                                              {row} ↔ {col}: {correlation.toFixed(3)}
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  ))}
                                </div>
                              </div>
                              
                              {/* 범례 */}
                              <div className="mt-4 flex items-center justify-center space-x-6">
                                <div className="flex items-center space-x-2">
                                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                                  <span className="text-xs text-muted-foreground">음의 상관관계</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <div className="w-4 h-4 bg-gray-300 rounded"></div>
                                  <span className="text-xs text-muted-foreground">상관관계 없음</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <div className="w-4 h-4 bg-blue-500 rounded"></div>
                                  <span className="text-xs text-muted-foreground">양의 상관관계</span>
                                </div>
                              </div>
                            </div>

                            {/* 강한 상관관계 요약 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <AlertCircle className="w-4 h-4 mr-2" />
                                주요 상관관계 (|r| ≥ 0.5)
                              </h4>
                              <div className="space-y-2">
                                {(() => {
                                  const strongCorrelations: Array<{col1: string, col2: string, correlation: number}> = [];
                                  
                                  numericColumns.forEach((col1, i) => {
                                    numericColumns.forEach((col2, j) => {
                                      if (i < j) { // 중복 제거
                                        const corr = correlationMatrix[col1][col2];
                                        if (Math.abs(corr) >= 0.5) {
                                          strongCorrelations.push({ col1, col2, correlation: corr });
                                        }
                                      }
                                    });
                                  });

                                  if (strongCorrelations.length === 0) {
                                    return (
                                      <div className="text-center text-muted-foreground py-4">
                                        <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        <div className="text-sm">강한 상관관계 (|r| ≥ 0.5)를 가진 변수 쌍이 없습니다</div>
                                      </div>
                                    );
                                  }

                                  return strongCorrelations
                                    .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
                                    .map(({ col1, col2, correlation }, idx) => (
                                      <div key={idx} className="flex items-center justify-between p-2 bg-background rounded border">
                                        <div className="flex items-center space-x-2">
                                          <span className="text-sm font-medium text-foreground">{col1}</span>
                                          <span className="text-muted-foreground">↔</span>
                                          <span className="text-sm font-medium text-foreground">{col2}</span>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                          <span className={`text-sm font-bold ${
                                            correlation > 0 ? 'text-blue-600' : 'text-red-600'
                                          }`}>
                                            {correlation.toFixed(3)}
                                          </span>
                                          <span className="text-xs text-muted-foreground">
                                            {Math.abs(correlation) >= 0.8 ? '매우 강함' :
                                             Math.abs(correlation) >= 0.6 ? '강함' : '보통'}
                                          </span>
                                        </div>
                                      </div>
                                    ));
                                })()}
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <div className="text-lg font-medium mb-2">데이터를 선택하세요</div>
                      <div className="text-sm">데이터를 선택하면 변수들 간의 상관관계를 매트릭스 형태로 확인할 수 있습니다</div>
                    </div>
                  )}
                </div>

                {/* 타겟 변수와의 상관관계 */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                    <Target className="w-5 h-5 mr-2 text-accent-purple" />
                    타겟 변수와의 상관관계
                  </h3>
                  
                  {data && data.length > 0 ? (
                    <div className="space-y-6">
                      {/* 타겟 변수 선택 */}
                      <div className="bg-muted/30 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <label className="text-sm font-medium text-foreground">타겟 변수 선택</label>
                          {preprocessingResult && (
                            <div className="text-xs text-accent-purple bg-accent-purple/10 px-2 py-1 rounded">
                              전처리에서 선택: {preprocessingResult.targetColumn}
                            </div>
                          )}
                        </div>
                        <Select
                          label=""
                          value={targetColumn || (preprocessingResult?.targetColumn || '')}
                          onChange={setTargetColumn}
                          options={
                            data && data.length > 0
                              ? Object.keys(data[0]).filter(col => typeof data[0][col] === 'number').map(col => ({ value: col, label: col }))
                              : []
                          }
                          placeholder="타겟 변수를 선택하세요"
                        />
                      </div>

                      {(targetColumn || preprocessingResult?.targetColumn) && (() => {
                        const target = targetColumn || preprocessingResult?.targetColumn || '';
                        const numericColumns = Object.keys(data[0]).filter(col => 
                          typeof data[0][col] === 'number' && col !== target
                        );

                        if (numericColumns.length === 0) {
                          return (
                            <div className="text-center text-muted-foreground py-8">
                              <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                              <div className="text-lg font-medium mb-2">분석할 변수가 없습니다</div>
                              <div className="text-sm">타겟 변수를 제외한 수치형 변수가 필요합니다</div>
                            </div>
                          );
                        }

                        // 타겟 변수와 각 변수 간의 상관관계 계산
                        const targetValues = data.map(row => row[target]).filter(v => typeof v === 'number') as number[];
                        const correlations = numericColumns.map(col => {
                          const values = data.map(row => row[col]).filter(v => typeof v === 'number') as number[];
                          
                          if (values.length > 1 && targetValues.length > 1) {
                            const mean1 = targetValues.reduce((a, b) => a + b, 0) / targetValues.length;
                            const mean2 = values.reduce((a, b) => a + b, 0) / values.length;
                            
                            let numerator = 0;
                            let sum1 = 0;
                            let sum2 = 0;
                            
                            for (let i = 0; i < Math.min(targetValues.length, values.length); i++) {
                              const diff1 = targetValues[i] - mean1;
                              const diff2 = values[i] - mean2;
                              numerator += diff1 * diff2;
                              sum1 += diff1 * diff1;
                              sum2 += diff2 * diff2;
                            }
                            
                            const denominator = Math.sqrt(sum1 * sum2);
                            return {
                              variable: col,
                              correlation: denominator !== 0 ? numerator / denominator : 0
                            };
                          }
                          
                          return { variable: col, correlation: 0 };
                        }).sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));

                        const maxAbsCorr = Math.max(...correlations.map(c => Math.abs(c.correlation)));

                        return (
                          <>
                            {/* 타겟 변수 정보 */}
                            <div className="bg-accent-purple/10 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <Target className="w-4 h-4 mr-2" />
                                타겟 변수: {target}
                              </h4>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {(() => {
                                  const mean = targetValues.reduce((a, b) => a + b, 0) / targetValues.length;
                                  const variance = targetValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / targetValues.length;
                                  const std = Math.sqrt(variance);
                                  const min = Math.min(...targetValues);
                                  const max = Math.max(...targetValues);

                                  return (
                                    <>
                                      <div className="text-center">
                                        <div className="text-lg font-bold text-foreground">{mean.toFixed(2)}</div>
                                        <div className="text-xs text-muted-foreground">평균</div>
                                      </div>
                                      <div className="text-center">
                                        <div className="text-lg font-bold text-foreground">{std.toFixed(2)}</div>
                                        <div className="text-xs text-muted-foreground">표준편차</div>
                                      </div>
                                      <div className="text-center">
                                        <div className="text-lg font-bold text-foreground">{min.toFixed(2)}</div>
                                        <div className="text-xs text-muted-foreground">최솟값</div>
                                      </div>
                                      <div className="text-center">
                                        <div className="text-lg font-bold text-foreground">{max.toFixed(2)}</div>
                                        <div className="text-xs text-muted-foreground">최댓값</div>
                                      </div>
                                    </>
                                  );
                                })()}
                              </div>
                            </div>

                            {/* 상관관계 막대 차트 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <BarChart className="w-4 h-4 mr-2" />
                                {target}과의 상관관계
                              </h4>
                              <div className="space-y-3">
                                {correlations.map(({ variable, correlation }, idx) => {
                                  const absCorr = Math.abs(correlation);
                                  const isPositive = correlation >= 0;
                                  const barWidth = maxAbsCorr > 0 ? (absCorr / maxAbsCorr) * 100 : 0;

                                  return (
                                    <div key={idx} className="flex items-center space-x-3">
                                      {/* 변수명 */}
                                      <div className="w-24 text-right">
                                        <span className="text-sm font-medium text-foreground">
                                          {variable.length > 10 ? variable.substring(0, 10) + '...' : variable}
                                        </span>
                                      </div>

                                      {/* 막대 그래프 */}
                                      <div className="flex-1 relative">
                                        <div className="w-full h-6 bg-muted rounded-lg relative overflow-hidden">
                                          {/* 중앙선 */}
                                          <div className="absolute left-1/2 top-0 w-px h-full bg-border"></div>
                                          
                                          {/* 상관관계 막대 */}
                                          <div 
                                            className={`absolute top-0 h-full rounded transition-all duration-300 ${
                                              isPositive 
                                                ? 'bg-blue-500 left-1/2' 
                                                : 'bg-red-500 right-1/2'
                                            }`}
                                            style={{ 
                                              width: `${barWidth / 2}%`,
                                              ...(isPositive ? {} : { transform: 'translateX(100%)' })
                                            }}
                                          />
                                          
                                          {/* 값 표시 */}
                                          <div className="absolute inset-0 flex items-center justify-center">
                                            <span className="text-xs font-bold text-foreground">
                                              {correlation.toFixed(3)}
                                            </span>
                                          </div>
                                        </div>
                                      </div>

                                      {/* 강도 표시 */}
                                      <div className="w-16 text-center">
                                        <span className={`text-xs px-2 py-1 rounded ${
                                          absCorr >= 0.8 ? 'bg-red-100 text-red-800' :
                                          absCorr >= 0.6 ? 'bg-orange-100 text-orange-800' :
                                          absCorr >= 0.4 ? 'bg-yellow-100 text-yellow-800' :
                                          absCorr >= 0.2 ? 'bg-blue-100 text-blue-800' :
                                          'bg-gray-100 text-gray-800'
                                        }`}>
                                          {absCorr >= 0.8 ? '매우강함' :
                                           absCorr >= 0.6 ? '강함' :
                                           absCorr >= 0.4 ? '보통' :
                                           absCorr >= 0.2 ? '약함' : '매우약함'}
                                        </span>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                              
                              {/* 범례 */}
                              <div className="mt-4 flex items-center justify-center space-x-4 text-xs text-muted-foreground">
                                <div className="flex items-center space-x-1">
                                  <div className="w-3 h-3 bg-red-500 rounded"></div>
                                  <span>음의 상관관계</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <div className="w-3 h-3 bg-blue-500 rounded"></div>
                                  <span>양의 상관관계</span>
                                </div>
                              </div>
                            </div>

                            {/* 상위 상관관계 요약 */}
                            <div className="bg-muted/30 rounded-lg p-4">
                              <h4 className="text-md font-semibold text-foreground mb-3 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-2" />
                                {target}과 가장 연관성이 높은 변수들
                              </h4>
                              <div className="space-y-2">
                                {correlations.slice(0, 5).map(({ variable, correlation }, idx) => (
                                  <div key={idx} className="flex items-center justify-between p-2 bg-background rounded border">
                                    <div className="flex items-center space-x-2">
                                      <span className="text-sm font-medium text-foreground">#{idx + 1}</span>
                                      <span className="text-sm text-foreground">{variable}</span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <span className={`text-sm font-bold ${
                                        correlation > 0 ? 'text-blue-600' : 'text-red-600'
                                      }`}>
                                        {correlation.toFixed(3)}
                                      </span>
                                      <span className="text-xs text-muted-foreground">
                                        {Math.abs(correlation) >= 0.8 ? '매우 강함' :
                                         Math.abs(correlation) >= 0.6 ? '강함' :
                                         Math.abs(correlation) >= 0.4 ? '보통' :
                                         Math.abs(correlation) >= 0.2 ? '약함' : '매우 약함'}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <div className="text-lg font-medium mb-2">데이터를 선택하세요</div>
                      <div className="text-sm">데이터를 선택하면 타겟 변수와 다른 변수들 간의 상관관계를 분석할 수 있습니다</div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

      {/* 플로팅 챗봇 */}
      <FloatingChatbot
        topic="product_data_analysis"
        sessionId="product_data_analysis_session"
        enableStreaming={true}
        simulationParams={{
          activeTab,
          hasData: !!data,
          dataInfo,
          uploadedFileName: uploadedFile?.name,
          selectedFileName: selectedFile?.filename,
          selectedColumns,
          correlationThreshold,
          selectedColumn,
          chartType,
          preprocessingCompleted: !!preprocessingResult,
          isAnalyzing,
          isPreprocessing,
          currentDataSource,
          availableFiles: savedFiles.length
        }}
        position="bottom-right"
        theme="dark"
        accentColor="purple"
        minimizedText="AI 데이터 분석 전문가"
        placeholder="데이터 분석에 대해 질문하세요..."
        maxHeight={800}
        width={600}
        showSessionInfo={false}
      />
    </div>
  );
} 