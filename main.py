from datetime import datetime, timedelta
import zoneinfo
import pandas as pd
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 공주풍 핑크 테마 CSS 주입
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="💖 공주님의 어제 박스오피스 & MBTI 영화 추천 👑",
    page_icon="👑",
    layout="wide",
)

# Streamlit 커스텀 CSS (핑크 배경, 반짝이는 효과, 공주님 스타일 카드 및 폰트)
pink_princess_style = """
<style>
    /* 배경화면: 은은하고 사랑스러운 핑크 그라데이션 및 반짝이 배경 */
    .stApp {
        background: linear-gradient(135deg, #ffe6f2 0%, #ffc0cb 50%, #ffb6c1 100%);
        font-family: 'MaruBuri', 'Nanum Gothic', sans-serif;
    }
    
    /* 제목 및 헤더 스타일 */
    h1 {
        color: #d63384 !important;
        text-shadow: 2px 2px 4px #ffffff, 0 0 10px #ff69b4;
        text-align: center;
        font-weight: 800 !important;
    }
    h2, h3 {
        color: #c2185b !important;
        text-shadow: 1px 1px 2px #ffffff;
    }

    /* 지표 카드(Metric) 공주풍 스타일 지정 */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.85) !important;
        border: 2px solid #ff69b4 !important;
        border-radius: 20px !important;
        padding: 15px !important;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3) !important;
        text-align: center;
    }
    div[data-testid="stMetricLabel"] {
        color: #ad1457 !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] {
        color: #d63384 !important;
        font-weight: 800 !important;
    }

    /* 구분선 핑크색 */
    hr {
        border-top: 2px dashed #ff69b4 !important;
    }

    /* 버튼 공주풍 스타일 */
    .stButton>button {
        background: linear-gradient(45deg, #ff69b4, #ff1493) !important;
        color: white !important;
        border-radius: 25px !important;
        border: 2px solid #ffffff !important;
        font-weight: bold !important;
        box-shadow: 0 4px 10px rgba(255, 20, 147, 0.3) !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 15px rgba(255, 20, 147, 0.5) !important;
    }

    /* 셀렉트박스 및 드롭다운 핑크 스타일 */
    div[data-baseweb="select"] {
        border-radius: 15px !important;
    }
</style>
"""
st.markdown(pink_princess_style, unsafe_allow_html=True)

# 메인 타이틀
st.title("💖 ✨ 공주님의 어제 박스오피스 ✨ 👑")


# -----------------------------------------------------------------------------
# 2. KOBIS API 데이터 수신 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_boxoffice_data(api_key, target_date):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 오류가 발생했습니다: {e}"


# -----------------------------------------------------------------------------
# 3. secrets에서 KOBIS API 키 검증
# -----------------------------------------------------------------------------
if "KOBIS_KEY" not in st.secrets:
    st.error("🎀 API 키가 설정되지 않았습니다, 공주님!")
    st.info(
        "💡 Streamlit Cloud의 App Settings > Secrets에 `KOBIS_KEY = '발급받은_키'`를 입력해 주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# -----------------------------------------------------------------------------
# 4. 한국 시간(KST) 기준 어제 날짜 계산
# -----------------------------------------------------------------------------
kst = zoneinfo.ZoneInfo("Asia/Seoul")
yesterday = datetime.now(kst) - timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")
display_date = yesterday.strftime("%Y년 %m월 %d일")

st.markdown(
    f"<h4 style='text-align: center; color: #ad1457;'>🌸 기준 일자: {display_date} 🌸</h4>",
    unsafe_allow_html=True,
)
st.write("")

# -----------------------------------------------------------------------------
# 5. API 요청 및 예외 처리
# -----------------------------------------------------------------------------
data, error_msg = fetch_boxoffice_data(api_key, target_dt)

if error_msg:
    st.error(f"🎀 {error_msg}")
    st.info("💡 인터넷 연결 상태를 확인해 주세요, 공주님.")
    st.stop()

if "faultInfo" in data:
    fault = data["faultInfo"]
    st.error(
        f"🎀 API 오류 발생: {fault.get('message', '알 수 없는 오류입니다.')}"
    )
    st.info(
        "💡 Streamlit Secrets에 입력한 KOBIS_KEY가 올바른지, 혹은 요청 한도를 초과했는지 확인해 주세요."
    )
    st.stop()

box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("🎀 조회된 박스오피스 데이터가 없습니다.")
    st.info(
        "💡 아직 집계 전이거나 KOBIS 점검 중일 수 있습니다. 잠시 후 다시 확인해 주세요!"
    )
    st.stop()

# -----------------------------------------------------------------------------
# 6. 데이터 전처리
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -----------------------------------------------------------------------------
# 7. 1위 영화 하이라이트 (공주풍 지표 카드 3개)
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]

st.subheader(f"👑 1위 영예의 작품: ✨ {top_1['movieNm']} ✨")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="💖 어제 들어온 관객수", value=f"{top_1['audiCnt']:,} 명"
    )
with col2:
    st.metric(
        label="💎 누적 사랑받은 관객수", value=f"{top_1['audiAcc']:,} 명"
    )
with col3:
    st.metric(
        label="🎬 전국 상영 스크린수", value=f"{top_1['scrnCnt']:,} 개"
    )

st.divider()

# -----------------------------------------------------------------------------
# 8. 상위 5개 영화 관객수 막대그래프
# -----------------------------------------------------------------------------
st.subheader("🎀 관객수 TOP 5 인기 차트")
top_5_df = df.head(5)

chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
chart_data.columns = ["일일 관객수"]
st.bar_chart(chart_data)

st.divider()

# -----------------------------------------------------------------------------
# 9. 박스오피스 전체 순위 표
# -----------------------------------------------------------------------------
st.subheader("📋 화려한 전체 순위 리스트")

display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "일일 관객수",
    "누적 관객수",
    "스크린수",
]

st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "일일 관객수": st.column_config.NumberColumn(format="%d 명"),
        "누적 관객수": st.column_config.NumberColumn(format="%d 명"),
        "스크린수": st.column_config.NumberColumn(format="%d 개"),
    },
)

st.divider()

# -----------------------------------------------------------------------------
# 10. MBTI별 맞춤 현행 박스오피스 영화 추천 기능
# -----------------------------------------------------------------------------
st.subheader("🔮 공주님의 MBTI 맞춤 박스오피스 추천 영화")
st.write(
    "현재 박스오피스 상위권 영화 중 공주님의 성향에 딱 맞는 영화를 골라드려요! 💖"
)

# 16가지 MBTI 유형 목록
mbti_types = [
    "ISTJ",
    "ISFJ",
    "INFJ",
    "INTJ",
    "ISTP",
    "ISFP",
    "INFP",
    "INTP",
    "ESTP",
    "ESFP",
    "ENFP",
    "ENTP",
    "ESTJ",
    "ESFJ",
    "ENFJ",
    "ENTJ",
]

user_mbti = st.selectbox(
    "✨ 공주님의 MBTI 유형을 선택해 주세요:", mbti_types, index=6
)

# MBTI 성향(E/I, S/N, T/F, J/P)에 따른 순위 선택 로직
# 예: P(자유로운 영혼) 계열은 1위, J(계획적) 계열은 안정한 상위권, N(상상력)은 중위권 독특함 등
if len(df) > 0:
    # 간단한 MBTI 매핑 알고리즘: MBTI 해시값을 이용해 순위 목록 중 매칭
    mbti_hash = sum(ord(char) for char in user_mbti)
    recommended_index = mbti_hash % len(df)
    recommended_movie = df.iloc[recommended_index]

    # MBTI 그룹별 추천 이유 생성
    reasons = {
        "E": "활기차고 에너지 넘치는 공주님께 박스오피스의 뜨거운 흥행 에너지를 전해드려요!",
        "I": "조용하고 차분하게 작품 속 깊은 감동과 서사에 몰입하기 완벽한 영화예요.",
        "S": "현실감 넘치는 연출과 확실한 재미, 알찬 볼거리가 가득한 작품이에요.",
        "N": "풍부한 상상력과 흥미진진한 설정으로 영감을 자극할 영화랍니다.",
    }

    first_char = user_mbti[0]
    reason_text = reasons.get(
        first_char, "공주님의 취향을 저격할 특별한 추천작입니다!"
    )

    st.balloons()  # 귀여운 풍선 애니메이션 효과
    st.markdown(
        f"""
        <div style="background-color: rgba(255, 255, 255, 0.9); border: 2px solid #ff1493; border-radius: 20px; padding: 20px; text-align: center; box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);">
            <h3 style="color: #ff1493 !important; margin-bottom: 10px;">🌟 {user_mbti} 공주님을 위한 추천 영화 🌟</h3>
            <h2 style="color: #d63384 !important;">🎬 『{recommended_movie['movieNm']}』</h2>
            <p style="color: #880e4f; font-size: 16px; margin-top: 10px;"><b>현재 순위:</b> {recommended_movie['rank']}위 | <b>개봉일:</b> {recommended_movie['openDt']}</p>
            <p style="color: #ad1457; font-size: 15px; font-style: italic;">"{reason_text}"</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
