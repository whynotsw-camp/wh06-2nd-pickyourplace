import pandas as pd
import os
import sys
from difflib import get_close_matches
from pyproj import Transformer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from geocoding.vworld_geocode import (
    road_address_to_coordinates,
    coordinates_to_jibun_address
)
from geocoding.admin_mapper import (
    extract_gu_and_dong,
    get_gu_dong_codes,
    smart_parse_gu_and_dong
)

# 매핑 테이블 불러오기
def load_dong_name_mapping(
    path="C:/Users/Admin/Desktop/pick-your-place/data/reference/KIKmix.20250701.xlsx"
) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    df = df[['시군구명', '동리명', '읍면동명']].dropna()
    df.columns = ['gu', 'legal_dong', 'admin_dong']
    return df

DONG_NAME_MAP = load_dong_name_mapping()

# 법정동명 → 행정동명 보정 함수
def map_legal_to_admin_dong(gu: str, legal_dong: str) -> str:
    if not gu or not legal_dong:
        return None
    sub = DONG_NAME_MAP[DONG_NAME_MAP['gu'] == gu]
    exact_match = sub[sub['legal_dong'] == legal_dong]
    if not exact_match.empty:
        return exact_match.iloc[0]['admin_dong']
    close = get_close_matches(legal_dong, sub['legal_dong'].tolist(), n=1, cutoff=0.8)
    if close:
        return sub[sub['legal_dong'] == close[0]].iloc[0]['admin_dong']
    return None

def load_store_csv(path: str = "data/raw/store__raw.csv") -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"[로드 완료] {path} - {len(df)}건")
    return df

def process_store_data(df: pd.DataFrame) -> pd.DataFrame:
    # 1) 영업중 필터링
    df = df[df['DTLSTATENM'] == '정상영업']

    needed_cols = ['MGTNO', 'SITEWHLADDR', 'RDNWHLADDR', 'BPLCNM', 'X', 'Y']
    df = df[[col for col in needed_cols if col in df.columns]]

    rename_map = {
        'MGTNO': 'store_code',
        'SITEWHLADDR': 'jibun_address',
        'RDNWHLADDR': 'road_address',
        'BPLCNM': 'store_name',
        'X': 'longitude',
        'Y': 'latitude'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df['jibun_address'] = df['jibun_address'].replace('', pd.NA)
    df.loc[df['longitude'].isna() | df['latitude'].isna(), ['longitude', 'latitude']] = [pd.NA, pd.NA]

    print(f"[INFO] 총 데이터 수: {len(df)}")
    print(f"[INFO] 지번주소 없는 데이터 수: {df['jibun_address'].isna().sum()}")
    print(f"[INFO] 좌표 없는 데이터 수: {df['longitude'].isna().sum()}")

    return df

transformer = Transformer.from_crs("epsg:5181", "epsg:4326", always_xy=True)
def tm_to_lonlat(x, y):
    try:
        return transformer.transform(x, y)
    except Exception as e:
        print(f"[좌표 변환 실패] X={x}, Y={y}, 에러: {e}")
        return None, None

def convert_coords(df: pd.DataFrame, x_col='longitude', y_col='latitude'):
    def safe_convert(row):
        try:
            return tm_to_lonlat(row[x_col], row[y_col])
        except Exception as e:
            print(f"[⚠️ 변환 실패] X: {row.get(x_col)}, Y: {row.get(y_col)} → {e}")
            return (None, None)
    coords = df.apply(safe_convert, axis=1)
    df['lon'], df['lat'] = zip(*coords)
    return df

def safe_jibun_address(row):
    try:
        raw_jibun = row.get('jibun_address', '')
        if isinstance(raw_jibun, str) and raw_jibun.strip():
            return raw_jibun.strip()
        
        road = row.get('road_address', '')
        if isinstance(road, str) and road.strip():
            lon, lat = road_address_to_coordinates(road)
            if lon is not None and lat is not None:
                addr = coordinates_to_jibun_address(lon, lat)
                if addr and '검색결과가 없습니다' not in addr:
                    return addr
        
        lon, lat = row.get('lon'), row.get('lat')
        if lon is not None and lat is not None and not (pd.isna(lon) or pd.isna(lat)):
            addr = coordinates_to_jibun_address(lon, lat)
            if addr and '검색결과가 없습니다' not in addr:
                return addr

        print(f"[⚠️ 지번주소 실패] 스토어: {row.get('store_name')}, 도로명: {road}")
        return None
    except Exception as e:
        print(f"[❌ 예외] 지번주소 변환 실패 - {e}")
        return None

def safe_extract_gu_dong(addr):
    try:
        gu, dong = extract_gu_and_dong(addr)
        if gu and dong:
            return pd.Series([gu, dong])
        gu2, dong2 = smart_parse_gu_and_dong(addr)
        return pd.Series([gu2, dong2])
    except Exception as e:
        print(f"[주소 파싱 실패] {addr} → {e}")
        return pd.Series([None, None])

# 여기서 보정 추가!
def safe_get_codes(row):
    gu = row['gu_name_from_jibun']
    dong = row['dong_name_from_jibun']
    try:
        return pd.Series(get_gu_dong_codes(gu, dong))
    except Exception as e:
        # 보정 시도
        admin_dong = map_legal_to_admin_dong(gu, dong)
        if admin_dong:
            try:
                return pd.Series(get_gu_dong_codes(gu, admin_dong))
            except Exception as e2:
                print(f"[행정동코드 보정 실패] gu={gu}, dong={dong} → admin_dong={admin_dong} - {e2}")
                return pd.Series([None, None])
        else:
            print(f"[법정→행정동 보정 실패] gu={gu}, dong={dong}")
            return pd.Series([None, None])

def mapping_process(df):
    df = process_store_data(df)
    df = convert_coords(df)
    df['jibun_address'] = df.apply(safe_jibun_address, axis=1)
    df[['gu_name_from_jibun', 'dong_name_from_jibun']] = df['jibun_address'].apply(safe_extract_gu_dong)
    df[['gu_code', 'dong_code']] = df.apply(safe_get_codes, axis=1)
    return df

if __name__ == "__main__":
    print("[실행] 시장 데이터를 전처리하고 저장합니다...")
    df_raw = load_store_csv()
    df = mapping_process(df_raw)

    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/store__processed.csv"))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {output_path}")

    failures = df[df['dong_code'].isnull()]
    failures_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/store__failed.csv"))
    failures.to_csv(failures_path, index=False, encoding='utf-8-sig')
    print(f"⚠️ 매핑 실패 데이터 저장 완료: {failures_path}")