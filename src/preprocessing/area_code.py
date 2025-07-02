# src/preprocessing/area_code.py

# 자치구명, 행정동명은 이미 존재. 코드 매핑 하는 함수
# 현재 컬럼 : gu_name,dong_name,area_km2,구성비 (%)
# 전처리 후 컬럼 : gu_code,dong_code,gu_name,dong_name,area_km2

import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from geocoding.admin_mapper import get_gu_dong_codes

def load_area_data(path="src/model/area_km2.csv"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[❌ 파일 없음] {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"[로드 완료] {len(df)}건")
    return df

def map_codes(df):
    def get_codes(row):
        try:
            gu_code, dong_code, _ = get_gu_dong_codes(row['gu_name'], row['dong_name'])
            return pd.Series([gu_code, dong_code])
        except Exception as e:
            print(f"[⚠️ 코드 매핑 실패] {row['gu_name']}, {row['dong_name']} → {e}")
            return pd.Series([None, None])
    
    df[['gu_code', 'dong_code']] = df.apply(get_codes, axis=1)
    return df

if __name__ == "__main__":
    input_path = "src/model/area_km2.csv"
    output_path = "src/model/area_km2__processed.csv"

    df = load_area_data(input_path)
    df = map_codes(df)

    # 구성비(%) 컬럼 제거 (선택사항)
    if '구성비 (%)' in df.columns:
        df = df.drop(columns=['구성비 (%)'])

    # 컬럼 순서 정리
    final_columns = ['gu_code', 'dong_code', 'gu_name', 'dong_name', 'area_km2']
    df = df[final_columns]

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[저장 완료] {output_path}")
