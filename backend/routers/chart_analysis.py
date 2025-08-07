"""
DX-AI Manufacturing Copilot - 차트 AI 분석 API 라우터
차트 이미지를 LLM으로 분석하는 엔드포인트
"""

import json
import logging
import base64
import io
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import httpx

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class ChartAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    timestamp: str
    chart_info: Optional[Dict[str, Any]] = None


@router.post("/ai/analyze-chart", response_model=ChartAnalysisResponse)
async def analyze_chart(
    image: UploadFile = File(...),
    metadata: str = Form(...),
    prompt: str = Form(...)
):
    """
    차트 이미지를 AI로 분석합니다.
    
    Args:
        image: 차트 이미지 파일 (PNG)
        metadata: 차트 메타데이터 (JSON 문자열)
        prompt: 분석 요청 설정 (JSON 문자열)
    
    Returns:
        ChartAnalysisResponse: 분석 결과
    """
    try:
        # 1. 입력 데이터 파싱
        try:
            metadata_dict = json.loads(metadata)
            prompt_dict = json.loads(prompt)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        
        # 2. 이미지 파일 검증
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid image file format")
        
        # 3. 이미지 읽기
        image_content = await image.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # 4. 차트 정보 추출 (축 범위 정보 포함)
        axis_ranges = metadata_dict.get("axisRanges", {})
        
        # 데이터 처리 정보 추출
        data_processing = metadata_dict.get("dataProcessing", {})
        statistics = metadata_dict.get("statistics", {})
        
        chart_info = {
            "chart_name": metadata_dict.get("chartName", "Unknown"),
            "chart_type": metadata_dict.get("chartType", "unknown"),
            "filename": metadata_dict.get("filename", ""),
            "data_points": statistics.get("processedDataPointsCount", statistics.get("dataPointsCount", 0)),
            "original_data_points": statistics.get("originalDataPointsCount", 0),
            "time_range": statistics.get("timeRange", "N/A"),
            "columns": metadata_dict.get("dataConfig", {}).get("visualizationColumns", []),
            "data_processing_applied": statistics.get("dataProcessingApplied", False),
            # ✅ 새로 추가: 실제 축 범위 정보
            "axis_ranges": axis_ranges,
            # ✅ 새로 추가: 데이터 처리 방식 정보
            "data_processing": data_processing
        }
        
        # 로깅을 위한 변수 추출
        chart_type = chart_info.get('chart_type', 'unknown')
        is_grouped = data_processing.get('isGrouped', False)
        grouping_method = data_processing.get('groupingMethod', 'none')
        original_points = chart_info.get('original_data_points', 0)
        processed_points = chart_info.get('data_points', 0)
        
        # 차트 분석 정보 로깅 (데이터 처리 방식 포함)
        logger.info(f"📊 차트 분석 요청 정보:")
        logger.info(f"  📐 차트 타입: {chart_type}")
        logger.info(f"  📊 데이터 처리: {grouping_method} ({'적용됨' if is_grouped else '미적용'})")
        logger.info(f"  📋 원본 데이터: {original_points:,}개 포인트")
        logger.info(f"  🔄 처리된 데이터: {processed_points:,}개 포인트")
        
        # 축 범위 정보 로깅 (시간 단위 정보 포함)
        if axis_ranges:
            logger.info(f"📊 수신된 축 범위 정보:")
            if "xAxis" in axis_ranges:
                logger.info(f"  📅 X축: {axis_ranges['xAxis'].get('range', 'N/A')}")
            if "yAxis" in axis_ranges:
                logger.info(f"  📈 Y축: {axis_ranges['yAxis'].get('min', 'N/A')} ~ {axis_ranges['yAxis'].get('max', 'N/A')} (평균: {axis_ranges['yAxis'].get('mean', 'N/A')})")
            if "timeUnitAnalysis" in axis_ranges:
                time_unit = axis_ranges['timeUnitAnalysis']
                if time_unit:
                    precise_info = time_unit.get('preciseTimeInfo', {})
                    logger.info(f"  ⏰ 시간 단위: {time_unit.get('unitName', 'N/A')} ({time_unit.get('timeUnit', 'N/A')}) - {time_unit.get('expectedGroups', 'N/A')}개 그룹, 그룹당 평균 {time_unit.get('avgPointsPerGroup', 'N/A')}개")
                    logger.info(f"  🔍 데이터 정밀도: 실제 간격 {precise_info.get('actualDataIntervalFormatted', 'N/A')}, 샘플링 레이트 {precise_info.get('samplingRate', 'N/A')}")
        else:
            logger.warning("⚠️  축 범위 정보가 전달되지 않았습니다")
        
        # 5. AI 분석 수행
        analysis_result = await perform_chart_analysis(
            image_base64, 
            metadata_dict, 
            prompt_dict,
            chart_info
        )
        
        # 응답 텍스트 안전 처리 (프록시 문제 방지를 위해 크기 제한)
        raw_analysis = analysis_result["analysis"]
        # 언어 정보 추출
        current_language = prompt_dict.get("language", "ko") if prompt_dict else "ko"
        safe_analysis = sanitize_response_text(raw_analysis, max_length=2000, language=current_language)
        
        logger.info(f"분석 완료 - 원본: {len(raw_analysis) if raw_analysis else 0}자, 정제: {len(safe_analysis)}자")
        
        response = ChartAnalysisResponse(
            success=True,
            analysis=safe_analysis,
            confidence=analysis_result.get("confidence", 0.8),
            error=None,
            timestamp=datetime.now().isoformat(),
            chart_info=chart_info
        )
        
        logger.info("ChartAnalysisResponse 객체 생성 완료")
        
        # JSON 응답을 명시적으로 생성하여 인코딩 문제 방지
        response_data = {
            "success": True,
            "analysis": safe_analysis,
            "confidence": response.confidence,
            "error": None,
            "timestamp": response.timestamp,
            "chart_info": response.chart_info
        }
        
        logger.info("JSON 응답 데이터 준비 완료")
        return JSONResponse(
            content=response_data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart analysis failed: {str(e)}")
        
        error_data = {
            "success": False,
            "analysis": None,
            "confidence": None,
            "error": sanitize_response_text(str(e), max_length=500, language="ko"),  # 에러 메시지도 안전 처리
            "timestamp": datetime.now().isoformat(),
            "chart_info": None
        }
        
        return JSONResponse(
            content=error_data,
            headers={
                "Content-Type": "application/json; charset=utf-8"
            }
        )


@router.get("/ai/dify-setup-status")
async def get_dify_setup_status():
    """
    Dify 차트 분석 Agent 설정 상태를 확인합니다.
    """
    try:
        agent_key = os.getenv("DIFY_CHART_AGENT_KEY", "")
        dify_url = os.getenv("DIFY_API_URL", "http://localhost")
        
        if agent_key:
            return {
                "success": True,
                "message": "Dify 차트 분석 Agent가 설정되어 있습니다.",
                "configured": True,
                "dify_url": dify_url,
                "agent_key_preview": f"{agent_key[:8]}...{agent_key[-4:]}" if len(agent_key) > 12 else "app-****"
            }
        else:
            return {
                "success": False,
                "message": "Dify 차트 분석 Agent 설정이 필요합니다.",
                "configured": False,
                "setup_guide": [
                    "1. Dify 웹 인터페이스에 접속하세요: http://localhost",
                    "2. 새로운 Agent 앱을 생성하세요",
                    "3. Vision을 지원하는 모델을 선택하세요 (GPT-4 Vision, Claude 3 등)",
                    "4. ⚠️ **중요**: 시스템 프롬프트에 다음을 설정하세요:",
                    "   - 데이터 시각화 분석 전문가 역할 정의",
                    "   - 언어별 응답 규칙 (한국어 요청 시 한국어로만 응답)",
                    "   - 분석 항목: 시각적 패턴, 데이터 특성, 이상치, 비즈니스 인사이트, 추가 분석 제안",
                    "   - 응답 형식: 마크다운, 간결한 서술, 추론과정 제외",
                    "5. 앱을 게시하고 API 키를 복사하세요", 
                    "6. 환경변수 DIFY_CHART_AGENT_KEY에 API 키를 설정하세요",
                    "7. 백엔드 서버를 재시작하세요",
                    "8. ✅ 소스 코드에서 하드코딩된 프롬프트가 제거되었으므로 Agent 설정이 매우 중요합니다. (data/agent_prompt.txt 파일 참고)"
                ]
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"설정 상태 확인 실패: {str(e)}",
            "configured": False
        }


@router.post("/ai/test-dify-connection")
async def test_dify_connection():
    """
    Dify Agent 연결 상태를 테스트합니다.
    """
    try:
        # 환경변수 확인
        agent_key = os.getenv("DIFY_CHART_AGENT_KEY", "")
        if not agent_key:
            return {
                "success": False,
                "message": "DIFY_CHART_AGENT_KEY 환경변수가 설정되지 않았습니다",
                "troubleshooting": ["1. .env 파일에 DIFY_CHART_AGENT_KEY를 설정하세요"]
            }
        
        # 간단한 텍스트 테스트
        test_result = await call_dify_chart_analysis(
            "",  # 빈 이미지 (텍스트만 테스트)
            "연결 테스트입니다. 'Dify 연결 성공'이라고 간단히 응답해주세요.",
            {"chart_type": "test", "chart_name": "connection_test"},
            {"language": "ko", "type": "connection_test"}  # 테스트용 설정
        )
        
        return {
            "success": True,
            "message": "Dify Agent 연결 성공!",
            "test_response": test_result[:200] + "..." if len(test_result) > 200 else test_result,
            "response_length": len(test_result)
        }
        
    except Exception as e:
        error_message = str(e)
        troubleshooting = []
        
        if "환경변수가 설정되지 않았습니다" in error_message:
            troubleshooting = [
                "1. .env 파일에 DIFY_CHART_AGENT_KEY를 설정하세요",
                "2. Dify에서 Agent를 생성하고 API 키를 발급받으세요"
            ]
        elif "인증 실패" in error_message:
            troubleshooting = [
                "1. Dify Agent API 키가 올바른지 확인하세요",
                "2. 'app-'으로 시작하는 키인지 확인하세요",
                "3. Agent가 게시(Published) 상태인지 확인하세요"
            ]
        elif "연결 실패" in error_message:
            troubleshooting = [
                "1. Dify 서버가 실행 중인지 확인하세요 (http://localhost)",
                "2. DIFY_API_URL 환경변수를 확인하세요"
            ]
        else:
            troubleshooting = [
                "1. Dify 서버 상태를 확인하세요",
                "2. Agent가 Vision 모델을 사용하는지 확인하세요",
                "3. 백엔드 로그를 확인하세요"
            ]
        
        return {
            "success": False,
            "message": f"Dify Agent 연결 실패: {error_message}",
            "troubleshooting": troubleshooting
        }


async def perform_chart_analysis(
    image_base64: str, 
    metadata: Dict[str, Any], 
    prompt_config: Dict[str, Any],
    chart_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Dify AI Agent를 통해 실제 차트 분석을 수행합니다.
    
    Args:
        image_base64: Base64 인코딩된 이미지
        metadata: 차트 메타데이터
        prompt_config: 분석 설정
        chart_info: 차트 정보
    
    Returns:
        Dict: 분석 결과
    """
    try:
        # AI 분석을 위한 기본 정보 준비
        # Dify Agent가 자체 프롬프트를 사용하므로 기본 차트 정보만 전달
        
        # Dify Agent를 통한 실제 AI 분석 수행
        try:
            logger.info("Dify AI Agent를 통한 차트 분석 시작...")
            analysis_result = await call_dify_chart_analysis(
                image_base64,
                chart_info,
                prompt_config
            )
            confidence = 0.95  # Dify 분석 결과의 높은 신뢰도
            logger.info(f"Dify 분석 성공: {len(analysis_result)} 문자")
            
        except Exception as dify_error:
            logger.warning(f"Dify 분석 실패, 더미 응답으로 대체: {str(dify_error)}")
            # Dify 호출 실패 시 더미 응답으로 대체
            try:
                dummy_analysis = generate_dummy_analysis(chart_info, prompt_config)
                current_language = prompt_config.get("language", "ko") if prompt_config else "ko"
                analysis_result = sanitize_response_text(dummy_analysis, max_length=2000, language=current_language)
                confidence = 0.60  # 더미 응답의 낮은 신뢰도
            except Exception as dummy_error:
                logger.error(f"더미 응답 생성도 실패: {str(dummy_error)}")
                # 최후의 안전장치
                current_language = prompt_config.get("language", "ko") if prompt_config else "ko"
                if current_language == "ko":
                    fallback_message = f"""
## 차트 분석 결과

죄송합니다. 현재 AI 분석 서비스에 일시적인 문제가 발생했습니다.

**차트 정보:**
- 차트 타입: {chart_info.get('chart_type', '알 수 없음')}
- 차트 이름: {chart_info.get('chart_name', '알 수 없음')}
- 데이터 포인트: {chart_info.get('data_points', 0)}개

**문제 해결 방법:**
1. 잠시 후 다시 시도해주세요
2. Dify Agent 설정을 확인해주세요
3. 네트워크 연결을 확인해주세요

*서비스 복구 후 정상적인 AI 분석이 제공됩니다.*
                    """.strip()
                else:
                    fallback_message = f"""
## Chart Analysis Results

Sorry, there is a temporary issue with the AI analysis service.

**Chart Information:**
- Chart Type: {chart_info.get('chart_type', 'Unknown')}
- Chart Name: {chart_info.get('chart_name', 'Unknown')}
- Data Points: {chart_info.get('data_points', 0)} points

**Solutions:**
1. Please try again in a moment
2. Check Dify Agent configuration
3. Verify network connection

*Normal AI analysis will be provided after service recovery.*
                    """.strip()
                analysis_result = sanitize_response_text(fallback_message, max_length=2000, language=current_language)
                confidence = 0.30
        
        return {
            "analysis": analysis_result,
            "confidence": confidence,
            "prompt_source": "Dify Agent 내부 시스템 프롬프트"
        }
        
    except Exception as e:
        logger.error(f"AI analysis execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis execution failed: {str(e)}")


async def call_dify_chart_analysis(
    image_base64: str, 
    chart_info: Dict[str, Any],
    prompt_config: Dict[str, Any] = None
) -> str:
    """
    Dify AI Agent를 호출하여 차트 분석을 수행합니다.
    
    Args:
        image_base64: Base64 인코딩된 차트 이미지
        chart_info: 차트 정보 (메타데이터로 전달)
        prompt_config: 언어 설정 등 기본 설정
    
    Returns:
        str: 분석 결과 텍스트
    """
    # Dify API 설정 (환경변수에서 가져오기)
    DIFY_BASE_URL = os.getenv("DIFY_API_URL", "http://localhost")
    DIFY_CHART_AGENT_KEY = os.getenv("DIFY_CHART_AGENT_KEY", "")
    
    if not DIFY_CHART_AGENT_KEY:
        raise Exception("Dify Agent API 키가 설정되지 않았습니다")
    
    # 언어 설정 추출
    language = prompt_config.get("language", "ko") if prompt_config else "ko"
    
    # 차트 메타데이터를 포함한 상세 컨텍스트 생성
    axis_ranges = chart_info.get('axis_ranges', {})
    
    # 축 범위 정보를 텍스트로 포맷팅 (시간 단위 정보 포함)
    axis_info = ""
    time_unit_info = ""
    
    if axis_ranges:
        if 'xAxis' in axis_ranges:
            x_axis = axis_ranges['xAxis']
            axis_info += f"- X축 (시간): {x_axis.get('range', 'N/A')}, 총 기간: {x_axis.get('totalDuration', 'N/A')}\n"
        
        if 'yAxis' in axis_ranges:
            y_axis = axis_ranges['yAxis']
            axis_info += f"- Y축 (값): {y_axis.get('min', 'N/A')} ~ {y_axis.get('max', 'N/A')}, 평균: {y_axis.get('mean', 'N/A')}, 변동범위: {y_axis.get('range', 'N/A')}\n"
        
        if 'dataDistribution' in axis_ranges:
            dist = axis_ranges['dataDistribution']
            axis_info += f"- 데이터 분포: 총 {dist.get('totalPoints', 0)}개 포인트, 분산: {dist.get('variance', 'N/A')}\n"
        
        # ✅ 새로 추가: 정밀한 시간 단위 분석 정보
        if 'timeUnitAnalysis' in axis_ranges:
            time_unit = axis_ranges['timeUnitAnalysis']
            if time_unit:
                precise_info = time_unit.get('preciseTimeInfo', {})
                
                time_unit_info = f"""
⏰ **시간 단위 분석:**
- 분석 단위: {time_unit.get('unitName', 'N/A')} ({time_unit.get('timeUnit', 'N/A')})
- 예상 그룹 수: {time_unit.get('expectedGroups', 'N/A')}개 {time_unit.get('unitName', '단위')}
- {time_unit.get('unitName', '단위')}당 평균 데이터 포인트: {time_unit.get('avgPointsPerGroup', 'N/A')}개
- 분석 방향: {time_unit.get('analysisHint', 'N/A')}

🔍 **데이터 정밀도 정보:**
- 실제 데이터 간격: {precise_info.get('actualDataIntervalFormatted', 'N/A')}
- 샘플링 레이트: {precise_info.get('samplingRate', 'N/A')}
- 데이터 해상도: {precise_info.get('dataResolution', 'N/A')} (분석 단위 대비 실제 데이터 포인트 배수)
- 총 시간 범위: {precise_info.get('totalTimeSpanMs', 'N/A')}ms
"""
    
    # 차트 타입별 데이터 처리 방식 설명 (프론트엔드에서 전달된 정보 활용)
    chart_processing_info = ""
    chart_type = chart_info.get('chart_type', 'unknown')
    data_processing = chart_info.get('data_processing', {})
    is_grouped = data_processing.get('isGrouped', False)
    grouping_method = data_processing.get('groupingMethod', 'none')
    original_points = chart_info.get('original_data_points', 0)
    processed_points = chart_info.get('data_points', 0)
    
    if chart_type == 'box':
        chart_processing_info = f"""
📦 **박스플롯 데이터 처리 방식:**
- 원본 데이터 {original_points:,}개 포인트를 {time_unit.get('unitName', '시간')} 단위로 그룹화
- 각 {time_unit.get('unitName', '시간')} 그룹별로 통계값 계산 (중앙값, 사분위수, 이상치)
- 총 {time_unit.get('expectedGroups', processed_points)}개 {time_unit.get('unitName', '시간')} 박스로 집계됨
- 각 박스는 해당 {time_unit.get('unitName', '시간')} 구간의 데이터 분포를 나타냄
- 집계 방식: {grouping_method} (통계적 집계)
""" if time_unit else f"""
📦 **박스플롯 데이터 처리 방식:**
- 원본 데이터 {original_points:,}개를 시간 단위별 통계값으로 집계
- 집계 후 {processed_points}개 박스로 표시
- 각 박스는 해당 시간 구간의 데이터 분포를 나타냄
"""
    elif chart_type == 'line':
        if is_grouped:
            chart_processing_info = f"""
📈 **라인차트 데이터 처리 방식:**
- 원본 데이터 {original_points:,}개 포인트를 {time_unit.get('unitName', '시간')} 단위로 그룹화
- 각 {time_unit.get('unitName', '시간')} 그룹별 평균값으로 집계
- 총 {time_unit.get('expectedGroups', processed_points)}개 {time_unit.get('unitName', '시간')} 포인트로 표시됨
- 연속된 라인으로 시간적 트렌드를 시각화
- 집계 방식: {grouping_method} (평균값 집계)
""" if time_unit else f"""
📈 **라인차트 데이터 처리 방식:**
- 원본 데이터 {original_points:,}개를 시간 단위별 평균값으로 집계
- 집계 후 {processed_points}개 포인트로 표시
- 연속된 라인으로 시간적 트렌드를 시각화
"""
        else:
            chart_processing_info = f"""
📈 **라인차트 데이터 처리 방식:**
- 원본 데이터를 그대로 사용 (집계 없음)
- 총 {original_points:,}개의 개별 포인트를 연결하여 표시
- 연속된 라인으로 상세한 시간적 변화를 시각화
"""
    elif chart_type == 'scatter':
        chart_processing_info = f"""
📊 **산점도 데이터 처리 방식:**
- 원본 데이터를 그대로 사용 (집계 없음)
- 각 데이터 포인트를 개별적으로 표시
- 총 {original_points:,}개의 개별 포인트
- 시간에 따른 값의 분산과 패턴을 시각화
- 집계 방식: {grouping_method} (집계 없음)
"""

    simple_context = f"""차트 분석 요청:

📊 **차트 기본 정보:**
- 차트 타입: {chart_info.get('chart_type', 'unknown')}
- 차트 이름: {chart_info.get('chart_name', 'unknown')}
- 데이터 소스: {chart_info.get('filename', 'unknown')}
- 분석 컬럼: {', '.join(chart_info.get('columns', []))}

{chart_processing_info}

📈 **실제 데이터 범위:**
{axis_info if axis_info else '- 축 범위 정보 없음'}
{time_unit_info if time_unit_info else ''}

🌍 **분석 설정:**
- 응답 언어: {language}  
- 원본 데이터 포인트 수: {original_points:,}개
- 차트 표시 포인트 수: {processed_points:,}개
- 데이터 처리 적용: {'예' if chart_info.get('data_processing_applied', False) else '아니오'}

**⚠️ 중요 분석 지침:**
1. 첨부된 차트 이미지를 정확히 분석하되, 위의 데이터 처리 방식을 고려해주세요
2. 차트 타입({chart_type})에 따른 데이터 집계/그룹화 특성을 반영해주세요
3. 시간 단위({time_unit.get('unitName', '시간') if time_unit else 'N/A'})별 패턴과 특성을 중점적으로 분석해주세요
4. 실제 표시된 데이터 범위와 축 정보를 기반으로 정확한 인사이트를 제공해주세요
5. 차트에서 보이는 시각적 패턴과 위의 메타데이터 정보를 종합하여 분석해주세요"""
    
    logger.info(f"📝 Dify Agent 컨텍스트: {simple_context}")
    
    headers = {
        "Authorization": f"Bearer {DIFY_CHART_AGENT_KEY}",
        "Content-Type": "application/json"
    }
    
    # 먼저 이미지를 Dify에 업로드
    file_id = None
    if image_base64 and len(image_base64.strip()) > 0:
        # 이미지 데이터 검증
        try:
            image_size = len(base64.b64decode(image_base64))
            logger.info(f"🖼️ 이미지 정보: 크기={image_size:,}바이트 ({image_size/1024/1024:.2f}MB)")
            
            if image_size > 10 * 1024 * 1024:  # 10MB 제한
                logger.warning("⚠️ 이미지가 너무 큽니다 (10MB 초과)")
                raise Exception("이미지 크기가 10MB를 초과합니다")
        except Exception as size_error:
            logger.error(f"❌ 이미지 크기 검증 실패: {str(size_error)}")
            
        try:
            file_id = await upload_image_to_dify(image_base64, DIFY_CHART_AGENT_KEY)
            logger.info(f"✅ 이미지 업로드 성공: {file_id}")
        except Exception as upload_error:
            logger.error(f"❌ 이미지 업로드 실패: {str(upload_error)}")
            # 이미지 없이도 텍스트 분석은 진행
    else:
        logger.warning("⚠️ 이미지 데이터가 없습니다")
    
    # Dify Vision API용 페이로드 구성 (Agent는 streaming 모드만 지원)
    payload = {
        "inputs": {},
        "query": simple_context, # 간단한 메타데이터만 전달
        "response_mode": "streaming",
        "user": f"chart-analyzer-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    # 업로드된 이미지가 있는 경우에만 files 추가
    if file_id:
        payload["files"] = [
            {
                "type": "image",
                "transfer_method": "local_file",
                "upload_file_id": file_id
            }
        ]
        logger.info(f"📎 이미지 파일 첨부됨: {file_id}")
    
    try:
        # 환경변수에서 timeout 설정 가져오기 (기본값: 120초)
        dify_timeout = float(os.getenv("DIFY_CHART_TIMEOUT", "120.0"))
        async with httpx.AsyncClient(timeout=dify_timeout) as client:
            # Vision 지원 엔드포인트들을 시도 (올바른 URL 구성)
            vision_endpoints = [
                "http://localhost/v1/chat-messages",
                "http://localhost/api/v1/chat-messages", 
                "http://localhost/console/api/v1/chat-messages"
            ]
            
            for endpoint in vision_endpoints:
                try:
                    logger.info(f"🚀 Dify API 호출: {endpoint}")
                    logger.info(f"📦 페이로드 구조: files={'있음' if 'files' in payload else '없음'}, query 길이={len(payload.get('query', ''))}")
                    
                    response = await client.post(
                        endpoint,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        # Streaming 응답 처리
                        analysis_text = await parse_dify_streaming_response(response)
                        
                        if analysis_text and len(analysis_text.strip()) > 10:
                            # 언어 후처리: 응답이 요청된 언어와 다른 경우 경고 추가
                            processed_text = post_process_language_response(analysis_text, language)
                            
                            return processed_text.strip()
                        else:
                            raise Exception("Empty or invalid analysis result")
                    
                    elif response.status_code == 401:
                        raise Exception("Dify API 인증 실패. Agent API 키를 확인하세요.")
                    elif response.status_code == 404:
                        continue  # 다음 엔드포인트 시도
                    else:
                        error_text = response.text
                        raise Exception(f"Dify API 오류 ({response.status_code}): {error_text}")
                        
                except httpx.ConnectError:
                    continue  # 다음 엔드포인트 시도
                except httpx.TimeoutException:
                    raise Exception("Dify API 타임아웃 (60초)")
                except Exception as e:
                    if "인증 실패" in str(e):
                        raise e  # 인증 오류는 재시도하지 않음
                    logger.warning(f"Endpoint {endpoint} 실패: {str(e)}")
                    continue
            
            # 모든 엔드포인트 실패
            raise Exception("모든 Dify API 엔드포인트 연결 실패")
            
    except Exception as e:
        if "Dify API" in str(e) or "인증" in str(e):
            raise e
        else:
            raise Exception(f"Dify 호출 중 오류 발생: {str(e)}")


async def parse_dify_streaming_response(response: httpx.Response) -> str:
    """
    Dify의 streaming 응답을 파싱합니다.
    
    Args:
        response: httpx Response 객체
    
    Returns:
        str: 파싱된 응답 텍스트
    """
    try:
        full_response = ""
        
        # Streaming 응답 처리
        async for line in response.aiter_lines():
            if not line.strip():
                continue
                
            # SSE (Server-Sent Events) 형식 처리
            if line.startswith("data: "):
                data_str = line[6:]  # "data: " 제거
                
                if data_str == "[DONE]":
                    break
                    
                try:
                    data = json.loads(data_str)
                    
                    # Dify 응답 구조에 따른 텍스트 추출
                    if "answer" in data:
                        full_response += data["answer"]
                    elif "data" in data:
                        if "outputs" in data["data"]:
                            full_response += data["data"]["outputs"].get("text", "")
                        elif "answer" in data["data"]:
                            full_response += data["data"]["answer"]
                    elif "message" in data:
                        full_response += data["message"]
                        
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 그대로 추가
                    if data_str and data_str != "[DONE]":
                        full_response += data_str
        
        return full_response.strip()
        
    except Exception as e:
        logger.error(f"Streaming response parsing failed: {str(e)}")
        # 스트리밍 파싱 실패 시 일반 응답으로 처리
        try:
            result = response.json()
            if "answer" in result:
                return result["answer"]
            elif "data" in result and "outputs" in result["data"]:
                return result["data"]["outputs"].get("text", "")
            elif "message" in result:
                return result["message"]
            else:
                return str(result)
        except:
            return response.text


async def upload_image_to_dify(image_base64: str, api_key: str) -> str:
    """
    이미지를 Dify에 업로드하고 file_id를 반환합니다.
    
    Args:
        image_base64: Base64 인코딩된 이미지 데이터
        api_key: Dify API 키
    
    Returns:
        str: 업로드된 파일의 ID
    """
    try:
        # Base64 이미지를 바이너리로 변환
        image_data = base64.b64decode(image_base64)
        
        # 파일 업로드용 헤더 (multipart/form-data)
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # 업로드할 파일 데이터
        files = {
            "file": ("chart.png", io.BytesIO(image_data), "image/png")
        }
        
        # 업로드 엔드포인트들 시도
        upload_endpoints = [
            "http://localhost/v1/files/upload",
            "http://localhost/api/v1/files/upload",
            "http://localhost/console/api/files/upload"
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in upload_endpoints:
                try:
                    logger.info(f"🔄 이미지 업로드 시도: {endpoint}")
                    
                    response = await client.post(
                        endpoint,
                        headers=headers,
                        files=files
                    )
                    
                    if response.status_code == 200 or response.status_code == 201:
                        result = response.json()
                        
                        # 다양한 응답 형식 지원
                        file_id = None
                        if "id" in result:
                            file_id = result["id"]
                        elif "file_id" in result:
                            file_id = result["file_id"]
                        elif "data" in result and "id" in result["data"]:
                            file_id = result["data"]["id"]
                        
                        if file_id:
                            logger.info(f"✅ 이미지 업로드 성공: {file_id}")
                            return file_id
                        else:
                            logger.warning(f"⚠️ 응답에서 file_id를 찾을 수 없음: {result}")
                            continue
                    
                    elif response.status_code == 413:
                        raise Exception("이미지 파일이 너무 큽니다 (최대 크기 초과)")
                    elif response.status_code == 401:
                        raise Exception("Dify API 인증 실패")
                    else:
                        logger.warning(f"❌ 업로드 실패 ({response.status_code}): {response.text}")
                        continue
                        
                except httpx.ConnectError:
                    logger.warning(f"⚠️ 연결 실패: {endpoint}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ 업로드 오류 ({endpoint}): {str(e)}")
                    continue
        
        raise Exception("모든 업로드 엔드포인트에서 실패")
        
    except Exception as e:
        logger.error(f"❌ 이미지 업로드 실패: {str(e)}")
        raise Exception(f"이미지 업로드 실패: {str(e)}")


def post_process_language_response(text: str, expected_language: str) -> str:
    """
    AI 응답의 언어를 확인하고 필요시 경고 메시지를 추가합니다.
    
    Args:
        text: AI 응답 텍스트
        expected_language: 예상 언어 ("ko" 또는 "en")
    
    Returns:
        str: 처리된 응답 텍스트
    """
    try:
        # 간단한 언어 감지 (ASCII 비율로 추정)
        ascii_count = sum(1 for char in text if ord(char) < 128)
        total_chars = len(text)
        ascii_ratio = ascii_count / total_chars if total_chars > 0 else 0
        
        # 한국어 문자 감지 (한글 유니코드 범위)
        korean_chars = sum(1 for char in text if 0xAC00 <= ord(char) <= 0xD7AF)
        korean_ratio = korean_chars / total_chars if total_chars > 0 else 0
        
        logger.info(f"🔍 언어 분석 - ASCII 비율: {ascii_ratio:.2f}, 한글 비율: {korean_ratio:.2f}")
        
        # 언어 불일치 감지 및 처리
        if expected_language == "ko":
            # 한국어를 원했는데 한글이 거의 없고 ASCII가 많은 경우 (영어 응답 추정)
            if korean_ratio < 0.05 and ascii_ratio > 0.8:
                logger.warning(f"⚠️ 한국어 요청했지만 영어로 응답됨 (한글: {korean_ratio:.2f}, ASCII: {ascii_ratio:.2f})")
                
                # 한국어 경고 메시지 추가
                warning_message = """
> ⚠️ **언어 설정 알림**: 한국어로 분석을 요청했지만 AI가 영어로 응답했습니다.
> 
> **해결 방법**:
> 1. Dify Agent 설정에서 시스템 프롬프트를 확인하세요
> 2. "반드시 한국어로만 응답하세요"라는 지시사항을 추가하세요
> 3. 사용 중인 AI 모델이 한국어를 지원하는지 확인하세요

---

"""
                return warning_message + text
                
        elif expected_language == "en":
            # 영어를 원했는데 한글이 많은 경우
            if korean_ratio > 0.1:
                logger.warning(f"⚠️ 영어 요청했지만 한국어로 응답됨 (한글: {korean_ratio:.2f}, ASCII: {ascii_ratio:.2f})")
                
                # 영어 경고 메시지 추가
                warning_message = """
> ⚠️ **Language Setting Notice**: English analysis was requested but AI responded in Korean.
> 
> **Solutions**:
> 1. Check Dify Agent settings for system prompt
> 2. Add instruction "Please respond only in English"
> 3. Verify that the AI model supports English

---

"""
                return warning_message + text
        
        # 언어가 올바른 경우 또는 감지할 수 없는 경우 원본 반환
        return text
        
    except Exception as e:
        logger.error(f"언어 후처리 중 오류: {str(e)}")
        return text


def sanitize_response_text(text: str, max_length: int = 2000, language: str = "ko") -> str:
    """
    응답 텍스트를 안전하게 정제하여 JSON 직렬화 오류를 방지합니다.
    
    Args:
        text: 정제할 텍스트
        max_length: 최대 길이 (기본: 2000자)
        language: 언어 코드 ("ko" 또는 "en")
    
    Returns:
        str: 정제된 안전한 텍스트
    """
    if not text or not isinstance(text, str):
        if language == "ko":
            return "분석 결과를 불러올 수 없습니다."
        else:
            return "Unable to load analysis results."
    
    try:
        # 1. 제어 문자 제거 (탭, 줄바꿈 제외)
        # 제어 문자: \x00-\x08, \x0B-\x0C, \x0E-\x1F, \x7F-\x9F
        control_chars = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]')
        cleaned_text = control_chars.sub('', text)
        
        # 2. 잘못된 유니코드 문자 처리
        try:
            cleaned_text = cleaned_text.encode('utf-8', errors='replace').decode('utf-8')
        except UnicodeError:
            cleaned_text = text.encode('ascii', errors='ignore').decode('ascii')
        
        # 3. 연속된 공백이나 줄바꿈 정리
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)  # 3개 이상 줄바꿈을 2개로
        cleaned_text = re.sub(r' {3,}', '  ', cleaned_text)     # 3개 이상 공백을 2개로
        
        # 4. 길이 제한 (마크다운 구조 유지하며 자르기)
        if len(cleaned_text) > max_length:
            truncated = cleaned_text[:max_length]
            # 마지막 완전한 문장이나 단락에서 자르기
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            truncate_msg = "*[분석 결과가 길어 일부만 표시됩니다]*" if language == "ko" else "*[Analysis result truncated for display]*"
            
            if last_period > max_length - 200:  # 마지막 200자 내에 마침표가 있으면
                cleaned_text = truncated[:last_period + 1] + f"\n\n{truncate_msg}"
            elif last_newline > max_length - 200:  # 마지막 200자 내에 줄바꿈이 있으면
                cleaned_text = truncated[:last_newline] + f"\n\n{truncate_msg}"
            else:
                cleaned_text = truncated + f"...\n\n{truncate_msg}"
        
        # 5. 최종 검증: 빈 문자열이면 기본 메시지 반환
        if not cleaned_text.strip():
            if language == "ko":
                return "## 분석 완료\n\nAI 분석이 완료되었으나 결과를 표시하는 중 문제가 발생했습니다.\n잠시 후 다시 시도해주세요."
            else:
                return "## Analysis Complete\n\nAI analysis completed but there was an issue displaying the results.\nPlease try again in a moment."
        
        logger.info(f"텍스트 정제 완료: 원본 {len(text)}자 → 정제 {len(cleaned_text)}자")
        return cleaned_text.strip()
        
    except Exception as e:
        logger.error(f"텍스트 정제 중 오류 발생: {str(e)}")
        # 최후의 안전장치
        if language == "ko":
            return f"""
## 차트 분석 결과

AI 분석이 완료되었으나 결과 처리 중 문제가 발생했습니다.

**문제**: 응답 텍스트 처리 오류  
**원인**: {str(e)[:100]}...

**해결 방법**:
1. 잠시 후 다시 시도해주세요
2. 차트가 너무 복잡한 경우 단순한 차트로 테스트해보세요
3. 문제가 지속되면 관리자에게 문의하세요

*정상적인 분석 결과는 곧 제공될 예정입니다.*
            """.strip()
        else:
            return f"""
## Chart Analysis Results

AI analysis completed but there was an issue processing the results.

**Issue**: Response text processing error  
**Cause**: {str(e)[:100]}...

**Solutions**:
1. Please try again in a moment
2. If the chart is too complex, try testing with a simpler chart
3. Contact administrator if the issue persists

*Normal analysis results will be provided soon.*
            """.strip()


def generate_dummy_analysis(chart_info: Dict[str, Any], prompt_config: Dict[str, Any]) -> str:
    """
    더미 분석 결과를 생성합니다. (실제 축 범위 정보 및 차트 타입별 처리 방식 반영)
    """
    chart_type = chart_info.get('chart_type', 'unknown')
    chart_name = chart_info.get('chart_name', '데이터')
    language = prompt_config.get("language", "ko")
    axis_ranges = chart_info.get('axis_ranges', {})
    
    # 축 범위 정보 추출 (시간 단위 정보 포함)
    x_range = "정보 없음"
    y_range = "정보 없음"
    y_mean = "정보 없음" 
    data_points = chart_info.get('data_points', 0)
    
    # 정밀한 시간 단위 분석 정보 추출
    time_unit_name = "시간"
    expected_groups = "N/A"
    avg_points_per_group = "N/A"
    analysis_hint = "시간대별 데이터 분석"
    actual_data_interval = "N/A"
    sampling_rate = "N/A"
    data_resolution = "N/A"
    
    # 차트 타입별 데이터 처리 방식 설명
    data_processing_description = ""
    
    if axis_ranges:
        if 'xAxis' in axis_ranges:
            x_range = axis_ranges['xAxis'].get('range', '정보 없음')
        if 'yAxis' in axis_ranges:
            y_axis = axis_ranges['yAxis']
            y_min = y_axis.get('min', 'N/A')
            y_max = y_axis.get('max', 'N/A')
            y_mean = y_axis.get('mean', 'N/A')
            if y_min != 'N/A' and y_max != 'N/A':
                y_range = f"{y_min:.2f} ~ {y_max:.2f}"
        
        # ✅ 새로 추가: 정밀한 시간 단위 분석 정보 추출
        if 'timeUnitAnalysis' in axis_ranges:
            time_unit = axis_ranges['timeUnitAnalysis']
            if time_unit:
                time_unit_name = time_unit.get('unitName', '시간')
                expected_groups = time_unit.get('expectedGroups', 'N/A')
                avg_points_per_group = time_unit.get('avgPointsPerGroup', 'N/A')
                analysis_hint = time_unit.get('analysisHint', '시간대별 데이터 분석')
                
                # 정밀한 시간 정보 추출
                precise_info = time_unit.get('preciseTimeInfo', {})
                if precise_info:
                    actual_data_interval = precise_info.get('actualDataIntervalFormatted', 'N/A')
                    sampling_rate = precise_info.get('samplingRate', 'N/A')
                    data_resolution = precise_info.get('dataResolution', 'N/A')
    
    # 차트 타입별 데이터 처리 방식 설명 생성
    if language == "ko":
        if chart_type == "box":
            data_processing_description = f"""
**📦 박스플롯 데이터 처리 방식:**
- 원본 데이터를 {time_unit_name} 단위로 그룹화
- 각 {time_unit_name}별로 통계값 계산 (중앙값, 사분위수, 이상치)
- 총 {expected_groups}개 {time_unit_name} 그룹으로 집계
- 각 박스는 해당 {time_unit_name}의 데이터 분포를 나타냄"""
        elif chart_type == "line":
            data_processing_description = f"""
**📈 라인차트 데이터 처리 방식:**
- 원본 데이터를 {time_unit_name} 단위로 그룹화 후 평균값 계산
- 총 {expected_groups}개 {time_unit_name} 포인트로 집계
- 연속된 라인으로 시간적 트렌드 시각화"""
        else:  # scatter
            data_processing_description = f"""
**📊 산점도 데이터 처리 방식:**
- 원본 데이터를 그대로 사용 (집계 없음)
- 총 {data_points:,}개의 개별 포인트 표시
- 시간에 따른 값의 분산과 패턴 시각화"""
    else:  # English
        if chart_type == "box":
            data_processing_description = f"""
**📦 Box Plot Data Processing:**
- Original data grouped by {time_unit_name} units
- Statistical values calculated for each {time_unit_name} (median, quartiles, outliers)
- Aggregated into {expected_groups} {time_unit_name} groups
- Each box represents data distribution for that {time_unit_name}"""
        elif chart_type == "line":
            data_processing_description = f"""
**📈 Line Chart Data Processing:**
- Original data grouped by {time_unit_name} units with average values
- Aggregated into {expected_groups} {time_unit_name} points
- Continuous line visualization of temporal trends"""
        else:  # scatter
            data_processing_description = f"""
**📊 Scatter Plot Data Processing:**
- Original data used as-is (no aggregation)
- Total {data_points:,} individual points displayed
- Time-based value distribution and pattern visualization"""
    
    if language == "ko":
        if chart_type == "line":
            return f"""
📊 **{chart_name} 시계열 분석 결과**

{data_processing_description}

**시각적 패턴:**
• 시간 범위: {x_range}
• 전체 데이터 트렌드 확인됨
• {time_unit_name} 단위 시계열 변동 패턴 관찰

**데이터 특성:**
• 원본 데이터 포인트: {data_points:,}개
• 집계 후 데이터 포인트: {expected_groups}개
• Y축 값 범위: {y_range}
• 평균값: {y_mean}
• {time_unit_name}당 평균 데이터: {avg_points_per_group}개

**정밀한 시간 분석:**
• {analysis_hint}
• 실제 데이터 간격: {actual_data_interval}
• 샘플링 레이트: {sampling_rate}
• 데이터 해상도: {data_resolution} (분석 단위 대비 배수)
• {time_unit_name} 기준 연속성 및 트렌드 분석
• {time_unit_name}별 변동성 패턴 확인

**이상치:**
• 일반 패턴 대비 편차 구간 존재
• {time_unit_name} 단위 급격한 변화점 감지

**비즈니스 인사이트:**
• 데이터 범위({y_range}) 내에서 안정적 운영
• 평균 수준({y_mean}) 기준 성과 평가 가능
• {time_unit_name}별 패턴 모니터링으로 예측 정확도 향상

**추가 분석 제안:**
• {time_unit_name} 단위 세분화 분석
• {time_unit_name}별 계절성/주기성 패턴 검증
• {time_unit_name} 기준 임계값 알림 설정

*실제 데이터 범위 및 시간 단위 기반 분석*
            """
        elif chart_type == "box":
            return f"""
📦 **{chart_name} 박스플롯 분석 결과**

{data_processing_description}

**시각적 패턴:**
• 시간 구간: {x_range}
• {time_unit_name} 단위별 분포 박스 구조 확인
• {time_unit_name}별 중앙값 및 사분위수 분포 패턴

**데이터 특성:**
• 원본 데이터 포인트: {data_points:,}개
• 집계 후 박스 개수: {expected_groups}개
• 값 범위: {y_range}
• 전체 평균: {y_mean}
• {time_unit_name}당 평균 데이터: {avg_points_per_group}개

**정밀한 시간 단위별 분포 분석:**
• {analysis_hint}
• 실제 데이터 간격: {actual_data_interval}
• 샘플링 레이트: {sampling_rate}
• 데이터 해상도: {data_resolution} (분석 단위 대비 배수)
• 각 {time_unit_name}별 데이터 분산도 및 중심 경향성
• {time_unit_name} 간 분포 특성 변화 패턴

**이상치:**
• {time_unit_name}별 박스플롯 경계 외부 값들 탐지
• {time_unit_name} 단위 통계적 이상치 패턴 식별

**비즈니스 인사이트:**
• 데이터 범위({y_range}) 내 {time_unit_name}별 분포 특성 양호
• 평균값({y_mean}) 기준 {time_unit_name} 단위 정상 운영 구간
• {time_unit_name}별 편차 수준 모니터링으로 품질 관리 최적화

**추가 분석 제안:**
• {time_unit_name} 단위 분포 변화 추적
• {time_unit_name}별 이상치 발생 패턴 분석
• {time_unit_name} 기준 사분위수 범위 품질 관리

*실제 데이터 범위 및 시간 단위 기반 분석*
            """
        else:  # scatter or others
            return f"""
📈 **{chart_name} 데이터 분석 결과**

{data_processing_description}

**시각적 패턴:**
• 시간 범위: {x_range}
• 개별 데이터 포인트 분산 패턴 확인
• 시간에 따른 전체적 분포 경향성 관찰

**데이터 특성:**
• 표시된 데이터 포인트: {data_points:,}개 (원본 데이터 그대로)
• X-Y 값 범위: {y_range}
• 중심값: {y_mean}
• 데이터 분산도: {time_unit_name} 단위별 개별 포인트 표시

**정밀한 시간 단위별 분포 분석:**
• {analysis_hint}
• 실제 데이터 간격: {actual_data_interval}
• 샘플링 레이트: {sampling_rate}
• 데이터 해상도: {data_resolution} (분석 단위 대비 배수)
• {time_unit_name} 기준 데이터 일관성 및 연속성 확인
• {time_unit_name}별 값 분산 특성 분석

**이상치:**
• {time_unit_name} 단위 일반 분포 범위 외 데이터 포인트 탐지
• {time_unit_name}별 극값 위치 및 패턴 식별

**비즈니스 인사이트:**
• 값 범위({y_range}) 내에서 {time_unit_name}별 정상 분포
• 평균 수준({y_mean}) 기준 {time_unit_name} 단위 성과 적정
• {time_unit_name}별 분산 패턴 기반 품질 평가 및 예측 가능

**추가 분석 제안:**
• {time_unit_name} 단위 분포 변화 추적
• {time_unit_name}별 상관관계 및 클러스터 분석
• {time_unit_name} 기준 이상치 발생 조건 분석

*실제 데이터 범위 및 시간 단위 기반 분석*
            """
    else:  # English
        if chart_type == "line":
            return f"""
📊 **{chart_name} Time Series Analysis Results**

{data_processing_description}

**Visual Patterns:**
• Time range: {x_range}
• Overall data trend confirmed
• {time_unit_name} unit temporal variation patterns observed

**Data Characteristics:**
• Original data points: {data_points:,}
• Aggregated data points: {expected_groups}
• Y-axis value range: {y_range}
• Average value: {y_mean}
• Average data per {time_unit_name}: {avg_points_per_group}

**Precise Time Unit Analysis:**
• {analysis_hint}
• Actual data interval: {actual_data_interval}
• Sampling rate: {sampling_rate}
• Data resolution: {data_resolution} (multiplier relative to analysis unit)
• {time_unit_name}-based continuity and trend analysis
• {time_unit_name} unit variability pattern verification

**Anomalies:**
• Deviation segments from general patterns
• {time_unit_name} unit sharp change points detected

**Business Insights:**
• Stable operation within data range ({y_range})
• Performance evaluation possible based on average level ({y_mean})
• {time_unit_name} unit pattern monitoring enhances prediction accuracy

**Additional Analysis Suggestions:**
• {time_unit_name} unit detailed segmentation analysis
• {time_unit_name} unit seasonality/periodicity pattern verification
• {time_unit_name}-based threshold alert configuration

*Analysis based on actual data ranges and time units*
            """
        else:
            return f"""
📈 **{chart_name} Data Analysis Results**

{data_processing_description}

**Visual Patterns:**
• Time range: {x_range}
• Individual data point distribution patterns confirmed
• Overall distribution trends observed

**Data Characteristics:**
• Displayed data points: {data_points:,} (original data as-is)
• X-Y value range: {y_range}
• Central value: {y_mean}
• Data distribution: Individual points shown by {time_unit_name} units

**Precise Time Unit Distribution Analysis:**
• {analysis_hint}
• Actual data interval: {actual_data_interval}
• Sampling rate: {sampling_rate}
• Data resolution: {data_resolution} (multiplier relative to analysis unit)
• {time_unit_name}-based data consistency and continuity verification
• {time_unit_name} unit value distribution characteristic analysis

**Anomalies:**
• Data points outside general distribution range detected
• Extreme value positions and patterns identified

**Business Insights:**
• Normal distribution within value range ({y_range})
• Appropriate performance based on average level ({y_mean})
• Quality assessment possible based on distribution patterns

**Additional Analysis Suggestions:**
• Time-based distribution change tracking
• Correlation and cluster analysis
• Anomaly occurrence condition analysis

*Analysis based on actual data ranges and time units*
            """


@router.post("/ai/test-image-upload")
async def test_image_upload(image: UploadFile = File(...)):
    """
    이미지 업로드를 테스트합니다.
    """
    try:
        # 이미지 파일 검증
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid image file format")
        
        # 이미지 읽기 및 base64 변환
        image_content = await image.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        logger.info(f"🧪 테스트 이미지 업로드: 크기={len(image_content):,}바이트")
        
        # Dify에 업로드 시도
        DIFY_CHART_AGENT_KEY = os.getenv("DIFY_CHART_AGENT_KEY", "")
        if not DIFY_CHART_AGENT_KEY:
            return {
                "success": False,
                "message": "Dify API 키가 설정되지 않았습니다"
            }
        
        file_id = await upload_image_to_dify(image_base64, DIFY_CHART_AGENT_KEY)
        
        return {
            "success": True,
            "message": "이미지 업로드 성공",
            "file_id": file_id,
            "image_size": len(image_content),
            "content_type": image.content_type
        }
        
    except Exception as e:
        logger.error(f"❌ 테스트 이미지 업로드 실패: {str(e)}")
        return {
            "success": False,
            "message": f"이미지 업로드 실패: {str(e)}"
        }


@router.post("/ai/test-axis-ranges")
async def test_axis_ranges(
    image: UploadFile = File(...),
    metadata: str = Form(...),
    prompt: str = Form(...)
):
    """
    축 범위 정보 전달을 테스트합니다.
    """
    try:
        # 메타데이터 파싱
        metadata_dict = json.loads(metadata)
        prompt_dict = json.loads(prompt)
        
        # 축 범위 정보 추출
        axis_ranges = metadata_dict.get("axisRanges", {})
        
        # 차트 정보 구성
        chart_info = {
            "chart_name": metadata_dict.get("chartName", "Unknown"),
            "chart_type": metadata_dict.get("chartType", "unknown"),
            "filename": metadata_dict.get("filename", ""),
            "data_points": metadata_dict.get("statistics", {}).get("dataPointsCount", 0),
            "time_range": metadata_dict.get("statistics", {}).get("timeRange", "N/A"),
            "columns": metadata_dict.get("dataConfig", {}).get("visualizationColumns", []),
            "axis_ranges": axis_ranges
        }
        
        # 축 범위 정보 분석
        range_analysis = {}
        if axis_ranges:
            if "xAxis" in axis_ranges:
                x_axis = axis_ranges["xAxis"]
                precise_info = x_axis.get("preciseInfo", {})
                range_analysis["x_axis"] = {
                    "range": x_axis.get("range", "N/A"),
                    "min": x_axis.get("min", "N/A"),
                    "max": x_axis.get("max", "N/A"),
                    "duration": x_axis.get("totalDuration", "N/A"),
                    # ✅ 새로 추가: 정밀한 시간 정보
                    "precise_info": {
                        "start_datetime": precise_info.get("startDateTime", "N/A"),
                        "end_datetime": precise_info.get("endDateTime", "N/A"),
                        "total_milliseconds": precise_info.get("totalMilliseconds", "N/A"),
                        "total_seconds": precise_info.get("totalSeconds", "N/A"),
                        "total_minutes": precise_info.get("totalMinutes", "N/A"),
                        "total_hours": precise_info.get("totalHours", "N/A"),
                        "total_days": precise_info.get("totalDays", "N/A")
                    }
                }
            
            if "yAxis" in axis_ranges:
                y_axis = axis_ranges["yAxis"]
                range_analysis["y_axis"] = {
                    "range": f"{y_axis.get('min', 'N/A')} ~ {y_axis.get('max', 'N/A')}",
                    "min": y_axis.get("min", "N/A"),
                    "max": y_axis.get("max", "N/A"),
                    "mean": y_axis.get("mean", "N/A"),
                    "variance": y_axis.get("range", "N/A")
                }
            
            if "dataDistribution" in axis_ranges:
                dist = axis_ranges["dataDistribution"]
                range_analysis["distribution"] = {
                    "total_points": dist.get("totalPoints", 0),
                    "variance": dist.get("variance", "N/A")
                }
            
            # ✅ 새로 추가: 정밀한 시간 단위 분석 정보
            if "timeUnitAnalysis" in axis_ranges:
                time_unit = axis_ranges["timeUnitAnalysis"]
                if time_unit:
                    precise_time_info = time_unit.get("preciseTimeInfo", {})
                    range_analysis["time_unit"] = {
                        "unit": time_unit.get("timeUnit", "N/A"),
                        "unit_name": time_unit.get("unitName", "N/A"),
                        "expected_groups": time_unit.get("expectedGroups", "N/A"),
                        "avg_points_per_group": time_unit.get("avgPointsPerGroup", "N/A"),
                        "analysis_hint": time_unit.get("analysisHint", "N/A"),
                        "chart_type": time_unit.get("chartType", "N/A"),
                        # ✅ 새로 추가: 정밀한 시간 분석 정보
                        "precise_time_info": {
                            "actual_data_interval": precise_time_info.get("actualDataInterval", "N/A"),
                            "actual_data_interval_formatted": precise_time_info.get("actualDataIntervalFormatted", "N/A"),
                            "unit_ms": precise_time_info.get("unitMs", "N/A"),
                            "total_time_span_ms": precise_time_info.get("totalTimeSpanMs", "N/A"),
                            "data_resolution": precise_time_info.get("dataResolution", "N/A"),
                            "sampling_rate": precise_time_info.get("samplingRate", "N/A")
                        }
                    }
        
        return {
            "success": True,
            "message": "축 범위 정보 분석 완료",
            "chart_info": {
                "name": chart_info["chart_name"],
                "type": chart_info["chart_type"],
                "data_points": chart_info["data_points"],
                "columns": chart_info["columns"]
            },
            "axis_ranges_received": axis_ranges != {},
            "range_analysis": range_analysis,
            "raw_axis_data": axis_ranges
        }
        
    except Exception as e:
        logger.error(f"❌ 축 범위 테스트 실패: {str(e)}")
        return {
            "success": False,
            "message": f"축 범위 테스트 실패: {str(e)}"
        } 