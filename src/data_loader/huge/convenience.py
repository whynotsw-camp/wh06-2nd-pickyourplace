import pandas as pd
import os

# 📥 입력 & 출력 경로
INPUT_PATH = "서울시 휴게음식점 인허가 정보.csv"
OUTPUT_PATH = "convenience_filtered.csv"

# ❌ 제외할 업태 목록
exclude_types = ["전통찻집", "키즈카페", "철도역구내", "관광호텔", "유원지", "떡카페", "푸드트럭", "다방"]

# 📄 CSV 불러오기 (인코딩 주의)
df = pd.read_csv(INPUT_PATH, encoding_errors='ignore')

print(f"📋 전체 행 수: {len(df)}")

# 📌 필요한 컬럼만 선택 (있는 경우에만)
required_cols = ["사업장명", "지번주소", "업태구분명", "영업상태명"]
df = df[[col for col in required_cols if col in df.columns]].copy()

# 🧹 폐업 제거
df = df[df["영업상태명"]!= "폐업"]

# 🧹 제외할 업태 제거
df = df[~df["업태구분명"].isin(exclude_types)]

# 💾 저장
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"✅ 필터링 후 저장 완료: {OUTPUT_PATH} ({len(df)}건)")
