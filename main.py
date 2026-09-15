from datetime import datetime, timedelta
import zoneinfo
import pandas as pd
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 ultra-cute 토끼 핑크 테마 CSS 주입
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="🐰 핑크토끼 공주님의 박스오피스 & MBTI 영화 추천 🎀",
    page_icon="🐰",
    layout="wide",
)

# 토끼 & 핑크공주풍 커스텀 CSS
rabbit_pink_style = """
<style>
    /* 전체 배경: 은은한 파스텔 핑크 그라데이션 & 구름 느낌 */
    .stApp {
        background: linear-gradient(135deg, #fff0f5 0%, #ffd1dc 40%, #ffb6c1 80%, #ffa6c9 100%);
        font-family: 'Nanum Gothic', 'Malgun Gothic', sans-serif;
    }
    
    /* 헤더 둥글둥글 핑크 텍스트 */
    h1 {
        color: #ff3385 !important;
        text-shadow: 3px 3px 6px #ffffff, 0 0 15px #ff99cc;
        text-align: center;
        font-weight: 900 !important;
        padding-bottom: 5px;
    }
    h2, h3 {
        color: #d63384 !important;
        text-shadow: 2px 2px 4px #ffffff;
    }

    /* 토끼 귀여운 카드 (Metric) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.92) !important;
        border: 3px solid #ff99cc !important;
        border-radius: 25px !important;
        padding: 18px !important;
        box-shadow: 0 8px 20px rgba(255, 105, 180, 0.3) !important;
        text-align: center;
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px) scale(1.02);
    }
    div[data-testid="stMetricLabel"] {
        color: #c2185b !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #ff007f !important;
        font-weight: 800 !important;
    }

    /* 점선 구분선 */
    hr {
        border-top: 3px dashed #ff80bf !important;
        margin: 30px 0 !important;
    }

    /* 토끼 핑크 버튼 */
    .stButton>button {
        background: linear-gradient(45deg, #ff66b2, #ff1a8c) !important;
        color: white !important;
        border-radius: 30px !important;
        border: 3px solid #ffffff !important;
        font-size: 18px !important;
        font-weight: bold !important;
        box-shadow: 0 6px 15px rgba(255, 26, 140, 0.4) !important;
        padding: 10px 25px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: scale(1.08) rotate(-1deg);
        box-shadow: 0 8px 20px rgba(255, 26, 140, 0.6) !important;
    }

    /* 데이터프레임 테두리 감싸기 */
    div[data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 20px;
        padding: 10px;
        border: 2px solid #ff99cc;
        box-shadow: 0 4px 15px rgba(255, 182, 193, 0.4);
    }

    /* 토끼 둥둥 떠다니는 상단 배너 카드 */
    .rabbit-banner {
        background: rgba(255, 255, 255, 0.88);
        border: 3px solid #ff66b2;
        border-radius: 30px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(255, 105, 180, 0.3);
        margin-bottom: 25px;
    }
</style>
"""
st.markdown(rabbit_pink_style, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 메인 타이틀 & 귀여운 토끼 배너
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="rabbit-banner">
        <span style="font-size: 40px;">🐇 🥕 🌸 🐇 🥕 🌸</span>
        <h1>🐰💖 핑크토끼 공주님의 박스오피스 💖🐰</h1>
        <p style="color: #d63384; font-size: 18px; font-weight: bold; margin-bottom: 0;">
            ~ 토끼와 함께하는 샤방샤방 어제 영화 순위 여행 ~
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 3. KOBIS API 데이터 수신 함수
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
        return None, f"네트워크 요청 중 오류가 발생했어요: {e}"


# -----------------------------------------------------------------------------
# 4. secrets에서 KOBIS API 키 검증
# -----------------------------------------------------------------------------
if "KOBIS_KEY" not in st.secrets:
    st.error("🐰🔑 앗! API 키를 찾을 수 없어요, 공주님!")
    st.info(
        "💡 Streamlit Cloud의 App Settings > Secrets에 `KOBIS_KEY = '발급받은_키'`를 작성해 주세요 🥕"
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# -----------------------------------------------------------------------------
# 5. 한국 시간(KST) 기준 어제 날짜 계산
# -----------------------------------------------------------------------------
kst = zoneinfo.ZoneInfo("Asia/Seoul")
yesterday = datetime.now(kst) - timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")
display_date = yesterday.strftime("%Y년 %m월 %d일")

st.markdown(
    f"""
    <div style='text-align: center; color: #c2185b; background-color: rgba(255, 255, 255, 0.7); 
                padding: 8px; border-radius: 15px; width: fit-content; margin: 0 auto 20px auto; border: 1px solid #ffb6c1;'>
        🌸 <b>기준 일자:</b> {display_date} (어제 집계분) 🐰
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 6. API 요청 및 예외 처리
# -----------------------------------------------------------------------------
data, error_msg = fetch_boxoffice_data(api_key, target_dt)

if error_msg:
    st.error(f"🐰💦 {error_msg}")
    st.info("💡 인터넷이 연결되어 있는지 확인해 주세요, 공주님 🥕")
    st.stop()

if "faultInfo" in data:
    fault = data["faultInfo"]
    st.error(
        f"🐰💦 API 오류 발생: {fault.get('message', '알 수 없는 오류예요')}"
    )
    st.info(
        "💡 KOBIS_KEY가 정확한지 또는 오늘 일일 요청 횟수를 다 채웠는지 확인해 주세요!"
    )
    st.stop()

box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("🐰❓ 조회된 박스오피스 데이터가 비어 있어요!")
    st.info(
        "💡 아직 어제 집계가 완료되지 않았거나 KOBIS 점검 중일 수 있어요. 잠시 후 당근을 먹으며 기다려 주세요 🥕"
    )
    st.stop()

# -----------------------------------------------------------------------------
# 7. 데이터 전처리
# -----------------------------------------------------------------------------
df = pd.DataFrame(daily_list)

numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -----------------------------------------------------------------------------
# 8. 1위 영화 하이라이트 (토끼 귀 장식 카드로 표현)
# -----------------------------------------------------------------------------
top_1 = df.iloc[0]

st.subheader(f"👑 🐰 최고 인기 1위 영예의 왕관: ✨ {top_1['movieNm']} ✨")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="💖 어제 찾아온 관객수", value=f"{top_1['audiCnt']:,} 명"
    )
with col2:
    st.metric(
        label="💎 총 누적 관객수", value=f"{top_1['audiAcc']:,} 명"
    )
with col3:
    st.metric(
        label="🎬 전국 상영 스크린", value=f"{top_1['scrnCnt']:,} 개"
    )

st.divider()

# -----------------------------------------------------------------------------
# 9. 상위 5개 영화 관객수 막대그래프
# -----------------------------------------------------------------------------
st.subheader("📊 🐇 핑크토끼가 집계한 인기 차트 TOP 5")
top_5_df = df.head(5)

chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
chart_data.columns = ["일일 관객수"]
st.bar_chart(chart_data)

st.divider()

# -----------------------------------------------------------------------------
# 10. 박스오피스 전체 순위 표
# -----------------------------------------------------------------------------
st.subheader("📋 🎀 한눈에 보는 전체 순위 리스트")

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
# 11. MBTI별 맞춤 현행 박스오피스 영화 추천 기능 (토끼 럭키 점괘)
# -----------------------------------------------------------------------------
st.subheader("🔮 🐇 토끼 도사의 MBTI 맞춤 현행 영화 점괘 🥕")
st.write(
    "공주님의 MBTI를 알려주시면 토끼 도사가 현행 박스오피스 영화 중 운명의 짝을 찾아드려요! 💖"
)

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
    "✨ 공주님의 MBTI 성향을 선택해 주세요 🐰:", mbti_types, index=6
)

if len(df) > 0:
    # MBTI별 영화 선택 알고리즘
    mbti_hash = sum(ord(char) for char in user_mbti)
    recommended_index = mbti_hash % len(df)
    recommended_movie = df.iloc[recommended_index]

    # 토끼 멘트 추천 이유
    reasons = {
        "E": "에너지 뿜뿜! 인싸 토끼 공주님께 흥분과 활력이 가득한 이 영화를 추천해요! 🐰⚡",
        "I": "조용히 이불 속에서 팝콘 먹으며 감성에 푹 빠지기 딱 좋은 영화랍니다 🐇🎀",
        "S": "오감 자극! 눈도 귀도 즐거운 확실하고 알찬 재미를 선사할게요 🥕✨",
        "N": "상상력 대폭발! 깊은 여운과 영감을 안겨줄 매력적인 작품이에요 🌙🐰",
    }

    first_char = user_mbti[0]
    reason_text = reasons.get(
        first_char, "공주님의 심장을 심쿵하게 만들 완벽한 영화예요! 💖"
    )

    # 클릭할 수 있는 럭키 추천 버튼
    if st.button("🔮 핑크토끼 점괘 보기! (클릭) 🔮"):
        st.balloons()  # 풍선 효과
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #ffffff 0%, #fff0f5 100%); 
                        border: 3px dashed #ff3399; border-radius: 25px; padding: 25px; 
                        text-align: center; box-shadow: 0 8px 25px rgba(255, 51, 153, 0.3); margin-top: 15px;">
                <p style="font-size: 30px; margin-bottom: 5px;">🐰🥕🎀🐇✨</p>
                <h3 style="color: #ff007f !important; margin-bottom: 10px;">💖 {user_mbti} 공주님을 위한 운명의 영화 💖</h3>
                <h1 style="color: #d63384 !important; font-size: 32px;">🎬 『{recommended_movie['movieNm']}』</h1>
                <p style="color: #880e4f; font-size: 17px; margin-top: 10px;">
                    <b>현재 박스오피스:</b> {recommended_movie['rank']}위 | <b>개봉일:</b> {recommended_movie['openDt']}
                </p>
                <p style="color: #c2185b; font-size: 16px; font-weight: bold; background-color: #ffe6f0; padding: 10px; border-radius: 15px;">
                    "{reason_text}"
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
