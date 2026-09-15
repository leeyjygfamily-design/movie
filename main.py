import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

# 1. 페이지 기본 설정 및 웅장한 다크 시네마 테마 CSS 적용
st.set_page_config(
    page_title="운명의 영화 - 당신이 태어난 날의 BoxOffice",
    layout="wide",
    page_icon="🎬",
)

st.markdown(
    """
<style>
    /* 전체 배경을 깊은 다크 시네마 톤으로 변경 */
    .stApp {
        background-color: #0b0c10;
        color: #c5c6c7;
    }
    
    /* 웅장한 금빛 대형 타이틀 */
    .epic-title {
        font-size: 3.2rem !important;
        font-weight: 900 !important;
        color: #d4af37 !important;
        text-align: center;
        letter-spacing: 4px;
        text-shadow: 0px 0px 20px rgba(212, 175, 55, 0.6);
        margin-bottom: 0.5rem;
    }
    
    /* 서브 타이틀 스타일 */
    .epic-subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #66fcf1;
        letter-spacing: 2px;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* 1위 영화 커스텀 카드 */
    .top-movie-card {
        background: linear-gradient(135deg, #1f2833 0%, #0b0c10 100%);
        border: 2px solid #d4af37;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0px 0px 30px rgba(212, 175, 55, 0.3);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .top-movie-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #ffffff;
        text-shadow: 0 0 10px #45a29e;
        margin-top: 1rem;
    }

    /* Streamlit 지표 카드 스타일 재정의 */
    div[data-testid="stMetric"] {
        background-color: #1f2833;
        border: 1px solid #45a29e;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricLabel"] {
        color: #c5c6c7 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #66fcf1 !important;
    }
</style>
""",
    unsafe_allow_html=True,  # 오타 수정된 부분
)

# 2. 웅장한 헤더 영역
st.markdown(
    "<h1 class='epic-title'>🏛️ 운명의 박스오피스 🏛️</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='epic-subtitle'>당신이 세상에 태어난 그날, 전국의 극장을 사로잡았던 전설의 영화</p>",
    unsafe_allow_html=True,
)

# 3. 날짜 설정 (KOBIS 데이터 전산화 기준일: 2003년 11월 11일 ~ 어제)
try:
    now_kst = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
except Exception:
    now_kst = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )

max_date = (now_kst - datetime.timedelta(days=1)).date()
min_date = datetime.date(2003, 11, 11)

# 생년월일 입력 섹션
col_space1, col_input, col_space2 = st.columns([1, 2, 1])
with col_input:
    birth_date = st.date_input(
        "✨ 생년월일을 선택하고 운명의 영화를 확인하세요",
        value=datetime.date(2005, 1, 1),
        min_value=min_date,
        max_value=max_date,
        help="2003년 11월 11일 이후 날짜부터 조회할 수 있습니다.",
    )

target_dt = birth_date.strftime("%Y%m%d")
formatted_date = birth_date.strftime("%Y년 %m월 %d일")

# 4. API 키 확인
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "❌ **API 키 미설정**: Streamlit Secrets에 `KOBIS_KEY`를 등록해야 합니다."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]


# 5. KOBIS API 데이터 호출 함수
@st.cache_data(ttl=86400)
def fetch_box_office(key, date_str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": date_str}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"통신 장애 발생: {e}"


data, error_msg = fetch_box_office(api_key, target_dt)

st.write("---")

# 6. 결과 출력 및 예외 안내
if error_msg:
    st.error(f"❌ 데이터 요청 실패: {error_msg}")
elif not data:
    st.error("❌ 응답받은 데이터가 없습니다.")
elif "faultInfo" in data:
    st.error(
        f"❌ **API 인증 오류**: {data['faultInfo'].get('message', '키를 확인해 주세요.')}"
    )
else:
    daily_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])

    if not daily_list:
        st.warning(
            f"⚠️ **{formatted_date}**의 집계된 박스오피스 기록이 없습니다."
        )
    else:
        df = pd.DataFrame(daily_list)
        df["rank"] = df["rank"].astype(int)
        df["audiCnt"] = df["audiCnt"].astype(int)
        df["audiAcc"] = df["audiAcc"].astype(int)

        top_movie = df.iloc[0]

        # 웅장한 1위 영화 하이라이트 전파
        st.markdown(
            f"""
        <div class="top-movie-card">
            <p style="color: #d4af37; font-size: 1.2rem; font-weight: bold; letter-spacing: 3px;">
                👑 {formatted_date} · 당신과 함께 태어난 1위 영화 👑
            </p>
            <div class="top-movie-title">« {top_movie['movieNm']} »</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 1위 영화 세부 지표
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("당일 관객 수", f"{top_movie['audiCnt']:,} 명")
        with m_col2:
            st.metric("누적 관객 수", f"{top_movie['audiAcc']:,} 명")
        with m_col3:
            st.metric("개봉일", top_movie["openDt"])

        st.markdown("<br>", unsafe_allow_html=True)

        # 상위 5개 관객수 차트
        st.subheader("⚔️ 당시 왕좌를 다투던 TOP 5 영화")
        top_5_df = df.head(5).copy()
        chart_df = top_5_df[["movieNm", "audiCnt"]].set_index("movieNm")
        chart_df.columns = ["관객수"]
        st.bar_chart(chart_df)

        st.markdown("<br>", unsafe_allow_html=True)

        # 전체 순위 표
        st.subheader("📜 당시 박스오피스 전체 순위 (TOP 10)")
        display_df = df[
            ["rank", "movieNm", "openDt", "audiCnt", "audiAcc"]
        ].copy()
        display_df.columns = [
            "순위",
            "영화명",
            "개봉일",
            "당일 관객수",
            "누적 관객수",
        ]

        st.dataframe(
            display_df.style.format(
                {"당일 관객수": "{:,}", "누적 관객수": "{:,}"}
            ),
            use_container_width=True,
            hide_index=True,
        )
