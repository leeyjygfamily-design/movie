import streamlit as st
from openai import OpenAI

# 페이지 제목 설정
st.title("💬 K-POP 아이돌 팬싸인회")

# 비밀 금고(secrets.toml)에서 Gemini API 키 가져오기
api_key = st.secrets.get("GEMINI_API_KEY")

# API 키가 없으면 경고 메시지를 띄우고 동작을 멈춤
if not api_key:
    st.error("GEMINI_API_KEY가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해 주세요.")
    st.stop()

# Gemini API를 OpenAI 라이브러리 규격에 맞춰 연결 설정
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# AI의 페르소나(아이돌 성격) 설정 (화면에는 출력되지 않음)
SYSTEM_PROMPT = {
    "role": "system",
    "content": "엄청 유명한 3년차 대한민국 케이팝 남자 아이돌. 대화하는 사람을 팬싸에 처음 온 여자 팬으로 대하고, 싸가지 없음.동태눈깔"
}

# 대화 기록(세션 상태) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 화면에 기존 대화 기록들을 순서대로 말풍선으로 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 채팅 입력창을 띄우고 사용자 입력 받기
if user_input := st.chat_input("할 말을 입력하세요..."):
    # 1. 사용자가 입력한 메시지를 화면 말풍선에 표시
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 2. 대화 기록 목록에 사용자의 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 3. AI 답변 생성 및 실시간 출력
    with st.chat_message("assistant"):
        try:
            # AI에게 전달할 메시지 목록 (성격 설정 + 지금까지의 대화 기록)
            full_messages = [SYSTEM_PROMPT] + st.session_state.messages

            # API 호출 (실시간 응답을 받기 위해 stream=True 설정)
            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=full_messages,
                stream=True,
            )

            # 실시간으로 흘러 나오는 답변을 화면에 표시
            response_text = st.write_stream(stream)
            
            # AI 답변을 대화 기록 목록에 저장
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception:
            # API 요청 실패 시 빨간 에러창 대신 한국어 안내 문구 표시
            st.warning("응답을 불러오는 중에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.")
