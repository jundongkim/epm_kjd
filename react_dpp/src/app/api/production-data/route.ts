import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DATA_FILE_PATH = path.join(process.cwd(), 'src/data/dpp_data.json');

export async function GET() {
  try {
    const fileContents = fs.readFileSync(DATA_FILE_PATH, 'utf8');
    const data = JSON.parse(fileContents);
    return NextResponse.json(data.productionInfo);
  } catch (error) {
    console.error('Error reading production data:', error);
    return NextResponse.json({ error: 'Failed to read production data' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const updatedProductionInfo = await request.json();
    
    // 기존 데이터 읽기
    const fileContents = fs.readFileSync(DATA_FILE_PATH, 'utf8');
    const data = JSON.parse(fileContents);
    
    // productionInfo 업데이트
    data.productionInfo = updatedProductionInfo;
    
    // 파일에 저장
    fs.writeFileSync(DATA_FILE_PATH, JSON.stringify(data, null, 2), 'utf8');
    
    return NextResponse.json({ success: true, message: 'Production data saved successfully' });
  } catch (error) {
    console.error('Error saving production data:', error);
    return NextResponse.json({ error: 'Failed to save production data' }, { status: 500 });
  }
} 