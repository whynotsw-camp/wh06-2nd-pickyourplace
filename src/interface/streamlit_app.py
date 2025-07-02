
import os
import sys
import pandas as pd
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium
import pymysql

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visualization.map_drawer import draw_choropleth
from model.rule_based_model import load_and_score_counts

# 페이지 설정
st.set_page_config(layout="wide")
st.title("서울시 행정동 추천 시스템")

# def get_connection():
#     return pymysql.connect(
#         host=os.environ["DB_HOST"],
#         user=os.environ["DB_USER"],
#         password=os.environ["DB_PASSWORD"],
#         database=os.environ["DB_NAME"],
#         charset="utf8mb4"
#     )

# try:
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SHOW TABLES;")
#     tables = cursor.fetchall()
#     st.success("DB 연결 성공!")
#     st.write("테이블 목록:", tables)
# except Exception as e:
#     st.error(f"DB 연결 실패: {e}")

# ✅ 카테고리별 변수 매핑
category_mapping = {
    "transport": ["bus_stop", "subway_station"],
    "living": ["store", "convenience", "market", "library", "bank", "park"],
    "medical": ["pharmacy", "hospital"],
    "safety": ["police_office", "cctv", "street_light", "safety_bell", "crime_rate"],
    "education": ["school"],
    "housing": ["real_estate"]
}

# ✅ 초기 세션 상태 설정
if "result_df" not in st.session_state:
    st.session_state["result_df"] = None

# ---------------- 상단: 슬라이더 가로 정렬 ---------------- 

st.markdown("#### 🧭 추천 조건 설정")
st.markdown("6개 카테고리에 대해 중요도를 설정하세요. 입력한 가중치는 해당 범주의 모든 항목에 동일하게 적용됩니다.")

col1, col2, col3 = st.columns(3)
with col1:
    transport_weight = st.slider("🚌 교통 인프라", 0, 10, 5)
    living_weight = st.slider("🏪 생활 인프라", 0, 10, 5)
with col2:
    medical_weight = st.slider("💊 의료 인프라", 0, 10, 5)
    safety_weight = st.slider("🛡️ 안전 인프라", 0, 10, 5)
with col3:
    education_weight = st.slider("🏫 교육 인프라", 0, 10, 5)
    housing_weight = st.slider("🏠 주거 정보", 0, 10, 5)

# weights = {}
# for cat, vars_in_cat in category_mapping.items():
#     cat_weight = {
#         "transport": transport_weight,
#         "living": living_weight,
#         "medical": medical_weight,
#         "safety": safety_weight,
#         "education": education_weight,
#         "housing": housing_weight,
#     }[cat]
#     for var in vars_in_cat:
#         weights[var] = cat_weight
    
# ✅ 변경: category별 가중치로 직접 넘기기
weights = {
    "transport": transport_weight,
    "living": living_weight,
    "medical": medical_weight,
    "safety": safety_weight,
    "education": education_weight,
    "housing": housing_weight
}

# 버튼 우측 정렬
button_col = st.columns([6, 1])[1]
with button_col:
    if st.button("✅ 추천 점수 계산"):
        with st.spinner("추천 점수 계산 중..."):
            result_df = load_and_score_counts(
                count_dir="data/processed_counts",
                processed_dir="data/processed",
                user_input_scores=weights
            )

            st.session_state["result_df"] = result_df
            st.success("추천 점수 계산 완료!")

# 항상 최신 result_df 사용
result_df = st.session_state.get("result_df")

if "result_df" not in st.session_state or st.session_state["result_df"] is None:
    st.info("추천 점수는 아직 계산되지 않았습니다. 지도는 빈 점수 기준으로 보여집니다.")
    
# ---------------- 중단: 지도 + 상위 10개 ---------------- #
st.markdown("---")
left_col, right_col = st.columns([2, 1])

clicked_dong_name = None
clicked_code = None
final_score = None
clicked_gu_name = None

with left_col:
    st.markdown("#### 🗺️ 추천 점수 기반 행정동 지도")

    try:
        geojson_path = "data/reference/Seoul_HangJeongDong.geojson"
        
        # score_path = "data/result/dongjak_dong_scores.csv"
        # score_df = pd.read_csv(score_path)
        # score_df["dong_code"] = score_df["dong_code"].astype(str)

        # 동코드 문자열형으로 변환
        # result_df["dong_code"] = result_df["dong_code"].astype(str)

        # 💡 지도용 result_df 생성 또는 불러오기
        if "result_df" not in st.session_state or st.session_state["result_df"] is None:
            gdf = gpd.read_file(geojson_path)[["adm_cd2", "adm_nm"]]
            gdf.columns = ["dong_code", "adm_nm"]
            gdf["dong_code"] = gdf["dong_code"].astype(str)

            # 구/동 이름 추출
            gdf["gu_name"] = gdf["adm_nm"].str.extract(r"서울특별시 (\S+구)")
            gdf["dong_name"] = gdf["adm_nm"].str.extract(r"\S+구 (\S+)$")

            result_df = pd.DataFrame({
                "dong_code": gdf["dong_code"],
                "gu_code": gdf["dong_code"].str[:5],
                "final_score": [0.0] * len(gdf)
            })

            # 병합해서 gu_name, dong_name 포함
            result_df = pd.merge(result_df, gdf[["dong_code", "gu_name", "dong_name"]], on="dong_code", how="left")
            result_df["dong_code"] = result_df["dong_code"].astype(str)
        else:
            result_df = st.session_state["result_df"]
            result_df["dong_code"] = result_df["dong_code"].astype(str)

            # ✅ 병합이 안 되어 있다면 Geo정보 merge
            if "dong_name" not in result_df.columns:
                gdf = gpd.read_file(geojson_path)[["adm_cd2", "adm_nm"]]
                gdf.columns = ["dong_code", "adm_nm"]
                gdf["dong_code"] = gdf["dong_code"].astype(str)
                gdf["gu_name"] = gdf["adm_nm"].str.extract(r"서울특별시 (\S+구)")
                gdf["dong_name"] = gdf["adm_nm"].str.extract(r"\S+구 (\S+)$")
                result_df = pd.merge(result_df, gdf[["dong_code", "gu_name", "dong_name"]], on="dong_code", how="left")

        # 지도 생성
        m = draw_choropleth(
            geojson_path=geojson_path,
            data_df=result_df,
            value_column="final_score",
            key_column="dong_code"
        )

        # st_folium 렌더링
        map_data = st_folium(m, width=1000, height=650, returned_objects=["last_active_drawing"])

        if map_data and map_data.get("last_active_drawing"):
            props = map_data["last_active_drawing"]["properties"]
            clicked_code = props.get("adm_cd2")
            match = result_df[result_df["dong_code"] == clicked_code]
            if not match.empty:
                final_score = match.iloc[0]["final_score"]
                clicked_dong_name = match.iloc[0]["dong_name"]
                clicked_gu_name = match.iloc[0]["gu_name"]

    except Exception as e:
        st.error(f"지도 렌더링 중 오류 발생: {e}")

with right_col:
    st.markdown("#### 🔝 상위 20개 추천 동")
    
    result_df = st.session_state.get("result_df")

    if result_df is None:
        st.info("⏳ 추천 점수가 계산되면 상위 20개 지역이 여기에 표시됩니다.")
    else:
        try:
            gdf = gpd.read_file(geojson_path)[["adm_cd2", "adm_nm"]]
            gdf.columns = ["dong_code", "adm_nm"]
            gdf["dong_code"] = gdf["dong_code"].astype(str)

            gdf["gu_name"] = gdf["adm_nm"].str.extract(r"서울특별시 (\S+구)")
            gdf["dong_name"] = gdf["adm_nm"].str.extract(r"\S+구 (\S+)$")

            merged = pd.merge(result_df, gdf[["dong_code", "gu_name", "dong_name"]], on="dong_code", how="left")
            merged["지역"] = merged["gu_name"] + " " + merged["dong_name"]

            top_df = merged.sort_values("final_score", ascending=False).head(20)[["지역", "final_score"]]
            top_df.reset_index(drop=True, inplace=True)
            top_df.index = top_df.index + 1

            st.dataframe(top_df, use_container_width=True, height=650)

        except Exception as e:
            st.warning(f"오류 발생: {e}")


# ---------------- 하단: 선택한 행정동 정보 ---------------- #
st.markdown("---")
st.markdown("#### 📍 선택한 행정동 정보")

if clicked_code:
    st.write(f"**자치구:** {clicked_gu_name}")
    st.write(f"**행정동:** {clicked_dong_name}")
    if final_score is not None:
        st.write(f"**점수:** {final_score:.2f}")
        # ✅ 순위 계산
        rank_df = result_df.sort_values(by="final_score", ascending=False).reset_index(drop=True)
        rank_df["rank"] = rank_df.index + 1

        selected_rank = rank_df.loc[rank_df["dong_code"] == clicked_code, "rank"].values
        if len(selected_rank) > 0:
            st.write(f"**순위:** {selected_rank[0]}위 / 총 {len(rank_df)}개 동")

        # ✅ 선택된 동의 전체 정보 추출
        detail_row = result_df[result_df["dong_code"] == clicked_code].iloc[0]

        # ✅ 출력 순서 정의
        ordered_columns = [
            "bus_stop", "subway_station", "store", "market", "library", "bank", "park",
            "hospital", "pharmacy", "school", "police_office", "cctv", "street_light",
            "safety_bell", "crime_rate", "real_estate"
        ]

        # ✅ 한글 매핑 정의
        COLUMN_KR = {
            "bus_stop": "버스정류장", "subway_station": "지하철역", "store": "편의시설", "market": "시장",
            "library": "도서관", "bank": "은행", "park": "공원", "pharmacy": "약국", "hospital": "병원",
            "school": "학교", "police_office": "경찰서", "cctv": "CCTV", "street_light": "스마트 가로등",
            "safety_bell": "비상벨", "crime_rate": "5대 범죄 발생률", "real_estate": "평당 실거래가"
        }

        exclude_columns = {"dong_code", "gu_code", "dong_name", "gu_name", "final_score"}
        already_printed = set()

        # ✅ 제목은 항목 출력 전에 공통으로
        st.markdown("**📊 인프라 및 통계 항목별 값**")

        # ✅ 좌우 2열로 분리
        col1, col2 = st.columns(2)
        half = len(ordered_columns) // 2
        col_list = [(col1, ordered_columns[:half]), (col2, ordered_columns[half:])]

        for column, cols in col_list:
            with column:
                for col in cols:
                    if col in exclude_columns or col in already_printed or col not in detail_row:
                        continue

                    value = detail_row[col]
                    if isinstance(value, pd.Series):
                        value = value.iloc[0]
                    if pd.isna(value):
                        continue

                    label = COLUMN_KR.get(col, col)
                    if isinstance(value, (int, float)):
                        if col == "real_estate":
                            st.write(f"- **{label}**: {int(value):,}원")
                        elif col == "crime_rate":
                            st.write(f"- **{label}**: {value:.1f}%")
                        else:
                            st.write(f"- **{label}**: {int(value)}개")
                    else:
                        st.write(f"- **{label}**: {value}")

                    already_printed.add(col)

    else:
        st.warning("해당 동의 점수를 찾을 수 없습니다.")
else:
    st.info("지도를 클릭해 행정동을 선택하세요.")
