import streamlit as st
import os
import time
import re
import calendar
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from PIL import Image
import io
import base64
from langchain_community.llms import Ollama
from langchain_ollama import ChatOllama
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import logging
import plotly.express as px
import plotly.graph_objects as go
from components.process.process_images import get_all_image_paths
from components.process.process_data_loader import find_image_file

# 유틸리티 함수
def create_download_link(content, filename, link_text):
    """마크다운 또는 HTML 콘텐츠를 다운로드할 수 있는 링크 생성"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def save_markdown_report(markdown_content, report_type, period):
    """마크다운 리포트를 파일로 저장합니다."""
    try:
        # 작업 디렉토리와 저장 경로 설정
        workspace_root = os.getcwd()
        save_dir = os.path.join(workspace_root, "PROCESS", "reports")
        os.makedirs(save_dir, exist_ok=True)

        # 현재 타임스탬프
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 파일명 설정
        report_filename = f"{report_type}_report_{period}_{timestamp}.md"
        report_path = os.path.join(save_dir, report_filename)

        # 리포트 헤더 추가
        report_header = f"""# {report_type.capitalize()} 공정관리 보고서: {period}
생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
        report_content = report_header + markdown_content

        # 파일 저장
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        logging.info(f"Report successfully saved to: {report_path}")
        return report_path, report_content

    except Exception as e:
        logging.error(f"리포트 저장 중 오류: {str(e)}")
        return None, None

def transform_process_data(data):
    """
    Transform nested PDF parsed data into flat process records.
    Takes a nested dictionary structure from PDF parsing and extracts process data.
    """
    try:
        records = []
        
        # Default date - use extraction date from metadata if available
        default_date = datetime.now()
        if isinstance(data, dict) and "metadata" in data and "extraction_date" in data["metadata"]:
            try:
                default_date = datetime.strptime(data["metadata"]["extraction_date"], "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # Process the parsed_data sections
        if isinstance(data, dict) and "parsed_data" in data:
            for key, section in data["parsed_data"].items():
                # Parse the section key to extract information
                parts = key.split(" - ")
                if len(parts) >= 2:
                    # Extract process name
                    process_name = parts[1] if len(parts) > 1 else ""
                    
                    # Extract text content and split into lines
                    text = section.get("text", "")
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    
                    # First line is often equipment name
                    equipment_name = lines[0] if lines else ""
                    
                    # Determine equipment type (if available)
                    equipment_type = ""
                    if "CAM5" in process_name:
                        equipment_type = "CAM5"
                    elif "CAM5N" in process_name:
                        equipment_type = "CAM5N"
                    
                    # Extract work details (remaining lines)
                    work_details = "\n".join(lines[1:]) if len(lines) > 1 else ""
                    
                    # Determine work type
                    work_type = "변경점" if "변경점" in key else "품질"
                    if "비고" in key:
                        work_type = "품질특이사항"
                    
                    # Create record - use both standard field names and Korean field names
                    record = {
                        "process_name": process_name,
                        "equipment_name": equipment_name,
                        "equipment_type": equipment_type,
                        "work_date": default_date,
                        "work_type": work_type,
                        "work_details": work_details,
                        # Korean field names for compatibility
                        "공정명": process_name,
                        "설비번호": equipment_name,
                        "설비유형": equipment_type,
                        "작업 일자": default_date,
                        "작업 종류": work_type,
                        "작업 상세내용": work_details
                    }
                    records.append(record)
        
        # If we have images, also process image descriptions
        if isinstance(data, dict) and "image_descriptions" in data and records:
            for img_file, description in data["image_descriptions"].items():
                # Add image descriptions to records
                for record in records:
                    if "image_description" not in record:
                        record["image_description"] = description
                        break  # Just add to first record for now
        
        return pd.DataFrame(records)
    except Exception as e:
        logging.error(f"데이터 변환 중 오류: {str(e)}")
        return pd.DataFrame()

def get_report_data(df, year, month):
    """선택한 년월에 맞게 데이터를 필터링하고 요약 통계를 생성합니다."""
    try:
        # 데이터프레임 복사
        df = df.copy()
        
        # 빈 데이터 확인
        if df.empty:
            logging.warning(f"필터링할 데이터가 비어 있습니다. ({year}년 {month}월)")
            return pd.DataFrame(), {}
        
        # 필드명이 다를 경우에 대비한 필드 매핑
        field_mappings = {
            'process_name': '공정명',
            'equipment_name': '설비번호',
            'equipment_type': '설비유형',
            'work_date': '작업 일자',
            'work_type': '작업 종류',
            'work_details': '작업 상세내용',
            'manager': '담당자'
        }
        
        # 필드명 역매핑 (사용 데이터에 따라 적절한 열 이름 사용)
        for standard_field, possible_field in field_mappings.items():
            if standard_field not in df.columns and possible_field in df.columns:
                df[standard_field] = df[possible_field]
        
        # 작업 일자 변환 (문자열 -> datetime)
        date_field = 'work_date' if 'work_date' in df.columns else '작업 일자'
        if date_field in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[date_field]):
                df[date_field] = pd.to_datetime(df[date_field], errors='coerce')
                # 날짜 변환 후 NaT 값 확인
                if df[date_field].isna().all():
                    logging.warning(f"모든 날짜가 유효하지 않습니다. ({year}년 {month}월)")
                    return pd.DataFrame(), {}
        else:
            logging.warning("날짜 열(work_date)이 없어 필터링할 수 없습니다.")
            return pd.DataFrame(), {}
        
        # 시작일과 종료일 계산
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # 해당 년/월 데이터만 필터링
        filtered_data = df[
            (df[date_field].dt.date >= start_date) & 
            (df[date_field].dt.date <= end_date)
        ]
        
        # 필터링 결과 확인
        if filtered_data.empty:
            logging.info(f"{year}년 {month}월 데이터가 없습니다.")
            return pd.DataFrame(), {}
        else:
            logging.info(f"{year}년 {month}월 데이터 {len(filtered_data)}건 필터링 완료")
        
        # 요약 통계 생성
        process_field = 'process_name' if 'process_name' in filtered_data.columns else '공정명'
        equipment_field = 'equipment_name' if 'equipment_name' in filtered_data.columns else '설비번호'
        equipment_type_field = 'equipment_type' if 'equipment_type' in filtered_data.columns else '설비유형'
        work_type_field = 'work_type' if 'work_type' in filtered_data.columns else '작업 종류'
        manager_field = 'manager' if 'manager' in filtered_data.columns else '담당자'
        
        summary_stats = {
            "기간": f"{start_date} ~ {end_date}",
            "total_work_count": len(filtered_data),
            "process_counts": filtered_data[process_field].value_counts().to_dict() if process_field in filtered_data.columns else {},
            "equipment_counts": filtered_data[equipment_field].value_counts().to_dict() if equipment_field in filtered_data.columns else {},
            "work_type_counts": filtered_data[work_type_field].value_counts().to_dict() if work_type_field in filtered_data.columns else {},
            "equipment_type_counts": filtered_data[equipment_type_field].value_counts().to_dict() if equipment_type_field in filtered_data.columns else {},
            "manager_counts": filtered_data[manager_field].value_counts().to_dict() if manager_field in filtered_data.columns else {}
        }
        
        # 일별 작업 건수
        if date_field in filtered_data.columns:
            daily_counts = filtered_data[date_field].dt.day.value_counts().sort_index().to_dict()
            summary_stats['daily_counts'] = daily_counts
        
        return filtered_data, summary_stats
        
    except Exception as e:
        logging.error(f"데이터 필터링 중 오류: {str(e)}")
        return pd.DataFrame(), {}

# Report generation class
class MonthlyReportGenerator:
    """월별 공정관리이력 보고서 생성 클래스"""
    def __init__(self, vector_store, selected_model="gemma3:4b", temperature=0.2):
        self.vector_store = vector_store
        self.selected_model = selected_model
        self.temperature = temperature
        
    def generate_report(self, year, month, message_placeholder, process_data):
        """특정 월의 보고서를 생성합니다."""
        try:
            # 데이터 변환 처리 (중첩 구조 등 다양한 데이터 형식 지원)
            transformed_data = None
            
            # process_data가 리스트이고 첫 항목이 딕셔너리일 경우 변환 시도
            if isinstance(process_data, list) and len(process_data) > 0 and isinstance(process_data[0], dict):
                # PDF 파싱 데이터와 같은 복잡한 형식인지 확인
                if any(("parsed_data" in item or "metadata" in item) for item in process_data[:5]):
                    logging.info("복잡한 중첩 데이터 구조 감지, 데이터 변환 시도...")
                    
                    # 각 항목을 변환하고 결합
                    transformed_dfs = []
                    for item in process_data:
                        item_df = transform_process_data(item)
                        if not item_df.empty:
                            transformed_dfs.append(item_df)
                    
                    if transformed_dfs:
                        transformed_data = pd.concat(transformed_dfs, ignore_index=True)
                        logging.info(f"데이터 변환 완료: {len(transformed_data)}개 레코드")
                    else:
                        logging.warning("변환된 데이터가 없습니다.")
                        # 기본 변환 시도
                        transformed_data = pd.DataFrame(process_data)
                else:
                    # 일반적인 딕셔너리 리스트인 경우 직접 DataFrame으로 변환
                    transformed_data = pd.DataFrame(process_data)
            elif isinstance(process_data, pd.DataFrame):
                # 이미 DataFrame인 경우 그대로 사용
                transformed_data = process_data
            else:
                # 기타 형식은 최대한 DataFrame으로 변환 시도
                try:
                    transformed_data = pd.DataFrame(process_data)
                except:
                    logging.error("지원되지 않는 데이터 형식")
                    message_placeholder.error("데이터 형식이 지원되지 않습니다.")
                    return None
            
            # 데이터 필터링 및 통계 생성 (개선된 방식 적용)
            filtered_data, stats = get_report_data(transformed_data, year, month)
            
            if filtered_data.empty:
                message_placeholder.error(f"{year}년 {month}월 데이터가 없습니다.")
                return None
            
            # 월간 주요 작업 요약
            work_summary = self._summarize_work_types(filtered_data)
            
            # 월간 데이터 컨텍스트 생성
            context = self._create_monthly_context(filtered_data, stats, work_summary)
            
            # 관련 이미지 찾기
            month_images = self._get_month_images(process_data, year, month)
            
            # 리포트 프롬프트 생성
            prompt = self._create_report_prompt(year, month, context)
            
            # 리포트 생성 (스트리밍)
            report_text = self._stream_report(prompt, message_placeholder)
            
            return {
                "text": report_text,
                "stats": stats,
                "data": filtered_data,
                "images": month_images
            }
            
        except Exception as e:
            import traceback
            logging.error(f"보고서 생성 중 오류: {str(e)}")
            logging.error(traceback.format_exc())
            message_placeholder.error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")
            return None
    
    def _summarize_work_types(self, month_data):
        """작업 유형 요약"""
        summary = []
        
        # 작업 유형 필드명 확인 (한글/영문 둘 다 지원)
        work_type_field = None
        work_details_field = None
        
        for field in ['work_type', '작업 종류']:
            if field in month_data.columns:
                work_type_field = field
                break
                
        for field in ['work_details', '작업 상세내용']:
            if field in month_data.columns:
                work_details_field = field
                break
        
        if work_type_field and work_details_field:
            # 작업 유형별로 데이터 그룹화
            grouped_data = month_data.groupby(work_type_field)
            
            for work_type, group in grouped_data:
                # 해당 작업 유형의 상위 3개 작업 내용 추출
                top_works = group[work_details_field].head(3).tolist()
                summary.append({
                    'work_type': work_type,
                    'count': len(group),
                    'examples': top_works
                })
        
        return summary
    
    def _create_monthly_context(self, month_data, stats, work_summary):
        """월간 보고서 컨텍스트 생성"""
        context_parts = []
        
        # 요약 통계
        summary_stats = f"### 월간 요약 통계\n"
        summary_stats += f"- 총 작업 건수: {stats['total_work_count']}건\n"
        
        if 'process_counts' in stats and stats['process_counts']:
            top_processes = sorted(stats['process_counts'].items(), key=lambda x: x[1], reverse=True)[:5]
            summary_stats += "- 주요 공정(상위 5개):\n"
            for proc, count in top_processes:
                proc_name = proc if pd.notna(proc) else "미지정"
                summary_stats += f"  - {proc_name}: {count}건\n"
        else:
            summary_stats += "- 주요 공정: 데이터 없음\n"
        
        if 'work_type_counts' in stats and stats['work_type_counts']:
            summary_stats += "- 작업 유형별 건수:\n"
            for work_type, count in stats['work_type_counts'].items():
                work_type_name = work_type if pd.notna(work_type) else "미지정"
                summary_stats += f"  - {work_type_name}: {count}건\n"
        else:
            summary_stats += "- 작업 유형: 데이터 없음\n"
        
        context_parts.append(summary_stats)
        
        # 작업 유형 요약
        if work_summary:
            work_type_summary = f"### 작업 유형 상세\n"
            for work_type_info in work_summary:
                work_type_name = work_type_info['work_type'] if pd.notna(work_type_info['work_type']) else "미지정"
                work_type_summary += f"- **{work_type_name}** ({work_type_info['count']}건)\n"
                work_type_summary += "  - 주요 작업 예시:\n"
                if work_type_info['examples']:
                    for example in work_type_info['examples']:
                        example_text = example if pd.notna(example) else "상세 내용 없음"
                        work_type_summary += f"    - {example_text}\n"
                else:
                    work_type_summary += "    - 예시 데이터 없음\n"
            
            context_parts.append(work_type_summary)
        
        # 주요 설비 작업
        if 'equipment_counts' in stats and stats['equipment_counts']:
            equipment_summary = f"### 주요 설비 작업\n"
            top_equipment = sorted(stats['equipment_counts'].items(), key=lambda x: x[1], reverse=True)[:5]
            
            for equipment, count in top_equipment:
                equipment_name = equipment if pd.notna(equipment) else "미지정"
                equipment_summary += f"- **{equipment_name}** ({count}건)\n"
                # 해당 설비의 대표 작업 내용
                if 'equipment_name' in month_data.columns and 'work_details' in month_data.columns:
                    equipment_works = month_data[month_data['equipment_name'] == equipment]['work_details'].head(2).tolist()
                    if equipment_works:
                        for work in equipment_works:
                            work_text = work if pd.notna(work) else "상세 내용 없음"
                            equipment_summary += f"  - {work_text}\n"
                    else:
                        equipment_summary += "  - 작업 상세 내용 없음\n"
            
            context_parts.append(equipment_summary)
        
        # 일별 작업 분포
        if 'daily_counts' in stats and stats['daily_counts']:
            daily_summary = f"### 일별 작업 분포\n"
            for day, count in sorted(stats['daily_counts'].items()):
                daily_summary += f"- {day}일: {count}건\n"
            
            context_parts.append(daily_summary)
        
        # 담당자별 작업
        if 'manager_counts' in stats and stats['manager_counts']:
            manager_summary = f"### 담당자별 작업\n"
            for manager, count in sorted(stats['manager_counts'].items(), key=lambda x: x[1], reverse=True):
                if pd.notna(manager) and manager != 'N/A':
                    manager_summary += f"- {manager}: {count}건\n"
            
            context_parts.append(manager_summary)
        
        # 컨텍스트 결합
        return "\n\n".join(context_parts)
    
    def _get_month_images(self, process_data, year, month):
        """해당 월의 관련 이미지 가져오기"""
        try:
            all_images = get_all_image_paths(process_data)
            month_images = []
            
            # 이미지 데이터가 없는 경우
            if not all_images:
                logging.info(f"{year}년 {month}월 관련 이미지 데이터가 없습니다.")
                return []
            
            # 해당 월의 이미지만 필터링
            for img in all_images:
                if 'work_date' in img and img['work_date']:
                    try:
                        img_date = pd.to_datetime(img['work_date'])
                        if img_date.year == year and img_date.month == month:
                            # 이미지 파일 존재 확인
                            if 'path' in img and os.path.exists(img['path']):
                                month_images.append(img)
                            else:
                                logging.warning(f"이미지 파일을 찾을 수 없습니다: {img.get('filename', 'unknown')}")
                    except Exception as e:
                        logging.warning(f"이미지 날짜 변환 오류: {str(e)}, 이미지: {img.get('filename', 'unknown')}")
            
            # 결과 로깅
            if month_images:
                logging.info(f"{year}년 {month}월 관련 이미지 {len(month_images)}개 필터링 완료")
            else:
                logging.info(f"{year}년 {month}월 관련 이미지가 없습니다.")
            
            # 최대 5개까지만 반환
            return month_images[:5]
        except Exception as e:
            logging.error(f"이미지 필터링 중 오류 발생: {str(e)}")
            return []
    
    def _create_report_prompt(self, year, month, context):
        """보고서 생성을 위한 프롬프트 생성"""
        month_name = calendar.month_name[month]
        
        system_prompt = f"""당신은 EcoPro BM의 공정관리이력 전문 분석가로서, {year}년 {month}월의 공정관리 데이터를 분석하여 종합적이고 상세한 월간 보고서를 작성해야 합니다.

아래 제공된 데이터를 바탕으로 논리적이고 통찰력 있는 월간 보고서를 작성하세요. 보고서는 경영진과 엔지니어링 팀 모두가 이해할 수 있도록 작성되어야 합니다.

### 보고서 작성 지침:
1. **보고서 제목**: "{year}년 {month}월 EcoPro BM 공정관리 월간 보고서"로 시작하세요.
2. **구조화된 형식**: 섹션과 하위 섹션을 사용하여 체계적으로 구성하세요.
3. **종합 요약**: 월간 주요 발견사항, 성과, 개선점, 도전과제를 요약하여 제시하세요.
4. **데이터 기반 인사이트**: 모든 분석은 데이터에 기반해야 하며, 핵심 수치와 비율을 포함하세요.
5. **기술적 분석**: 공정 및 설비별 주요 활동과 성과에 대한 기술적 평가를 제공하세요.
6. **트렌드 분석**: 이전 보고서의 맥락에서 데이터의 추세와 패턴을 분석하세요.
7. **함의와 권장사항**: 분석 결과에 따른 실행 가능한 제안과 다음 단계를 제공하세요.

### 보고서 필수 포함 섹션:
1. **개요 및 핵심 요약**
   - 월간 주요 성과 및 도전과제
   - 핵심 수치 대시보드
   
2. **공정별 상세 분석**
   - 각 주요 공정별 작업 내역 및 성과
   - 주목할만한 트렌드 및 이슈
   
3. **설비 관리 및 성능**
   - 주요 설비 상태 및 성능 분석
   - 설비 유지보수 및 개선 활동 요약
   
4. **개선 사항 및 기술 구현**
   - 구현된 개선 사항 및 그 효과
   - 새로운 기술 도입 및 적용 현황
   
5. **품질 관리 분석**
   - 품질 지표 성과
   - 품질 관련 이슈 및 해결책
   
6. **교차 기능 협업**
   - 부서간 협력 활동
   - 팀별 주요 기여
   
7. **향후 계획 및 권장사항**
   - 단기 및 중기 조치 사항
   - 장기적 개선 기회

보고서는 전체적인 맥락에서 개별 데이터 포인트의 의미를 설명하고, 그래프나 차트로 표현할 수 있는 수치 데이터를 시각적으로 설명하세요. 경영진이 중요한 정보를 신속하게 파악할 수 있도록 핵심 요약 정보를 제공하면서, 엔지니어링 팀에게는 기술적 세부 사항과 개선 기회를 제공하세요.

아래는 분석에 사용할 {year}년 {month}월 데이터입니다:

{context}
"""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt)
        ])
        
        return prompt
    
    def _stream_report(self, prompt, message_placeholder):
        """보고서 생성 및 스트리밍"""
        try:
            # 모델 초기화
            model_kwargs = {"temperature": self.temperature}
            if "max_tokens" in st.session_state and st.session_state.max_tokens:
                model_kwargs["max_tokens"] = st.session_state.max_tokens
            
            # Ollama 서버 URL 확인    
            base_url = st.session_state.get("ollama_base_url", "http://localhost:11434")
            logging.info(f"Ollama 서버에 연결 시도: {base_url}")
            
            try:
                llm = ChatOllama(
                    model=self.selected_model,
                    base_url=base_url,
                    **model_kwargs
                )
                logging.info(f"Ollama 모델 초기화 성공: {self.selected_model}")
            except Exception as model_error:
                error_msg = f"모델 초기화 오류: {str(model_error)}"
                logging.error(error_msg)
                message_placeholder.error(error_msg)
                
                # 대체 메시지 반환
                fallback_msg = f"""
                # 모델 연결 오류로 보고서를 생성할 수 없습니다.
                
                오류 내용: {str(model_error)}
                
                다음을 확인해주세요:
                1. Ollama 서버가 실행 중인지 확인 ({base_url})
                2. 선택한 모델({self.selected_model})이 사용 가능한지 확인
                3. 네트워크 연결 상태 확인
                """
                message_placeholder.warning(fallback_msg)
                return fallback_msg
            
            # 체인 구성
            chain = prompt | llm | StrOutputParser()
            
            # 스트리밍 응답 처리
            full_response = ""
            
            try:
                for chunk in chain.stream({}):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)  # 자연스러운 타이핑 효과
                
                # 최종 응답 표시
                message_placeholder.markdown(full_response)
                logging.info("보고서 생성 완료")
                
                return full_response
            except Exception as stream_error:
                error_msg = f"스트리밍 처리 중 오류: {str(stream_error)}"
                logging.error(error_msg)
                
                # 일부라도 생성된 내용이 있으면 표시
                if full_response:
                    message_placeholder.warning("보고서 생성 중 오류가 발생했으나, 일부 내용을 표시합니다.")
                    message_placeholder.markdown(full_response)
                    return full_response
                else:
                    message_placeholder.error(error_msg)
                    return None
                
        except Exception as e:
            import traceback
            error_msg = f"보고서 생성 중 오류: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            message_placeholder.error(error_msg)
            return None

# 보고서 시각화 관련 함수들
def create_work_type_chart(stats):
    """작업 유형 분포 차트 생성"""
    if 'work_type_counts' in stats and stats['work_type_counts']:
        work_types = list(stats['work_type_counts'].keys())
        counts = list(stats['work_type_counts'].values())
        
        fig = px.pie(
            names=work_types,
            values=counts,
            title="작업 유형별 분포",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
        
        return fig
    return None

def create_daily_trend_chart(stats):
    """일별 작업 추이 차트 생성"""
    if 'daily_counts' in stats and stats['daily_counts']:
        days = list(stats['daily_counts'].keys())
        counts = list(stats['daily_counts'].values())
        
        fig = px.line(
            x=days,
            y=counts,
            markers=True,
            title="일별 작업 건수",
            labels={'x': '일자', 'y': '작업 건수'}
        )
        fig.update_layout(margin=dict(t=50, b=50, l=50, r=20))
        fig.update_xaxes(tickmode='linear')
        fig.update_traces(line=dict(width=3))
        
        return fig
    return None

def create_process_chart(stats):
    """공정별 작업 분포 차트 생성"""
    if 'process_counts' in stats and stats['process_counts']:
        # 상위 10개 공정만 표시
        top_processes = sorted(stats['process_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        processes = [item[0] for item in top_processes]
        counts = [item[1] for item in top_processes]
        
        fig = px.bar(
            x=processes,
            y=counts,
            title="주요 공정별 작업 건수 (상위 10개)",
            labels={'x': '공정명', 'y': '작업 건수'},
            color=counts,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(margin=dict(t=50, b=100, l=50, r=20))
        fig.update_xaxes(tickangle=45)
        
        return fig
    return None

def create_equipment_chart(stats):
    """설비별 작업 분포 차트 생성"""
    if 'equipment_counts' in stats and stats['equipment_counts']:
        # 상위 10개 설비만 표시
        top_equipment = sorted(stats['equipment_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        equipment = [item[0] for item in top_equipment]
        counts = [item[1] for item in top_equipment]
        
        fig = px.bar(
            x=equipment,
            y=counts,
            title="주요 설비별 작업 건수 (상위 10개)",
            labels={'x': '설비명', 'y': '작업 건수'},
            color=counts,
            color_continuous_scale='Turbo'
        )
        fig.update_layout(margin=dict(t=50, b=100, l=50, r=20))
        fig.update_xaxes(tickangle=45)
        
        return fig
    return None

# 월별 보고서 인터페이스 표시 함수
def show_process_reports():
    """월별 공정관리이력 보고서 인터페이스를 표시합니다."""
    st.title("📊 월별 공정관리이력 보고서")
    
    # 로깅 설정
    logging.info("월별 공정관리이력 보고서 페이지 로드")
    
    # 공정관리이력 데이터 및 벡터 스토어 확인
    if "process_data" not in st.session_state:
        st.error("공정관리이력 데이터가 로드되지 않았습니다.")
        st.info("먼저 '공정관리이력 데이터 로드' 메뉴에서 데이터를 로드해주세요.")
        return
    
    if "process_vector_store" not in st.session_state:
        st.warning("벡터 저장소가 초기화되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
    
    # 데이터 유효성 확인
    process_data = st.session_state.process_data
    if not process_data:
        st.error("유효한 공정관리이력 데이터가 없습니다.")
        st.info("먼저 '공정관리이력 데이터 로드' 메뉴에서 올바른 데이터를 로드해주세요.")
        return
    
    # 데이터 구조 확인 및 정보 표시
    data_info = "데이터 형식: "
    if isinstance(process_data, list):
        data_count = len(process_data)
        data_info += f"리스트 ({data_count}개 항목)"
        if data_count > 0:
            data_info += f", 첫 항목 타입: {type(process_data[0]).__name__}"
            
            # 중첩 구조 감지
            if isinstance(process_data[0], dict) and any(key in process_data[0] for key in ["parsed_data", "metadata"]):
                data_info += " (중첩 구조 감지됨)"
                
    elif isinstance(process_data, pd.DataFrame):
        data_count = len(process_data.index)
        data_info += f"DataFrame ({data_count}행 x {len(process_data.columns)}열)"
    else:
        data_count = 1
        data_info += f"기타 ({type(process_data).__name__})"
    
    st.success(f"공정관리이력 데이터 {data_count}건이 로드되었습니다. {data_info}")
    
    # 보고서 설정 (메인 페이지에 표시)
    st.header("보고서 설정")
    
    # 년/월 선택 (2열 레이아웃)
    col1, col2 = st.columns(2)
    
    with col1:
        current_year = datetime.now().year
        year_options = list(range(current_year-2, current_year+1))
        selected_year = st.selectbox("년도 선택", options=year_options, index=len(year_options)-1)
    
    with col2:
        month_options = list(range(1, 13))
        current_month = datetime.now().month
        selected_month = st.selectbox("월 선택", options=month_options, index=current_month-1 if current_month <= 12 else 11)
    
    # 다운로드 옵션
    download_option = st.checkbox("보고서 자동 저장", value=True, help="생성된 보고서를 마크다운 파일로 저장합니다.")
    
    # 보고서 생성 버튼
    generate_report = st.button("보고서 생성", type="primary", help="선택한 설정으로 월간 보고서를 생성합니다.")
    
    # 사이드바 설정 (글로벌 설정만 표시)
    with st.sidebar:
        st.header("고급 설정")
        
        # 설정이 존재하지 않을 경우 기본값으로 초기화
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "gemma3:4b"
        if "temperature" not in st.session_state:
            st.session_state.temperature = 0.2
        
        # 현재 글로벌 설정 표시
        st.info(f"""
        **현재 모델 설정:**
        - 모델: {st.session_state.get('selected_model', 'gemma3:4b')}
        - Temperature: {st.session_state.get('temperature', 0.2)}
        
        *모델 설정을 변경하려면 메인 설정 페이지를 이용하세요.*
        """)
        
        # 고급 설정 (접힌 상태로) - 기본 URL 및 토큰 제한 설정
        with st.expander("고급 설정 재정의", expanded=False):
            st.warning("이 설정은 임시로 적용되며, 다음에 앱을 다시 로드하면 초기화됩니다.")
            
            # Ollama 서버 URL 설정
            ollama_url = st.text_input(
                "Ollama 서버 URL", 
                value=st.session_state.get("ollama_base_url", "http://localhost:11434"),
                help="Ollama 서버의 URL을 입력하세요. 기본값: http://localhost:11434"
            )
            st.session_state.ollama_base_url = ollama_url
            
            # 최대 토큰 수 설정
            max_tokens = st.number_input(
                "최대 토큰 수", 
                min_value=1000, 
                max_value=32000, 
                value=st.session_state.get("max_tokens", 4000),
                step=500,
                help="생성할 최대 토큰 수입니다. 보고서 길이에 영향을 줍니다."
            )
            st.session_state.max_tokens = max_tokens
    
    # 보고서 생성 처리
    if generate_report:
        # 글로벌 모델 설정 사용
        selected_model = st.session_state.get('selected_model', 'gemma3:4b')
        temperature = st.session_state.get('temperature', 0.2)
        
        # 보고서 생성 시작 로깅
        logging.info(f"{selected_year}년 {selected_month}월 보고서 생성 시작 (모델: {selected_model}, 온도: {temperature})")
        
        # 보고서 컨테이너 생성
        report_container = st.container()
        
        with report_container:
            st.header(f"{selected_year}년 {selected_month}월 공정관리 보고서")
            
            # 스피너와 메시지 플레이스홀더
            with st.spinner("보고서 생성 중..."):
                message_placeholder = st.empty()
                message_placeholder.info("보고서를 생성하고 있습니다. 잠시만 기다려주세요...")
                
                # 시작 시간 기록
                start_time = time.time()
                
                # 보고서 생성기 초기화
                report_generator = MonthlyReportGenerator(
                    st.session_state.get("process_vector_store", None),
                    selected_model=selected_model,
                    temperature=temperature
                )
                
                # 보고서 생성
                report_result = report_generator.generate_report(
                    selected_year, 
                    selected_month, 
                    message_placeholder,
                    st.session_state.process_data
                )
                
                # 소요 시간 계산
                elapsed_time = time.time() - start_time
                logging.info(f"보고서 생성 완료. 소요 시간: {elapsed_time:.2f}초")
                
                if report_result:
                    # 생성된 보고서 텍스트 저장
                    report_text = report_result.get("text", "")
                    
                    # 보고서 저장 (옵션)
                    if download_option and report_text:
                        report_path, report_content = save_markdown_report(
                            report_text,
                            "monthly",
                            f"{selected_year}-{selected_month}"
                        )
                        if report_path:
                            st.success(f"보고서가 저장되었습니다: {report_path}")
                            
                            # 다운로드 링크 생성
                            st.markdown(
                                create_download_link(
                                    report_content, 
                                    os.path.basename(report_path), 
                                    "📥 보고서 다운로드"
                                ), 
                                unsafe_allow_html=True
                            )
                    
                    # 차트 섹션
                    st.subheader("📈 주요 지표 시각화")
                    
                    # 2x2 그리드 레이아웃으로 차트 배치
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 작업 유형 분포 차트
                        work_type_chart = create_work_type_chart(report_result['stats'])
                        if work_type_chart:
                            st.plotly_chart(work_type_chart, use_container_width=True)
                        else:
                            st.info("작업 유형 데이터가 충분하지 않아 차트를 생성할 수 없습니다.")
                        
                        # 공정별 작업 분포 차트
                        process_chart = create_process_chart(report_result['stats'])
                        if process_chart:
                            st.plotly_chart(process_chart, use_container_width=True)
                        else:
                            st.info("공정 데이터가 충분하지 않아 차트를 생성할 수 없습니다.")
                    
                    with col2:
                        # 일별 작업 추이 차트
                        daily_chart = create_daily_trend_chart(report_result['stats'])
                        if daily_chart:
                            st.plotly_chart(daily_chart, use_container_width=True)
                        else:
                            st.info("일별 작업 데이터가 충분하지 않아 차트를 생성할 수 없습니다.")
                        
                        # 설비별 작업 분포 차트
                        equipment_chart = create_equipment_chart(report_result['stats'])
                        if equipment_chart:
                            st.plotly_chart(equipment_chart, use_container_width=True)
                        else:
                            st.info("설비 데이터가 충분하지 않아 차트를 생성할 수 없습니다.")
                    
                    # 관련 이미지 표시
                    if report_result['images']:
                        st.subheader("📷 관련 이미지")
                        
                        # 이미지를 3열로 표시
                        image_cols = st.columns(min(len(report_result['images']), 3))
                        
                        for i, img in enumerate(report_result['images']):
                            col_idx = i % len(image_cols)
                            with image_cols[col_idx]:
                                if 'path' in img and os.path.exists(img["path"]):
                                    st.image(img["path"], caption=img.get("filename", "이미지"))
                                    
                                    if img.get("description"):
                                        st.markdown("**이미지 설명:**")
                                        st.markdown(img['description'])
                                        
                                    # 기타 메타데이터
                                    st.markdown(f"""
                                    - **공정명:** {img.get('process_name', 'N/A')}
                                    - **설비명:** {img.get('equipment_name', 'N/A')}
                                    - **일자:** {img.get('work_date', 'N/A')}
                                    """)
                                else:
                                    st.warning(f"이미지 파일을 찾을 수 없습니다: {img.get('filename', 'unknown')}")
                    else:
                        st.info(f"{selected_year}년 {selected_month}월 관련 이미지가 없습니다.")
                    
                    # 원본 데이터 표시 (접힌 상태로)
                    with st.expander("원본 데이터 보기", expanded=False):
                        if not report_result['data'].empty:
                            st.dataframe(
                                report_result['data'],
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("표시할 데이터가 없습니다.")
                            
                    # 보고서 생성 완료 메시지
                    st.success(f"보고서 생성이 완료되었습니다. (소요 시간: {elapsed_time:.2f}초)")
                else:
                    st.error("보고서 생성에 실패했습니다.")
                    st.info("다른 년/월을 선택하거나, 다른 모델을 시도해보세요.")
    else:
        # 사용 안내 메시지
        st.info("보고서 생성을 시작하려면 년도와 월을 선택한 후 '보고서 생성' 버튼을 클릭하세요.")
        st.markdown("""
        ### 월별 보고서 기능 안내
        
        이 기능은 선택한 월의 공정관리이력 데이터를 분석하여 상세한 보고서를 생성합니다.
        
        **보고서에 포함되는 내용:**
        - 월간 작업 요약 및 주요 통계
        - 공정별/설비별 작업 분석
        - 작업 유형 분석 및 트렌드
        - 주요 이슈 및 성과
        - 데이터 시각화 및 차트
        - 관련 이미지 모음
        
        **활용 방법:**
        1. 보고서를 생성할 년도와 월을 선택합니다.
        2. '보고서 생성' 버튼을 클릭하여 보고서를 생성합니다.
        3. 생성된 보고서와 차트를 확인합니다.
        4. 필요시 보고서를 다운로드할 수 있습니다.
        
        **유의사항:**
        - 보고서는 현재 설정된 글로벌 모델 ({st.session_state.get('selected_model', 'gemma3:4b')})을 사용하여 생성됩니다.
        - 보고서 생성에는 수 분이 소요될 수 있습니다.
        - 데이터가 부족한 경우 일부 차트나 분석이 제한될 수 있습니다.
        """)