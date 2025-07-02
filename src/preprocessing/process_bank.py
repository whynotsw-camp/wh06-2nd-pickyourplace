import sys 
import os
import pandas as pd
import re

# 행정동 코드 파일 경로
DONG_CODE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/reference/KIKcd_H.20250701.xlsx"))

# 현재 파일 기준으로 상위 폴더 src 추가 (data_loader 모듈 import 위해)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_loader.bank_csv import load_banks_data
from geocoding.admin_mapper import get_gu_dong_codes

def add_je_to_dong_name(dong_name: str) -> str:
    return re.sub(r'(\D)(\d+)(동)$', r'\1제\2\3', dong_name)

def get_codes_by_admin_dong(gu: str, dong: str, dong_df: pd.DataFrame) -> tuple:
    code_row = dong_df[
        (dong_df['시군구명'] == gu) & (dong_df['읍면동명'] == dong)
    ]
    if not code_row.empty:
        dong_code = code_row.iloc[0]["행정동코드"]
        gu_code = dong_code[:5]
        return gu_code, dong_code
    else:
        print(f"[행정동 코드 조회 실패] gu='{gu}', dong='{dong}'")
        print(f"  → dong_df 읍면동명 샘플: {dong_df['읍면동명'].unique()[:20]}")
        return None, None

def main():
    df = load_banks_data()

    # 첫 2개 행 제거
    df = df.iloc[2:].reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    df = df.drop(columns=['동별(1)'])
    df.rename(columns={'동별(2)': 'gu_name', '동별(3)': 'dong_name'}, inplace=True)

    # 은행 수 계산
    counts = df.iloc[:, 2:].apply(pd.to_numeric, errors='coerce').sum(axis=1).astype(int)
    df = df.iloc[:, :2].copy()
    df['count'] = counts

    dong_df = pd.read_excel(DONG_CODE_PATH, dtype=str)

    df['dong_name'] = df['dong_name'].apply(add_je_to_dong_name)

    gu_codes = []
    dong_codes = []

    for idx, row in df.iterrows():
        gu = row['gu_name'].strip()
        dong = row['dong_name'].strip()
        gu_code, dong_code = get_codes_by_admin_dong(gu, dong, dong_df)
        gu_codes.append(gu_code if gu_code else '')
        dong_codes.append(dong_code if dong_code else '')

    df['gu_code'] = gu_codes
    df['dong_code'] = dong_codes

    # 저장: 전체 데이터
    processed_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/bank__processed.csv"))
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {processed_path}")

    # 저장: counts만 따로
    count_df = df[['gu_code', 'dong_code', 'gu_name', 'dong_name', 'count']].copy()
    count_df.rename(columns={'count': 'counts'}, inplace=True)

    counts_output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed_counts/bank__counts.csv"))
    count_df.to_csv(counts_output_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {counts_output_path}")

if __name__ == "__main__":
    main()