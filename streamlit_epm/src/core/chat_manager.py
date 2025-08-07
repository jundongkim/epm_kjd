"""
DX-AI Manufacturing Copilot - AI 챗봇 관리자

Ollama를 사용한 LLM 기반 챗봇 기능을 제공합니다.
"""

import streamlit as st
import requests
import json
import time
from typing import List, Dict, Any, Generator
from datetime import datetime
from .config import settings


class ChatManager:
    """AI 챗봇 관리 클래스"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.conversation_history = []
        
    def get_available_models(self) -> List[str]:
        """사용 가능한 Ollama 모델 목록 조회"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except Exception as e:
            st.error(f"❌ 모델 목록 조회 실패: {str(e)}")
            return []
    
    def check_ollama_connection(self) -> bool:
        """Ollama 연결 상태 확인"""
        try:
            response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def clear_conversation(self):
        """대화 기록 초기화"""
        self.conversation_history = []
    
    def add_to_conversation(self, role: str, content: str):
        """대화 기록에 메시지 추가"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_conversation_context(self, max_turns: int = 5) -> str:
        """대화 기록을 문맥으로 변환"""
        if not self.conversation_history:
            return ""
        
        # 최근 대화만 사용
        recent_history = self.conversation_history[-max_turns*2:]
        
        context = "\n--- 이전 대화 ---\n"
        for msg in recent_history:
            role_name = "사용자" if msg["role"] == "user" else "AI"
            context += f"{role_name}: {msg['content']}\n"
        context += "--- 현재 질문 ---\n"
        
        return context
    
    def generate_response(self, 
                         prompt: str, 
                         model: str = None,
                         temperature: float = 0.7,
                         context_data: str = "",
                         max_turns: int = 5,
                         max_tokens: int = None) -> Generator[str, None, None]:
        """스트리밍 응답 생성"""
        
        # 기본 모델 설정 (config.py에서 가져옴)
        if model is None:
            model = settings.default_llm_model
        
        # 시스템 프롬프트 구성
        system_prompt = """당신은 DX-AI Manufacturing Copilot의 생산관리 시스템 AI 어시스턴트입니다.

주요 역할:
1. 생산 공정 데이터 분석 및 해석
2. 품질 관리 및 최적화 제안
3. 설비 운영 상태 모니터링
4. 원가 분석 및 효율성 개선 방안 제시
5. 생산 계획 수립 지원

대화 시 다음 원칙을 따라주세요:
- 전문적이고 정확한 제조업 용어 사용
- 데이터 기반의 객관적인 분석 제공
- 구체적이고 실행 가능한 제안 제시
- 안전을 최우선으로 고려
- 한국어로 친근하게 대화

현재 사용자와 제조 공정 관련 질문에 대해 도움을 드리겠습니다.
"""

        # 전체 프롬프트 구성
        full_prompt = f"{system_prompt}\n\n"
        
        if context_data:
            full_prompt += f"=== 현재 생산 데이터 ===\n{context_data}\n\n"
        
        # 대화 기록 추가
        conversation_context = self.get_conversation_context(max_turns)
        if conversation_context:
            full_prompt += conversation_context
        
        full_prompt += f"사용자 질문: {prompt}\n\nAI 답변:"
        
        # 대화 기록에 추가
        self.add_to_conversation("user", prompt)
        
        try:
            # max_tokens 우선순위: 매개변수 > 세션 상태 > config.py 설정
            final_max_tokens = max_tokens or st.session_state.get('max_tokens', settings.ollama_max_tokens)
            
            # Ollama API 호출
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": final_max_tokens,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                yield f"❌ API 호출 실패: {response.status_code}"
                return
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            chunk = data['response']
                            full_response += chunk
                            yield chunk
                        
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            # 대화 기록에 응답 추가
            self.add_to_conversation("assistant", full_response)
            
        except requests.exceptions.RequestException as e:
            yield f"❌ 연결 오류: {str(e)}"
        except Exception as e:
            yield f"❌ 예상치 못한 오류: {str(e)}"
    
    def generate_analysis_report(self, 
                               analysis_data: Dict[str, Any],
                               model: str = None,
                               temperature: float = 0.3,
                               max_tokens: int = None) -> Generator[str, None, None]:
        """분석 보고서 자동 생성"""
        
        # 기본 모델 설정 (config.py에서 가져옴)
        if model is None:
            model = settings.default_llm_model
        
        # 분석 데이터를 텍스트로 변환
        context_data = self._format_analysis_data(analysis_data)
        
        analysis_prompt = """제공된 생산 데이터를 바탕으로 다음 항목에 대한 종합 분석 보고서를 작성해주세요:

1. **현재 상황 요약**
   - 전체 생산 현황
   - 주요 지표 현황

2. **핵심 인사이트**
   - 긍정적 요소
   - 주의가 필요한 요소

3. **개선 권장사항**
   - 단기 개선 방안
   - 중장기 개선 방안

4. **위험 요소 및 대응 방안**

보고서는 경영진이 이해하기 쉽게 구조화하여 작성해주세요."""

        yield from self.generate_response(
            analysis_prompt, 
            model=model, 
            temperature=temperature,
            context_data=context_data,
            max_turns=0,  # 분석 보고서는 이전 대화 기록 사용하지 않음
            max_tokens=max_tokens
        )
    
    def _format_analysis_data(self, data: Dict[str, Any]) -> str:
        """분석 데이터를 텍스트 형태로 포맷팅"""
        formatted_data = []
        
        # Lot 추적 데이터
        if 'lot_tracking' in data:
            lot_data = data['lot_tracking']
            formatted_data.append("=== Lot 추적 현황 ===")
            formatted_data.append(f"활성 Lot: {lot_data.get('active_lots', 0)}개")
            formatted_data.append(f"완료 Lot: {lot_data.get('completed_lots', 0)}개")
            formatted_data.append(f"대기 Lot: {lot_data.get('waiting_lots', 0)}개")
            formatted_data.append(f"전체 Lot: {lot_data.get('total_lots', 0)}개")
            formatted_data.append("")
        
        # 설비 모니터링 데이터
        if 'equipment_monitoring' in data:
            eq_data = data['equipment_monitoring']
            formatted_data.append("=== 설비 모니터링 현황 ===")
            for eq in eq_data:
                formatted_data.append(f"설비 {eq['ID']}: {eq['상태']}, 가동률 {eq['가동률']}%")
            formatted_data.append("")
        
        # 이상탐지 데이터
        if 'anomaly_detection' in data:
            anomaly_data = data['anomaly_detection']
            formatted_data.append("=== 이상탐지 현황 ===")
            formatted_data.append(f"총 검사 Lot: {anomaly_data.get('total_lots', 0)}개")
            formatted_data.append(f"이상 탐지: {anomaly_data.get('anomaly_count', 0)}건")
            formatted_data.append(f"이상 비율: {anomaly_data.get('anomaly_rate', 0):.1f}%")
            formatted_data.append(f"온도 이상: {anomaly_data.get('temp_anomalies', 0)}건")
            formatted_data.append(f"압력 이상: {anomaly_data.get('pressure_anomalies', 0)}건")
            formatted_data.append("")
        
        return "\n".join(formatted_data)


def create_chat_interface(chat_manager: ChatManager, 
                         context_data: str = "",
                         tab_name: str = "일반") -> None:
    """챗봇 인터페이스 생성"""
    
    st.markdown(f"### 💬 AI 어시스턴트 ({tab_name})")
    
    # 연결 상태 확인
    if not chat_manager.check_ollama_connection():
        st.error("❌ Ollama 서비스에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요.")
        st.code("ollama serve", language="bash")
        return
    
    # 대화 기록 표시
    if chat_manager.conversation_history:
        st.markdown("#### 📝 대화 기록")
        
        # 최근 대화만 표시
        recent_history = chat_manager.conversation_history[-10:]
        
        for msg in recent_history:
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            role_name = "사용자" if msg["role"] == "user" else "AI"
            
            with st.expander(f"{role_icon} {role_name} - {msg['timestamp'][:19]}"):
                st.write(msg["content"])
    
    # 채팅 입력
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "질문을 입력하세요:",
            placeholder="예: 현재 생산 현황에 대해 분석해주세요",
            key=f"chat_input_{tab_name}"
        )
    
    with col2:
        send_button = st.button("전송", key=f"send_btn_{tab_name}")
        clear_button = st.button("초기화", key=f"clear_btn_{tab_name}")
    
    # 자동 분석 버튼
    if context_data:
        if st.button(f"📊 {tab_name} 데이터 자동 분석", key=f"auto_analysis_{tab_name}"):
            st.markdown("#### 🔍 AI 분석 결과")
            
            # 사이드바에서 설정 가져오기
            model = st.session_state.get('selected_model', settings.default_llm_model)
            temperature = st.session_state.get('temperature', 0.3)
            max_tokens = st.session_state.get('max_tokens', settings.ollama_max_tokens)
            
            # 분석 데이터 구성
            analysis_data = {
                'context': context_data,
                'tab_name': tab_name
            }
            
            # 스트리밍 응답 표시
            response_container = st.empty()
            full_response = ""
            
            for chunk in chat_manager.generate_analysis_report(
                analysis_data, 
                model=model, 
                temperature=temperature,
                max_tokens=max_tokens
            ):
                full_response += chunk
                response_container.markdown(full_response)
            
            st.success("✅ 분석 완료!")
    
    # 대화 초기화
    if clear_button:
        chat_manager.clear_conversation()
        st.success("🔄 대화 기록이 초기화되었습니다.")
        st.rerun()
    
    # 메시지 전송
    if send_button and user_input:
        st.markdown("#### 🤖 AI 응답")
        
        # 사이드바에서 설정 가져오기
        model = st.session_state.get('selected_model', settings.default_llm_model)
        temperature = st.session_state.get('temperature', 0.7)
        max_turns = st.session_state.get('memory_turns', 5)
        max_tokens = st.session_state.get('max_tokens', settings.ollama_max_tokens)
        
        # 스트리밍 응답 표시
        response_container = st.empty()
        full_response = ""
        
        for chunk in chat_manager.generate_response(
            user_input,
            model=model,
            temperature=temperature,
            context_data=context_data,
            max_turns=max_turns,
            max_tokens=max_tokens
        ):
            full_response += chunk
            response_container.markdown(full_response)
        
        st.success("✅ 응답 완료!")
        
        # 입력 필드 초기화를 위한 재실행 제거 - 자연스럽게 완료되도록 함
        # st.rerun()


def setup_chat_sidebar(chat_manager: ChatManager) -> None:
    """사이드바에 챗봇 설정 추가"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🤖 AI 어시스턴트 설정")
    
    # 모델 선택 (config.py의 available_llm_models 사용)
    available_models = settings.available_llm_models
    model_display_names = list(available_models.keys())
    model_values = list(available_models.values())
    
    if model_display_names:
        selected_display_name = st.sidebar.selectbox(
            "🧠 LLM 모델 선택",
            options=model_display_names,
            index=0,
            help="사용할 LLM 모델을 선택하세요"
        )
        
        # 선택된 표시 이름에 해당하는 실제 모델 값 저장
        selected_model = available_models[selected_display_name]
        st.session_state['selected_model'] = selected_model
        
        # 모델 정보 표시
        model_size = settings.get_model_size_category(selected_model)
        st.sidebar.caption(f"📊 {model_size}")
        
        # 모델 타입에 따른 추가 정보
        if settings.is_ollama_model(selected_model):
            st.sidebar.caption("🏠 로컬 모델 (Ollama)")
            if not chat_manager.check_ollama_connection():
                st.sidebar.error("❌ Ollama 연결 실패")
                st.sidebar.code("ollama serve", language="bash")
        elif settings.is_external_model(selected_model):
            st.sidebar.caption("☁️ 클라우드 모델")
            st.sidebar.warning("⚠️ 외부 API 키가 필요합니다")
            
    else:
        st.sidebar.error("❌ 사용 가능한 모델이 없습니다.")
        st.sidebar.code("ollama pull gemma3:12b-it-qat", language="bash")
    
    # Temperature 설정
    temperature = st.sidebar.slider(
        "🌡️ Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="응답의 창의성을 조절합니다 (0.0: 일관성, 1.0: 창의성)"
    )
    st.session_state['temperature'] = temperature
    
    # Memory Turn 설정
    memory_turns = st.sidebar.slider(
        "🧠 Memory Turns",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        help="대화 기록을 몇 턴까지 기억할지 설정합니다"
    )
    st.session_state['memory_turns'] = memory_turns
    
    # 최대 토큰 수 설정
    max_tokens = st.sidebar.slider(
        "📝 최대 토큰 수",
        min_value=500,
        max_value=8000,
        value=settings.ollama_max_tokens,
        step=500,
        help="생성할 최대 토큰 수를 설정합니다 (더 긴 응답을 위해서는 높은 값 사용)"
    )
    st.session_state['max_tokens'] = max_tokens
    
    # 연결 상태 표시
    st.sidebar.markdown("### 📡 연결 상태")
    if chat_manager.check_ollama_connection():
        st.sidebar.success("✅ Ollama 연결됨")
    else:
        st.sidebar.error("❌ Ollama 연결 실패")
        st.sidebar.code("ollama serve", language="bash") 