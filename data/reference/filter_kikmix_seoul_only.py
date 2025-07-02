import pandas as pd
import os

# 📁 입력/출력 경로 설정
INPUT_PATH = "data/reference/KIKmix.20250701.xlsx"
OUTPUT_PATH = "data/reference/KIKmix_seoul.20250701.csv"

# 📥 엑셀 파일 읽기
df = pd.read_excel(INPUT_PATH, dtype=str)

# 🧹 컬럼명 정리
df = df.rename(columns={
    "시도명": "sido_name",       # 시도명 컬럼이 있는 경우
    "시군구명": "gu_name",
    "동리명": "legal_dong",
    "읍면동명": "admin_dong",
    "행정동코드": "admin_code"
})

# 🌆 서울특별시만 필터링
seoul_df = df[df["sido_name"] == "서울특별시"].dropna(subset=["gu_name", "legal_dong", "admin_dong", "admin_code"])

# 💾 저장
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
seoul_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"✅ 서울 데이터 저장 완료: {OUTPUT_PATH} (총 {len(seoul_df)}행)")
