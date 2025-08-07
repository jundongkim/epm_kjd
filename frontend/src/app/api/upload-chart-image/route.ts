import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const image = formData.get('image') as File
    const metadata = formData.get('metadata') as string

    if (!image) {
      return NextResponse.json({ error: 'No image provided' }, { status: 400 })
    }

    // 파싱된 메타데이터
    let parsedMetadata = {}
    if (metadata) {
      try {
        parsedMetadata = JSON.parse(metadata)
      } catch (error) {
        console.warn('메타데이터 파싱 실패:', error)
      }
    }

    // 이미지 저장 디렉토리 설정
    const uploadDir = path.join(process.cwd(), 'public', 'uploads', 'chart-images')
    
    // 디렉토리가 존재하지 않으면 생성
    if (!existsSync(uploadDir)) {
      await mkdir(uploadDir, { recursive: true })
    }

    // 파일명 생성 (안전한 파일명으로 변경)
    const originalName = image.name
    const fileExtension = path.extname(originalName)
    const baseName = path.basename(originalName, fileExtension)
    const safeFileName = baseName.replace(/[^a-zA-Z0-9\-_]/g, '_')
    const fileName = `${safeFileName}${fileExtension}`
    
    const filePath = path.join(uploadDir, fileName)
    const relativePath = `/uploads/chart-images/${fileName}`

    // 이미지 파일을 서버에 저장
    const bytes = await image.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filePath, buffer)

    // 메타데이터와 함께 응답 (향후 DB 저장용)
    const response = {
      success: true,
      imagePath: relativePath,
      fullPath: filePath,
      fileName: fileName,
      originalName: originalName,
      size: buffer.length,
      uploadedAt: new Date().toISOString(),
      metadata: parsedMetadata
    }

    console.log('차트 이미지 저장 완료:', response)

    return NextResponse.json(response)

  } catch (error) {
    console.error('이미지 업로드 중 오류:', error)
    return NextResponse.json(
      { error: 'Failed to upload image', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

// GET 요청으로 저장된 이미지 목록 조회 (선택사항)
export async function GET() {
  try {
    const uploadDir = path.join(process.cwd(), 'public', 'uploads', 'chart-images')
    
    if (!existsSync(uploadDir)) {
      return NextResponse.json({ images: [] })
    }

    // 향후 DB에서 이미지 메타데이터를 조회하는 로직으로 대체 가능
    return NextResponse.json({ 
      message: 'Chart images endpoint active',
      uploadDir: '/uploads/chart-images/'
    })

  } catch (error) {
    console.error('이미지 목록 조회 중 오류:', error)
    return NextResponse.json(
      { error: 'Failed to get images' },
      { status: 500 }
    )
  }
} 