import os
import sys
import pandas as pd
import re
from pyproj import Transformer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from geocoding.vworld_geocode import (
    coordinates_to_jibun_address,
    road_to_jibun_address,
)
from geocoding.admin_mapper import extract_gu_and_dong, get_gu_dong_codes

def load_pharmacy_csv(path="data/raw/pharmacy__raw.csv", sample_n=None):
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    if sample_n:
        df = df.sample(n=sample_n, random_state=42).reset_index(drop=True)
        print(f"[샘플 추출] {sample_n}건")
    else:
        print(f"[로드 완료] {path} - {len(df)}건")
    return df

def process_pharmacy_data(df):
    df = df[df['DTLSTATENM'] == '영업중']
    needed_cols = ['MGTNO', 'SITEWHLADDR', 'RDNWHLADDR', 'BPLCNM', 'X', 'Y']
    df = df[needed_cols]
    df = df.rename(columns={
        'MGTNO': 'pharmacy_id',
        'SITEWHLADDR': 'jibun_address',
        'RDNWHLADDR': 'road_address',
        'BPLCNM': 'pharmacy_name',
        'X': 'longitude',
        'Y': 'latitude'
    })
    print(f"[전처리 완료] {len(df)}건")
    return df

def tm_to_lonlat(x, y):
    try:
        transformer = Transformer.from_crs("epsg:5181", "epsg:4326", always_xy=True)
        return transformer.transform(x, y)
    except:
        return None, None

def convert_coords(df):
    coords = df.apply(lambda r: tm_to_lonlat(r['longitude'], r['latitude']), axis=1)
    df['lon'], df['lat'] = zip(*coords)
    return df

def clean_road_address(addr):
    if not isinstance(addr, str):
        return ""
    addr = re.sub(r"\([^)]*\)", "", addr)
    addr = re.sub(r"(지하\s*\d*층?|B\d+층?)", "", addr)
    addr = re.sub(r"\d+층", "", addr)
    addr = re.sub(r"\d+호", "", addr)
    addr = re.sub(r"\b\w*역\b", "", addr)
    addr = addr.replace(",", " ")
    addr = re.sub(r"\s+", " ", addr)
    return addr.strip()

def safe_jibun_address(row):
    lon, lat = row['lon'], row['lat']
    if lon and lat:
        addr = coordinates_to_jibun_address(lon, lat)
        if addr and "검색결과가 없습니다" not in addr:
            return addr
    if isinstance(row.get('jibun_address'), str) and row['jibun_address'].strip():
        return row['jibun_address'].strip()
    if isinstance(row.get('road_address'), str):
        cleaned = clean_road_address(row['road_address'])
        addr = road_to_jibun_address(cleaned)
        if addr:
            return addr
    print(f"[도로명주소 없음] ({lon}, {lat})")
    return None

def safe_extract_gu_dong(addr):
    try:
        return pd.Series(extract_gu_and_dong(addr)) if addr else pd.Series([None, None])
    except Exception as e:
        print(f"[❌ 법정동 추출 실패] {addr} → {e}")
        return pd.Series([None, None])

def safe_get_codes(row):
    try:
        result = get_gu_dong_codes(row['gu_name'], row['dong_name_from_jibun'])
        if result and len(result) == 3:
            return pd.Series(result)
        else:
            return pd.Series([None, None, None])
    except Exception as e:
        print(f"[❌ 코드 매핑 실패] {row['gu_name']}, {row['dong_name_from_jibun']} → {e}")
        return pd.Series([None, None, None])

def mapping_process(df):
    df = process_pharmacy_data(df)
    df = convert_coords(df)
    df['jibun_address_final'] = df.apply(safe_jibun_address, axis=1)

    # 지번주소 → (gu_name, dong_name_from_jibun)
    df[['gu_name', 'dong_name_from_jibun']] = df['jibun_address_final'].apply(safe_extract_gu_dong)

    # gu_name, dong_name_from_jibun → gu_code, dong_code, 행정동명
    df[['gu_code', 'dong_code', 'dong_name']] = df.apply(safe_get_codes, axis=1)

    return df

if __name__ == "__main__":
    df_raw = load_pharmacy_csv()  # 빠른 테스트용: sample_n=100
    df = mapping_process(df_raw)

    final_cols = [
        'gu_code', 'dong_code',
        'gu_name', 'dong_name',
        'jibun_address_final', 'road_address',
        'lon', 'lat',
        'pharmacy_id', 'pharmacy_name'
    ]
    df = df[final_cols]

    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/pharmacy__processed.csv"))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"[저장 완료] {output_path}")

    failures = df[df['dong_code'].isnull()]
    failures_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/pharmacy__failed.csv"))
    failures.to_csv(failures_path, index=False, encoding='utf-8-sig')
    print(f"[⚠️ 실패 저장 완료] {failures_path}")
