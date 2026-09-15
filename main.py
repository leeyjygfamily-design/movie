import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

# 1. 페이지 기본 설정 (제목 및 넓은 레이아웃)
st.set_page_config(page_title="어제 박스오피스 순위", layout="wide")
st.title("🎬 어제 일별 박스오피스 TOP 10")

# 2. 파이썬 기본 모듈(zoneinfo)로 한국 표준시(KST) 어제 날짜 구하기
# 배포 서버 시계(UTC)와 상관없이 한국 시간 기준으로 어제 날짜를 계산합니다.
try:
    now_kst = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
except Exception:
    # 혹시 모를 타임존 환경 예외를 대비한 UTC+9 고정 시차 방식
    now_kst = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )

yesterday = now_kst - datetime.timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")  # API 요청용 (YYYYMMDD)
formatted_date = yesterday.strftime("%Y년 %m월 %d일")

st.caption(f"기준일자: {formatted_date}")

# 3. Streamlit Secrets에서 API 키 불러오기
# Streamlit Cloud의 Secrets 설정에 KOBIS_KEY가 등록되어 있어야 합니다.
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "❌ **API 키 설정 필요**: Streamlit Cloud Secrets에 `KOBIS_KEY`를 등록해 주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]


# 4. KOBIS API 요청 처리 함수 (캐싱 적용으로 속도 최적화)
@st.cache_data(ttl=3600)  # 1시간 동안 조회 결과 보관
def fetch_box_office_data(key, date_str):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": key, "targetDt": date_str}

    try:
        response = requests.get(url, params=params, timeout=10)
        # HTTP 응답 코드가 200(성공)이 아닌 경우 예외 처리
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"네트워크 통신 오류가 발생했습니다: {e}"


# API 데이터 요청 실행
data, error_msg = fetch_box_office_data(api_key, target_dt)

# 5. 오류 및 예외 상황 한국어 안내 처리
if error_msg:
    st.error(
        f"❌ **데이터 요청 실패**\n\n- {error_msg}\n- 인터넷 연결 상태를 확인해 주세요."
    )
elif not data:
    st.error(
        "❌ **응답 데이터 없음**: 영화진흥위원회 서버로부터 데이터를 받아오지 못했습니다."
    )
# 인증키가 틀렸거나 문제가 있을 때 KOBIS에서 보내는 faultInfo 객체 처리
elif "faultInfo" in data:
    fault_msg = data["faultInfo"].get(
        "message", "알 수 없는 오류가 발생했습니다."
    )
    st.error(
        f"❌ **KOBIS API 오류 발생**\n\n"
        f"- **오류 내용**: {fault_msg}\n\n"
        "**확인해야 할 사항:**\n"
        "1. Streamlit Cloud의 Secrets 영역에 `KOBIS_KEY` 값이 정확히 입력되었는지 확인하세요.\n"
        "2. 영화진흥위원회(KOBIS) 개발자 센터에서 키 상태 및 일일 트래픽 제한을 확인해 주세요."
    )
else:
    # 정상 데이터 추출
    box_office_result = data.get("boxOfficeResult", {})
    daily_list = box_office_result.get("dailyBoxOfficeList", [])

    if not daily_list:
        st.warning(
            "⚠️ **영화 목록이 비어 있습니다.**\n\n"
            "- 해당 날짜의 집계 데이터가 아직 업데이트되지 않았거나 조회할 영화가 없을 수 있습니다."
        )
    else:
        # 6. 데이터 전처리 (문자열 데이터를 숫자형 데이터로 변환)
        df = pd.DataFrame(daily_list)

        df["rank"] = df["rank"].astype(int)
        df["audiCnt"] = df["audiCnt"].astype(int)
        df["audiAcc"] = df["audiAcc"].astype(int)
        df["scrnCnt"] = df["scrnCnt"].astype(int)

        # 7. [시각화 1] 1위 영화 지표 카드 3장
        top_movie = df.iloc[0]

        st.subheader(f"🥇 1위: {top_movie['movieNm']}")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="어제 관객수", value=f"{top_movie['audiCnt']:,} 명"
            )
        with col2:
            st.metric(
                label="누적 관객수", value=f"{top_movie['audiAcc']:,} 명"
            )
        with col3:
            st.metric(
                label="상영 스크린수", value=f"{top_movie['scrnCnt']:,} 개"
            )

        st.divider()

        # 8. [시각화 2] 관객수 상위 5개 영화 막대그래프
        st.subheader("📊 관객수 상위 5개 영화")
        top_5_df = df.head(5).copy()

        # 막대그래프에 보여줄 데이터 준비
        chart_df = top_5_df[["movieNm", "audiCnt"]].set_index("movieNm")
        chart_df.columns = ["관객수"]

        st.bar_chart(chart_df)

        st.divider()

        # 9. [시각화 3] 전체 TOP 10 순위 표
        st.subheader("📋 전체 박스오피스 순위")

        # 표에 나타낼 컬럼 지정 및 한글화
        display_df = df[
            ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
        ].copy()
        display_df.columns = [
            "순위",
            "영화명",
            "개봉일",
            "어제 관객수",
            "누적 관객수",
            "스크린수",
        ]

        # 천 단위 쉼표 표기 적용 후 데이터프레임 표시
        st.dataframe(
            display_df.style.format(
                {"어제 관객수": "{:,}", "누적 관객수": "{:,}", "스크린수": "{:,}"}
            ),
            use_container_width=True,
            hide_index=True,
        )
