import { NextRequest, NextResponse } from 'next/server'

// DB 저장을 위한 차트 메타데이터 인터페이스
interface ChartMetadata {
  id?: string
  originalFilename: string
  imagePath: string
  chartType: string
  viewMode: string
  chartName?: string
  chartId: string
  uploadedAt: string
  fileSize: number
  analysisConfig: {
    timestampColumn: string
    visualizationColumns: string[]
    excludeColumns: string[]
    timeUnit?: string
  }
  statistics?: {
    dataPointsCount: number
    columnCount: number
    timeRange: string
  }
  comparisonSegments?: Array<{
    id: string
    column: string
    startTime: string
    endTime: string
    dataPointsCount: number
  }>
}

// 메모리 저장소 (실제 환경에서는 실제 DB로 대체)
const chartMetadataStore: ChartMetadata[] = []

// POST: 차트 메타데이터 저장
export async function POST(request: NextRequest) {
  try {
    const metadataArray: ChartMetadata[] = await request.json()

    if (!Array.isArray(metadataArray)) {
      return NextResponse.json(
        { error: 'Invalid data format. Expected array of metadata objects.' },
        { status: 400 }
      )
    }

    const savedMetadata = metadataArray.map(metadata => {
      const id = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const enrichedMetadata = {
        ...metadata,
        id,
        savedAt: new Date().toISOString()
      }

      // 실제 환경에서는 여기서 DB에 저장
      chartMetadataStore.push(enrichedMetadata)
      
      console.log('차트 메타데이터 저장됨:', enrichedMetadata)
      return enrichedMetadata
    })

    return NextResponse.json({
      success: true,
      message: `${savedMetadata.length}개의 차트 메타데이터가 저장되었습니다.`,
      data: savedMetadata
    })

  } catch (error) {
    console.error('메타데이터 저장 중 오류:', error)
    return NextResponse.json(
      { error: 'Failed to save metadata', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

// GET: 저장된 차트 메타데이터 조회
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const originalFilename = searchParams.get('filename')
    const chartType = searchParams.get('chartType')
    const limit = parseInt(searchParams.get('limit') || '50')
    const offset = parseInt(searchParams.get('offset') || '0')

    let filteredData = [...chartMetadataStore]

    // 필터링
    if (originalFilename) {
      filteredData = filteredData.filter(item => 
        item.originalFilename.toLowerCase().includes(originalFilename.toLowerCase())
      )
    }

    if (chartType) {
      filteredData = filteredData.filter(item => item.chartType === chartType)
    }

    // 페이지네이션
    const total = filteredData.length
    const paginatedData = filteredData
      .sort((a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime())
      .slice(offset, offset + limit)

    return NextResponse.json({
      success: true,
      data: paginatedData,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      }
    })

  } catch (error) {
    console.error('메타데이터 조회 중 오류:', error)
    return NextResponse.json(
      { error: 'Failed to get metadata' },
      { status: 500 }
    )
  }
}

// DELETE: 특정 차트 메타데이터 삭제
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json(
        { error: 'Chart ID is required' },
        { status: 400 }
      )
    }

    const index = chartMetadataStore.findIndex(item => item.id === id)
    
    if (index === -1) {
      return NextResponse.json(
        { error: 'Chart metadata not found' },
        { status: 404 }
      )
    }

    const deletedItem = chartMetadataStore.splice(index, 1)[0]

    return NextResponse.json({
      success: true,
      message: '차트 메타데이터가 삭제되었습니다.',
      deletedItem
    })

  } catch (error) {
    console.error('메타데이터 삭제 중 오류:', error)
    return NextResponse.json(
      { error: 'Failed to delete metadata' },
      { status: 500 }
    )
  }
} 