#!/bin/bash

echo "🚀 DX-AI Manufacturing Copilot 시스템 시작 중..."
echo "======================================="

# 1. n8n 시작
echo "📋 n8n 워크플로우 시작..."
cd n8n && docker compose up -d && cd ..
if [ $? -eq 0 ]; then
    echo "✅ n8n 시작 완료"
else
    echo "❌ n8n 시작 실패"
fi

echo ""

# 2. Dify 시작
echo "🤖 Dify AI Platform 시작..."
cd dify/docker && docker compose -p dify up -d && cd ../..
if [ $? -eq 0 ]; then
    echo "✅ Dify 시작 완료"
else
    echo "❌ Dify 시작 실패"
fi

echo ""
echo "======================================="
echo "✅ Docker 서비스 시작 완료!"
echo ""
echo "📋 서비스 접속 정보:"
echo "- n8n 워크플로우: http://localhost:5678"
echo "- Dify Console: http://localhost"
echo "- Dify API: http://localhost/console/api"
echo ""
echo "🖥️ 추가 실행 필요 (별도 터미널):"
echo "- Backend: cd backend && python main.py"
echo "- Frontend: cd frontend && npm run dev"
echo ""
echo "📊 서비스 상태 확인:"
echo "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(dx-ai-n8n|dify-)'" 