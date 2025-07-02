import geopandas as gpd
import os

"""
이 스크립트는 전국 단위의 행정동 GeoJSON 파일에서 '서울특별시'에 해당하는 데이터만 필터링하여,
geometry를 단순화한 뒤 별도의 파일로 저장합니다.
지도 시각화 성능 개선 및 서울시 데이터만 사용하는 프로젝트에 최적화된 전처리 작업입니다.
"""

# 경로 설정
INPUT_PATH = "data/reference/HangJeongDong_ver20250401.geojson"
OUTPUT_PATH = "data/reference/Seoul_HangJeongDong.geojson"

# GeoJSON 파일 읽기
gdf = gpd.read_file(INPUT_PATH)

# 서울특별시만 필터링
seoul_gdf = gdf[gdf["sidonm"] == "서울특별시"].copy()

"""
geometry 단순화는 시각화 성능을 향상시키기 위해 꼭 필요한 과정입니다.
단순화 인자값(0.0003)은 지도의 외형을 유지하면서 렌더링 속도를 빠르게 합니다.
"""
seoul_gdf["geometry"] = seoul_gdf["geometry"].simplify(0.0003)

# GeoJSON 저장
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
seoul_gdf.to_file(OUTPUT_PATH, driver="GeoJSON")

print(f"저장 완료: {OUTPUT_PATH}")
