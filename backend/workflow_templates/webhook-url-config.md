# Teams Webhook URL 설정 가이드

## 1. 환경변수 설정 (권장)

### `.env` 파일에 저장
```bash
# .env 파일
TEAMS_WEBHOOK_URL=https://contoso.webhook.office.com/webhookb2/YOUR_ACTUAL_WEBHOOK_KEY
TEAMS_WEBHOOK_NG_MOISTURE=https://contoso.webhook.office.com/webhookb2/YOUR_NG_MOISTURE_KEY
```

### n8n 환경변수 설정
```bash
# n8n 컨테이너 환경변수
docker run -e TEAMS_WEBHOOK_URL="YOUR_URL_HERE" n8nio/n8n
```

## 2. 워크플로우에서 환경변수 사용

### 기존 워크플로우 수정
```json
{
  "parameters": {
    "method": "POST",
    "url": "={{$env.TEAMS_WEBHOOK_URL}}",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Content-Type", 
          "value": "application/json"
        }
      ]
    }
  }
}
```

## 3. 직접 URL 입력 방법

### ng-moisture-context.json 파일 수정
1. 파일 열기: `backend/workflow_templates/ng-moisture-context.json`
2. 203번째 줄 근처에서 찾기: `"url": "YOUR_TEAMS_WEBHOOK_URL_HERE"`
3. 교체: `"url": "https://your-actual-webhook-url"`

### teams-webhook-test.json 파일 수정
1. 파일 열기: `backend/workflow_templates/teams-webhook-test.json`
2. 동일하게 URL 교체

## 4. 테스트 방법

### cURL로 직접 테스트
```bash
curl -X POST "https://your-webhook-url" \
  -H "Content-Type: application/json" \
  -d '{
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions", 
    "summary": "테스트 메시지",
    "title": "🧪 Teams 연동 테스트",
    "text": "Teams Webhook이 정상적으로 작동합니다!"
  }'
```

### 예상 응답
```
성공시: HTTP 200 OK, "1" 
실패시: HTTP 400/404 등 에러 코드
```

## 5. 보안 모범 사례

### URL 보호 방법
- ✅ 환경변수 사용
- ✅ .gitignore에 .env 추가
- ✅ 접근 권한 제한
- ✅ 정기적 URL 재생성

### 모니터링
```bash
# 웹훅 호출 로그 확인
docker logs n8n-container | grep "teams"
```

## 6. 문제해결

### 자주 발생하는 오류
1. **400 Bad Request**: JSON 형식 오류
2. **404 Not Found**: URL 오류 또는 만료
3. **429 Too Many Requests**: 너무 많은 요청

### 해결책
```bash
# JSON 유효성 검사
echo '{"test": "message"}' | jq .

# URL 유효성 테스트  
curl -I "YOUR_WEBHOOK_URL"
``` 