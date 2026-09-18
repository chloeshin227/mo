import streamlit as st
from openai import OpenAI

# ==============================
# 페이지 설정
# ==============================
st.title("📚 까칠한 AI 정보 선생님")
st.write("모르는 게 있으면 물어봐. ...딱히 네가 궁금해서 알려주는 건 아니고.")

# ==============================
# Gemini API 키 가져오기
# ==============================
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("secrets.toml 파일에 GEMINI_API_KEY 설정이 누락되었습니다.")
    st.stop()

# ==============================
# Gemini API 클라이언트
# ==============================
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# ==============================
# AI 선생님 성격 설정
# ==============================
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
너는 중고등학생을 가르치는 남자 정보 선생님이다.

[성격]
- 기본적으로 까칠하고 무심한 츤데레 스타일이다.
- 학생의 질문에 "그것도 모르냐", "참 답답하네"처럼 가볍게 놀릴 수 있지만,
  절대로 학생을 모욕하거나 자존감을 깎아내리지 않는다.
- 겉으로는 귀찮아하는 것처럼 말하지만 실제로는 학생이 이해할 때까지 친절하게 설명한다.
- 학생이 어려워하거나 틀렸을 때는 은근히 걱정하고 격려한다.
- 학생이 잘하면 직접적으로 과하게 칭찬하기보다는
  "뭐, 이 정도면 꽤 잘했네."처럼 무심하게 인정한다.
- 가끔 "내가 특별히 설명해 주는 거니까 잘 들어." 같은 츤데레식 표현을 사용한다.
- 말투는 자연스러운 한국어 구어체를 사용한다.
- 과도한 유행어, 인터넷 밈, 이모지는 사용하지 않는다.
- 학생과의 관계는 철저히 교사와 학생의 교육적 관계로 유지한다.
- 연애, 플러팅, 신체적 친밀감, 성적인 표현은 절대 사용하지 않는다.

[추구하는 분위기]
- 차분하고 세련된 교실 분위기
- 약간의 빈티지한 선생님 감성
- 칠판, 노트, 만년필, 책, 커피가 어울리는 지적인 분위기
- "까칠하지만 믿을 수 있는 선생님"이라는 이미지를 유지한다.

[답변 방식]
- 중고등학생이 이해할 수 있도록 어려운 개념은 쉬운 말로 설명한다.
- 질문의 핵심부터 답한다.
- 필요하면 예시를 사용한다.
- 복잡한 내용은 단계별로 나누어 설명한다.
- 학생의 답변이 틀렸다면 틀린 부분과 이유를 친절하게 설명한다.
- 반드시 자연스러운 한국어로 답한다.
""",
}

# ==============================
# 세션 상태 초기화
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================
# 사이드바
# ==============================
with st.sidebar:
    st.header("⚙️ 대화 설정")

    st.caption("지금까지의 대화 기록을 관리할 수 있어.")

    if st.button(
        "🗑️ 대화 지우기",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.caption(
        "“딱히 네 질문이 궁금해서 답하는 건 아니야.\n"
        "모르면 손해 보는 건 너니까 알려주는 거지.”"
    )

# ==============================
# 기존 대화 화면에 표시
# ==============================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==============================
# 사용자 질문
# ==============================
if user_input := st.chat_input("질문을 입력하세요..."):

    # 사용자 메시지 저장
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(user_input)

    # ==============================
    # AI 응답
    # ==============================
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # 시스템 프롬프트 + 전체 대화 내역
            api_messages = [SYSTEM_PROMPT] + st.session_state.messages

            # Gemini API 호출
            response = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=api_messages,
                stream=True,
            )

            # 스트리밍 응답
            for chunk in response:
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    full_response += chunk.choices[0].delta.content

                    response_placeholder.markdown(
                        full_response + "▌"
                    )

            # 최종 응답
            response_placeholder.markdown(full_response)

            # AI 응답 저장
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                }
            )

        except Exception as e:
            response_placeholder.error(
                "잠깐만. 지금은 AI 선생님이 접속 상태가 좀 안 좋네. "
                "잠시 후 다시 질문해 봐."
            )

            # 개발 중 오류 확인용
            # 배포할 때는 필요 없다면 주석 처리 가능
            st.caption(f"오류 정보: {e}")
