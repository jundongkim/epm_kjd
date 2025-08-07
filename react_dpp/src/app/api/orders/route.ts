import { NextResponse } from 'next/server'
import prisma from '@/lib/prisma'
import Papa from 'papaparse'
import { Prisma } from '@prisma/client'

// Helper function to clean and convert numeric values
function toFloat(value: any): number | null {
  if (value === null || value === undefined || value === '' || value === '-') {
    return null
  }
  const strValue = String(value).replace(/,/g, '')
  const num = parseFloat(strValue)
  return isNaN(num) ? null : num
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const customVersionName = formData.get('versionName') as string | null
    const versionName = customVersionName || file.name;

    if (!file) {
      return NextResponse.json({ error: '파일이 없습니다.' }, { status: 400 })
    }

    if (file.type !== 'text/csv') {
      return NextResponse.json({ error: 'CSV 파일만 업로드 가능합니다.' }, { status: 400 })
    }

    const fileContent = await file.text()

    const parseResult = Papa.parse(fileContent, {
      header: true,
      skipEmptyLines: true,
    })

    if (parseResult.errors.length > 0) {
      console.error('CSV Parsing errors:', parseResult.errors)
      return NextResponse.json({ error: 'CSV 파싱 중 오류가 발생했습니다.', details: parseResult.errors }, { status: 400 })
    }

    const dataToInsert = parseResult.data.map((row: any) => ({
      division: row['구분'],
      team: row['팀'],
      customer_name: row['고객명'],
      steel_grade_ordered: row['강종(주문)'],
      steel_grade_produced: row['강종(생산)'],
      code: row['코드'],
      steel_plant: row['제강공장'],
      code2: row['코드2'],
      rolling: row['압연'],
      thickness: toFloat(row['두께']),
      product_length: toFloat(row['길이(제품)']),
      material_length: row['길이(소재)'],
      requested_quantity: row['요청량'],
      stock_quantity: row['재고량'],
      steelmaking_quantity: row['제강량'],
      ch_count: toFloat(row['Ch수']),
      final_production_quantity: row['생산량(최종)'],
      usage: row['용도별'],
      adjusted_quantity: row['조정량'],
      carryover_order: row['이월주문'],
      small_lot_classification: row['소LOT분류'],
      production_increase_review: row['생산증량 검토 시'],
      remarks_factory: row['비고(공장)'],
      remarks_sales: row['비고(영업) - 특기사항'],
      remarks: row['비고'],
      requested_line: row['요청라인'],
    })).filter(d => d.customer_name)

    const newOrderVersion = await prisma.orderVersion.create({
      data: {
        name: versionName,
      },
    });

    const dataWithVersion = dataToInsert.map(order => ({
      ...order,
      orderVersionId: newOrderVersion.id,
    }));

    await prisma.order.createMany({
      data: dataWithVersion,
    });

    return NextResponse.json({ message: '성공적으로 업로드 및 저장되었습니다.' }, { status: 201 })
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json({ error: '서버 내부 오류가 발생했습니다.' }, { status: 500 })
  }
}


export async function GET() {
  try {
    const orders = await prisma.order.findMany({
      orderBy: {
        id: 'asc'
      }
    });
    return NextResponse.json(orders);
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json({ error: '데이터를 가져오는 중 오류가 발생했습니다.' }, { status: 500 })
  }
} 