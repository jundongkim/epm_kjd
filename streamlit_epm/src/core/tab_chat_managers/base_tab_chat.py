"""
DX-AI Manufacturing Copilot - 기본 탭 챗봇 매니저

모든 탭별 챗봇 매니저의 기본 클래스를 제공합니다.
"""

import streamlit as st
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Generator
from datetime import datetime
from src.core.chat_manager import ChatManager


class BaseTabChatManager(ABC):
    """탭별 챗봇 매니저 기본 클래스"""
    
    def __init__(self, tab_name: str, chat_manager: ChatManager):
        self.tab_name = tab_name
        self.chat_manager = chat_manager
        self.analysis_report = None
        self.context_data = None
        
    @abstractmethod
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """탭별 데이터를 Context로 변환"""
        pass
    
    @abstractmethod
    def generate_analysis_questions(self) -> List[str]:
        """분석 보고서 기반 추천 질문 생성"""
        pass
    
    @abstractmethod
    def get_tab_specific_system_prompt(self) -> str:
        """탭별 특화 시스템 프롬프트"""
        pass
    
    def update_context_data(self, data: Dict[str, Any], date_filter: str):
        """Context 데이터 업데이트"""
        self.context_data = self.format_context_data(data, date_filter)
    
    def generate_analysis_report(self, model: str, temperature: float = 0.3) -> Generator[str, None, None]:
        """분석 보고서 생성"""
        if not self.context_data:
            yield "❌ 분석할 데이터가 없습니다. 먼저 데이터를 로드해주세요."
            return
        
        # 탭별 특화 분석 프롬프트
        analysis_prompt = f"""
{self.get_tab_specific_system_prompt()}

다음 {self.tab_name} 데이터를 바탕으로 종합 분석 보고서를 작성해주세요:

=== 분석 보고서 구조 ===
1. **📊 현재 상황 요약**
   - 핵심 지표 현황
   - 전반적 상태 평가

2. **🔍 상세 분석**
   - 주요 발견사항
   - 데이터 트렌드 분석
   - 성능 지표 평가

3. **⚠️ 주의사항 및 위험 요소**
   - 우선순위별 위험 요소
   - 예상 영향도

4. **💡 개선 권장사항**
   - 즉시 조치 사항
   - 단기 개선 방안
   - 중장기 전략

5. **❓ 추가 분석 질문**
   - 심화 분석을 위한 질문 제안
   - 데이터 수집 권장사항

보고서는 실무진과 경영진 모두가 이해하기 쉽게 작성해주세요.
"""
        
        # ChatManager를 통해 분석 보고서 생성
        full_response = ""
        for chunk in self.chat_manager.generate_response(
            analysis_prompt,
            model=model,
            temperature=temperature,
            context_data=self.context_data,
            max_turns=0,  # 분석 보고서는 이전 대화 기록 사용하지 않음
            max_tokens=st.session_state.get('max_tokens', 4000)
        ):
            full_response += chunk
            yield chunk
        
        # 생성된 보고서 저장
        self.analysis_report = full_response
    
    def create_chat_interface(self):
        """탭별 챗봇 인터페이스 생성"""
        st.markdown(f"### 💬 {self.tab_name} AI 어시스턴트")
        
        # 연결 상태 확인
        if not self.chat_manager.check_ollama_connection():
            st.error("❌ Ollama 서비스에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요.")
            st.code("ollama serve", language="bash")
            return
        
        # 탭별 전용 세션 상태 키
        chat_history_key = f"chat_history_{self.tab_name}"
        analysis_report_key = f"analysis_report_{self.tab_name}"
        analysis_generated_key = f"analysis_generated_{self.tab_name}"
        
        # 세션 상태 초기화
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = []
        if analysis_generated_key not in st.session_state:
            st.session_state[analysis_generated_key] = False
        
        # 분석 보고서 생성 섹션
        st.markdown("#### 📊 자동 분석 보고서")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.info(f"💡 현재 {self.tab_name} 데이터를 AI가 자동으로 분석하여 종합 보고서를 생성합니다.")
        
        with col2:
            generate_report_btn = st.button(
                "🔍 분석 시작", 
                key=f"generate_report_{self.tab_name}",
                help="현재 데이터를 기반으로 AI 분석 보고서를 생성합니다."
            )
        
        with col3:
            # 분석 초기화 버튼 (분석이 완료된 경우에만 표시)
            if st.session_state.get(analysis_generated_key, False):
                reset_analysis_btn = st.button(
                    "🔄 분석 초기화",
                    key=f"reset_analysis_{self.tab_name}",
                    help="분석 보고서를 초기화하고 새로운 분석을 시작합니다."
                )
                if reset_analysis_btn:
                    st.session_state[analysis_generated_key] = False
                    if analysis_report_key in st.session_state:
                        del st.session_state[analysis_report_key]
                    st.success("🔄 분석이 초기화되었습니다.")
                    st.rerun()
        
        # 분석 보고서 생성 및 표시
        if generate_report_btn:
            if not self.context_data:
                st.error("❌ 분석할 데이터가 없습니다. 데이터를 먼저 로드해주세요.")
                return
            
            # 사이드바에서 설정 가져오기
            model = st.session_state.get('selected_model', None)
            temperature = st.session_state.get('temperature', 0.3)
            max_tokens = st.session_state.get('max_tokens', 4000)
            
            st.markdown("#### 📋 분석 보고서")
            
            # 스트리밍 응답 표시
            response_container = st.empty()
            full_response = ""
            
            with st.spinner("🤖 AI가 데이터를 분석하고 있습니다..."):
                for chunk in self.generate_analysis_report(model, temperature):
                    full_response += chunk
                    response_container.markdown(full_response)
            
            # 세션 상태에 보고서 저장
            st.session_state[analysis_report_key] = full_response
            st.session_state[analysis_generated_key] = True
            
            st.success("✅ 분석 보고서 생성 완료!")
        
        # 분석 보고서가 생성되었다면 추천 질문 표시 (세션 상태 기반)
        if st.session_state.get(analysis_generated_key, False):
            st.markdown("#### 💡 추천 질문")
            recommended_questions = self.generate_analysis_questions()
            
            # 추천 질문 버튼들
            cols = st.columns(min(len(recommended_questions), 3))
            for i, question in enumerate(recommended_questions[:6]):  # 최대 6개까지
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(f"❓ {question}", key=f"rec_q_{self.tab_name}_{i}"):
                        # 추천 질문을 임시 키에 저장하여 위젯 생성 전에 처리되도록 함
                        st.session_state[f"pending_question_{self.tab_name}"] = question
                        # 페이지를 다시 로드하여 입력 필드 업데이트 (분석 상태는 유지됨)
                        st.rerun()
        
        # 기존 분석 보고서 표시
        if analysis_report_key in st.session_state:
            st.markdown("#### 📋 최근 분석 보고서")
            with st.expander("📊 보고서 내용 보기", expanded=False):
                st.markdown(st.session_state[analysis_report_key])
        
        # 연속 질문 답변 섹션
        st.markdown("---")
        st.markdown("#### 💬 질문 & 답변")
        
        # 대화 기록 표시
        if st.session_state[chat_history_key]:
            st.markdown("**📝 대화 기록**")
            
            # 최근 대화 10개만 표시
            recent_conversations = st.session_state[chat_history_key][-10:]
            
            for i, conversation in enumerate(recent_conversations):
                with st.expander(f"💬 대화 {i+1}: {conversation['question'][:50]}...", expanded=False):
                    st.markdown(f"**👤 질문:** {conversation['question']}")
                    st.markdown(f"**🤖 답변:** {conversation['answer']}")
                    st.markdown(f"**⏰ 시간:** {conversation['timestamp']}")
        
        # 질문 입력 및 답변 생성
        st.markdown("**🔍 새로운 질문하기**")
        
        # 질문 입력
        user_input_key = f"user_input_{self.tab_name}"
        widget_key = f"question_input_{self.tab_name}"
        pending_question_key = f"pending_question_{self.tab_name}"
        
        # 위젯 생성 전에 session_state 초기화
        if widget_key not in st.session_state:
            st.session_state[widget_key] = ""
        
        # 추천 질문 클릭 시 위젯에 값 설정 (위젯 생성 전에 처리)
        if pending_question_key in st.session_state and st.session_state[pending_question_key]:
            st.session_state[widget_key] = st.session_state[pending_question_key]
            del st.session_state[pending_question_key]  # 일회성 설정 후 제거
        
        # 기존 user_input_key 처리 (하위 호환성)
        if user_input_key in st.session_state and st.session_state[user_input_key]:
            st.session_state[widget_key] = st.session_state[user_input_key]
            del st.session_state[user_input_key]  # 일회성 설정 후 제거
        
        user_question = st.text_area(
            "질문을 입력하세요:",
            placeholder=f"예: {self.tab_name} 데이터에서 가장 중요한 개선사항은 무엇인가요?",
            key=widget_key,
            height=80
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            ask_button = st.button("💬 질문하기", key=f"ask_btn_{self.tab_name}")
        
        with col2:
            clear_history_btn = st.button("🗑️ 대화 삭제", key=f"clear_history_{self.tab_name}")
        
        with col3:
            clear_input_btn = st.button("🔄 입력 초기화", key=f"clear_input_{self.tab_name}")
        
        # 입력 초기화 (위젯 키를 삭제하여 다음 실행에서 초기화)
        if clear_input_btn:
            if widget_key in st.session_state:
                del st.session_state[widget_key]
            if user_input_key in st.session_state:
                del st.session_state[user_input_key]
            if pending_question_key in st.session_state:
                del st.session_state[pending_question_key]
            st.rerun()
        
        # 대화 기록 삭제
        if clear_history_btn:
            st.session_state[chat_history_key] = []
            st.success("🔄 대화 기록이 삭제되었습니다.")
            st.rerun()
        
        # 질문 답변 생성
        if ask_button and user_question.strip():
            # 사이드바에서 설정 가져오기
            model = st.session_state.get('selected_model', None)
            temperature = st.session_state.get('temperature', 0.7)
            max_turns = st.session_state.get('memory_turns', 5)
            max_tokens = st.session_state.get('max_tokens', 4000)
            
            st.markdown("#### 🤖 AI 답변")
            
            # 스트리밍 응답 표시
            response_container = st.empty()
            full_response = ""
            
            with st.spinner("🤖 AI가 답변을 생성하고 있습니다..."):
                for chunk in self.chat_manager.generate_response(
                    user_question,
                    model=model,
                    temperature=temperature,
                    context_data=self.context_data,
                    max_turns=max_turns,
                    max_tokens=max_tokens
                ):
                    full_response += chunk
                    response_container.markdown(full_response)
            
            # 대화 기록에 추가
            conversation = {
                'question': user_question,
                'answer': full_response,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            st.session_state[chat_history_key].append(conversation)
            
            # 입력 필드 초기화를 위해 위젯 키를 삭제하여 다음 실행에서 초기화
            if widget_key in st.session_state:
                del st.session_state[widget_key]
            if user_input_key in st.session_state:
                del st.session_state[user_input_key]
            if pending_question_key in st.session_state:
                del st.session_state[pending_question_key]
            
            st.success("✅ 답변 생성 완료!")
            # st.rerun() 제거 - AI 응답 완료 후 자연스럽게 완료되도록 함
    
    def get_conversation_summary(self) -> str:
        """대화 요약 정보 반환"""
        chat_history_key = f"chat_history_{self.tab_name}"
        if chat_history_key in st.session_state:
            conversations = st.session_state[chat_history_key]
            return f"총 {len(conversations)}개의 대화 기록"
        return "대화 기록 없음" 