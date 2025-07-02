import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader.center_csv import load_centers_data
from geocoding.vworld_geocode import road_address_to_coordinates, coordinates_to_jibun_address
from geocoding.admin_mapper import extract_gu_and_dong, get_gu_dong_codes, smart_parse_gu_and_dong

# 동 이름 보정 매핑
dong_alias_map = {
    "돈암1동": "돈암제1동",
    "안암동": "안암동2가",
    "월곡1동": "월곡제1동",
    "공릉1동": "공릉제1동",
    "발산1동": "발산제1동",
    "신길6동": "신길제6동",
    "대림3동": "대림제3동",
    "노량진1동": "노량진제1동",
    "신대방2동": "신대방제2동"
}

def correct_dong_name(dong: str) -> str:
    if not isinstance(dong, str):
        return dong
    return dong_alias_map.get(dong.strip(), dong.strip())

def rename_columns(df):
    needed_cols = ['도로명 주소', '행정 구']
    df = df[needed_cols].copy()
    return df.rename(columns={
        '도로명 주소': 'road_address',
        '행정 구': 'gu_name',
    })

def mapping_process(df):
    df = rename_columns(df)

    # 1) 도로명 주소 → (경도, 위도)
    coords = df['road_address'].apply(lambda addr: road_address_to_coordinates(addr))
    df['lon'], df['lat'] = zip(*coords)

    # 2) 위도, 경도 → 지번 주소
    df['jibun_address'] = df.apply(
        lambda r: coordinates_to_jibun_address(r['lon'], r['lat']) if pd.notna(r['lon']) and pd.notna(r['lat']) else None,
        axis=1
    )

    # 3) 지번 주소 → 자치구명, 법정동명
    extracted = df['jibun_address'].apply(lambda addr: pd.Series(extract_gu_and_dong(addr)) if pd.notna(addr) else pd.Series([None, None]))
    df['dong_name'] = extracted[1].apply(correct_dong_name)  # 동 이름만 추출 + 보정

    # 4) 자치구명, 보정된 동 이름 → 코드
    df[['gu_code', 'dong_code']] = df.apply(
        lambda r: pd.Series(get_gu_dong_codes(r['gu_name'], r['dong_name'])) 
        if pd.notna(r['gu_name']) and pd.notna(r['dong_name']) else pd.Series([None, None]),
        axis=1
    )

    return df

if __name__ == "__main__":
    df = load_centers_data()
    df = mapping_process(df)

    # 저장
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/center__processed.csv"))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {output_path}")

    # 실패한 행 저장
    failures = df[df['dong_code'].isnull()]
    failures_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/center__failed.csv"))
    failures.to_csv(failures_path, index=False, encoding='utf-8-sig')
    print(f"⚠️ 매핑 실패 데이터 저장 완료: {failures_path}")