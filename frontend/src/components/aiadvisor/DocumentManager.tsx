'use client'

import { useState, useEffect, useRef } from 'react'
import { File, Upload, Trash2, Search, AlertCircle, CheckCircle, Clock, Database, FileText, Download } from 'lucide-react'
import { aiAdvisorService } from '@/services/aiadvisor'

interface Document {
  document_id: string
  filename: string
  category: string
  description: string
  uploaded_at: string
  file_size: number
  processed_sections: number
  extracted_entities: number
  status: string
  summary?: string
}

interface UploadProgress {
  stage: string
  progress: number
  message: string
}

interface DocumentManagerProps {
  onDocumentChange?: () => void
}

export default function DocumentManager({ onDocumentChange }: DocumentManagerProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploadingDocument, setUploadingDocument] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await aiAdvisorService.listDocuments()
      setDocuments(response.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
      setError('문서 목록을 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    let progressInterval: NodeJS.Timeout | undefined

    setUploadingDocument(true)
    setError(null)
    setUploadProgress({
      stage: '파일 업로드',
      progress: 0,
      message: '파일을 서버로 전송하는 중...'
    })

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', selectedCategory === 'all' ? 'general' : selectedCategory)
      formData.append('description', `업로드된 문서: ${file.name}`)

      // 실제 업로드 진행률 표시
      const startTime = Date.now()
      const estimatedTime = 10000 // 10초 예상
      
      const updateProgress = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min((elapsed / estimatedTime) * 90, 90) // 최대 90%까지
        const stage = progress < 30 ? '파일 업로드' : 
                     progress < 50 ? '문서 파싱' : 
                     progress < 70 ? '청크 생성' : '벡터 생성'
        const message = progress < 30 ? '파일을 서버로 전송하는 중...' :
                       progress < 50 ? '문서 내용을 분석하는 중...' :
                       progress < 70 ? '문서를 청크로 분할하는 중...' : '벡터 데이터베이스에 저장하는 중...'
        
        setUploadProgress({ stage, progress: Math.round(progress), message })
      }
      
      // 진행률 업데이트 인터벌 시작
      progressInterval = setInterval(updateProgress, 200)
      
      // 초기 진행률 설정
      updateProgress()

      await aiAdvisorService.uploadDocument(formData)
      
      // 문서 목록 새로고침
      await loadDocuments()
      
      // 부모 컴포넌트에 변경 알림
      if (onDocumentChange) {
        onDocumentChange()
      }

    } catch (err) {
      console.error('Document upload error:', err)
      setError('문서 업로드 중 오류가 발생했습니다.')
    } finally {
      // 진행률 인터벌 정리
      if (progressInterval) {
        clearInterval(progressInterval)
      }
      
      // 완료 상태 표시
      setUploadProgress({ stage: '완료', progress: 100, message: '문서 업로드가 완료되었습니다.' })
      
      // 잠시 후 진행률 숨기기
      setTimeout(() => {
        setUploadingDocument(false)
        setUploadProgress(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }, 1000)
    }
  }

  const handleDeleteDocument = async (documentId: string, filename: string) => {
    if (!confirm(`문서 "${filename}"을 삭제하시겠습니까?`)) {
      return
    }

    try {
      setError(null)
      await aiAdvisorService.deleteDocument(documentId)
      
      // 문서 목록 새로고침
      await loadDocuments()
      
      // 부모 컴포넌트에 변경 알림
      if (onDocumentChange) {
        onDocumentChange()
      }

    } catch (err) {
      console.error('Document deletion error:', err)
      setError('문서 삭제 중 오류가 발생했습니다.')
    }
  }

  const handleDownloadDocument = async (documentId: string, filename: string) => {
    try {
      setError(null)
      const blob = await aiAdvisorService.downloadDocument(documentId)
      
      // 다운로드 링크 생성
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      
      // 정리
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
    } catch (err) {
      console.error('Document download error:', err)
      setError('문서 다운로드 중 오류가 발생했습니다.')
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      await loadDocuments()
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await aiAdvisorService.searchDocuments(searchQuery, 20, selectedCategory === 'all' ? undefined : selectedCategory)
      setDocuments(response.documents || [])
    } catch (err) {
      console.error('Search failed:', err)
      setError('문서 검색 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatSummary = (summary: string) => {
    // 원본 청크 내용이 아닌 실제 요약만 표시
    if (!summary) return ''
    
    // 패턴 1: "요약: [category] filename" 형태 제거
    let cleanSummary = summary.replace(/^요약:\s*\[[^\]]+\]\s*[^(]+\([^)]+\)\s*-\s*/i, '')
    
    // 패턴 2: "요약:" 키워드 다음의 실제 내용 추출
    const summaryMatch = cleanSummary.match(/요약:\s*(.+?)(?:\n|$)/i)
    if (summaryMatch) {
      cleanSummary = summaryMatch[1].trim()
    }
    
    // 패턴 3: "--- 페이지 X ---" 형태의 메타데이터 제거
    cleanSummary = cleanSummary.replace(/---\s*페이지\s*\d+\s*---/g, '')
    
    // 패턴 4: 파일명이나 메타데이터로 보이는 부분 제거
    cleanSummary = cleanSummary.replace(/^[^가-힣a-zA-Z]*/, '')
    
    // 실제 내용이 있는 첫 번째 문장 찾기
    const sentences = cleanSummary.split(/[.!?]/)
    for (const sentence of sentences) {
      const trimmed = sentence.trim()
      if (trimmed.length > 10 && /[가-힣]/.test(trimmed)) {
        return trimmed.length > 200 ? trimmed.substring(0, 200) + '...' : trimmed
      }
    }
    
    // 적절한 문장을 찾지 못한 경우, 전체를 정리해서 반환
    cleanSummary = cleanSummary.trim()
    if (cleanSummary.length > 10) {
      return cleanSummary.length > 200 ? cleanSummary.substring(0, 200) + '...' : cleanSummary
    }
    
    return '요약 정보가 없습니다.'
  }

  const formatDescription = (description: string) => {
    if (!description) return ''
    
    // 청크 내용이 아닌 실제 설명만 표시
    if (description.includes('페이지') || description.includes('---')) {
      // 페이지 정보나 구분자가 있는 경우 첫 번째 실제 내용 부분만 추출
      const cleanContent = description.split('---').pop()?.trim() || description
      return cleanContent.length > 150 ? cleanContent.substring(0, 150) + '...' : cleanContent
    }
    
    return description.length > 150 ? description.substring(0, 150) + '...' : description
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'processed':
        return '처리 완료'
      case 'processing':
        return '처리 중'
      case 'error':
        return '오류'
      case 'completed':
        return '완료'
      default:
        return '대기 중'
    }
  }

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const categories = ['all', 'general', 'manual', 'report', 'analysis']

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">문서 업로드</h3>
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.docx,.md"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingDocument}
              className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>{uploadingDocument ? '업로드 중...' : '문서 선택'}</span>
            </button>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background text-foreground"
            >
              <option value="all">모든 카테고리</option>
              <option value="general">일반</option>
              <option value="manual">매뉴얼</option>
              <option value="report">리포트</option>
              <option value="analysis">분석</option>
            </select>
            <span className="text-sm text-muted-foreground">
              지원 형식: PDF, TXT, DOCX, MD
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            업로드된 문서는 AI가 답변할 때 참고 자료로 사용됩니다.
          </p>
          
          {/* Upload Progress */}
          {uploadProgress && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-800">{uploadProgress.stage}</span>
                <span className="text-sm text-blue-600">{uploadProgress.progress}%</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress.progress}%` }}
                ></div>
              </div>
              <p className="text-sm text-blue-700 mt-2">{uploadProgress.message}</p>
            </div>
          )}
        </div>
      </div>

      {/* Search Section */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">문서 검색</h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="문서명 또는 내용으로 검색..."
              className="w-full pl-12 pr-4 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            검색
          </button>
          <button
            onClick={() => {
              setSearchQuery('')
              setSelectedCategory('all')
              loadDocuments()
            }}
            className="px-4 py-2 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors"
          >
            초기화
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">업로드된 문서</h3>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              총 {documents.length}개 문서
            </span>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground mt-2">문서 목록을 불러오는 중...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-8">
            <File className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              {searchQuery ? '검색 결과가 없습니다.' : '업로드된 문서가 없습니다.'}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              문서를 업로드하여 AI가 더 정확한 답변을 제공할 수 있도록 하세요.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredDocuments.map((doc) => (
              <div key={doc.document_id} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors">
                <div className="flex items-center space-x-3 flex-1">
                  <FileText className="w-5 h-5 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-foreground truncate">{doc.filename}</p>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDownloadDocument(doc.document_id, doc.filename)}
                          className="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="문서 다운로드"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        {getStatusIcon(doc.status)}
                      </div>
                    </div>
                    <div className="flex items-center space-x-4 mt-1">
                      <p className="text-sm text-muted-foreground">
                        업로드: {new Date(doc.uploaded_at).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        크기: {formatFileSize(doc.file_size)}
                      </p>
                      {doc.processed_sections > 0 && (
                        <p className="text-sm text-muted-foreground">
                          {doc.processed_sections} 페이지
                        </p>
                      )}
                      {doc.extracted_entities > 0 && (
                        <p className="text-sm text-muted-foreground">
                          엔티티: {doc.extracted_entities}개
                        </p>
                      )}
                    </div>
                    {doc.summary && (
                      <div className="mt-2 p-2 bg-blue-50 border-l-4 border-blue-200 rounded">
                        <p className="text-sm text-blue-800 line-clamp-3">
                          <span className="font-medium">요약:</span> {formatSummary(doc.summary)}
                        </p>
                      </div>
                    )}
                    {!doc.summary && doc.description && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {formatDescription(doc.description)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleDeleteDocument(doc.document_id, doc.filename)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="문서 삭제"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
} 