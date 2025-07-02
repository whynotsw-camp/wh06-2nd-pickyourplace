import folium
from folium import Choropleth, GeoJson, GeoJsonTooltip
import json

def draw_choropleth(
    geojson_path,
    data_df,
    value_column="final_score",
    key_column="dong_code"
):
    """
    GeoJSON과 데이터프레임을 이용한 행정동 단위 Choropleth 시각화 함수

    Parameters:
    - geojson_path (str): GeoJSON 파일 경로 (adm_cd2 포함)
    - data_df (pd.DataFrame): 시각화 대상 데이터프레임 (dong_code, final_score 포함)
    - value_column (str): 색상값으로 사용할 컬럼명 (기본값: 'final_score')
    - key_column (str): GeoJSON의 adm_cd2와 매핑할 데이터프레임 키 컬럼

    Returns:
    - folium.Map 객체
    """

    # 지도 초기화
    m = folium.Map(
        location=[37.5642135, 127.0016985],  # 서울 중심 좌표
        zoom_start=11,
        control_scale=True
    )

    # GeoJSON 로드
    with open(geojson_path, encoding="utf-8") as f:
        geojson_data = json.load(f)

    # key 컬럼 문자열 처리
    data_df = data_df.copy()
    data_df[key_column] = data_df[key_column].astype(str)

    # 단계구분도 레이어 추가
    Choropleth(
        geo_data=geojson_data,
        data=data_df,
        columns=[key_column, value_column],
        key_on="feature.properties.adm_cd2",
        fill_color="Blues",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="추천 점수"
    ).add_to(m)

    # 툴팁 표시
    GeoJson(
        geojson_data,
        tooltip=GeoJsonTooltip(
            fields=["adm_nm", "sggnm"],  # 예: 사직동, 종로구
            aliases=["행정동", "자치구"],
            localize=True,
            sticky=False
        ),
        style_function=lambda x: {
            "fillOpacity": 0,
            "color": "black",
            "weight": 0.3
        },
        highlight_function=lambda x: {
            'color': 'blue',
            'weight': 3,
            'fillOpacity': 0.3
        }
    ).add_to(m)

    return m
