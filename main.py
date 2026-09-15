
from datetime import datetime, timedelta
import zoneinfo
import pandas as pd
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="어제의 박스오피스", page_icon="🎬", layout="wide"
)

st.title("🎬 어제의 박스오피스 TOP 10")


# KOBIS API 데이터 수신 함수 (st.cache_data를 사용해 불필요한 반복 요청 방지)
@st.cache_data(ttl=3600)
def fetch_boxoffice_data(api_key, target_date):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 오류가 발생했습니다: {e}"


# 1. secrets에서 KOBIS API 키 가져오기
if "KOBIS_KEY" not in st.secrets:
    st.error("🔑 API 키가 설정되지 않았습니다.")
    st.info(
        "Streamlit Cloud의 App Settings > Secrets에 `KOBIS_KEY = '발급받은_키'`를 입력해주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 2. 한국 시간(KST) 기준으로 어제 날짜 계산 (YYYYMMDD 형식)
kst = zoneinfo.ZoneInfo("Asia/Seoul")
yesterday = datetime.now(kst) - timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")
display_date = yesterday.strftime("%Y년 %m월 %d일")

st.caption(f" 기준 일자: {display_date}")

# 3. API 데이터 요청
data, error_msg = fetch_boxoffice_data(api_key, target_dt)

# 4. 예외 및 오류 처리
if error_msg:
    st.error(error_msg)
    st.info("💡 인터넷 연결 상태를 확인해보세요.")
    st.stop()

# API 인증 오류 처리 (KOBIS는 키가 틀려도 HTTP 200 응답과 함께 faultInfo 반환)
if "faultInfo" in data:
    fault = data["faultInfo"]
    st.error(f"❌ API 오류 발생: {fault.get('message', '알 수 없는 오류')}")
    st.info(
        "💡 Streamlit Secrets에 입력한 KOBIS_KEY가 올바른지, 혹은 KOBIS 응답 한도를 초과했는지 확인해주세요."
    )
    st.stop()

# 영화 목록 데이터 추출
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("⚠️ 조회된 박스오피스 데이터가 없습니다.")
    st.info(
        "💡 해당 날짜의 데이터가 아직 집계되지 않았거나 KOBIS 데이터베이스 점검 중일 수 있습니다."
    )
    st.stop()

# 5. 데이터 프레임 변환 및 전처리
df = pd.DataFrame(daily_list)

# 필요한 컬럼 추출 및 숫자형 변환 (KOBIS API는 숫자를 문자열로 반환함)
numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 6. 1위 영화 지표 카드 (Metrics)
top_1 = df.iloc[0]

st.subheader(f"🥇 1위: {top_1['movieNm']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="일일 관객수", value=f"{top_1['audiCnt']:,} 명"
    )
with col2:
    st.metric(
        label="누적 관객수", value=f"{top_1['audiAcc']:,} 명"
    )
with col3:
    st.metric(
        label="스크린 수", value=f"{top_1['scrnCnt']:,} 개"
    )

st.divider()

# 7. 상위 5개 영화 일일 관객수 막대그래프
st.subheader("📊 관객수 TOP 5")
top_5_df = df.head(5)

# Plotly나 Altair 없이 Streamlit 내장 차트로 간단히 시각화
chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
chart_data.columns = ["일일 관객수"]
st.bar_chart(chart_data)

st.divider()

# 8. 박스오피스 전체 순위 표
st.subheader("📋 전체 순위 목록")

# 표 출력을 위해 컬럼 이름 변경 및 정렬
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

# 화면에 표 출력
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
