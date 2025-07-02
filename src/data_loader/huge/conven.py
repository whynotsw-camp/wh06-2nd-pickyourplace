import pandas as pd

# CSV 파일 경로
INPUT_PATH = "서울시 휴게음식점 인허가 정보.csv"

# CSV 불러오기 (인코딩 자동 처리, 오류 무시)
df = pd.read_csv(INPUT_PATH, encoding_errors='ignore')

# 컬럼명 좌우 공백 제거
df.columns = df.columns.str.strip()

# 컬럼명 리스트 출력
print("📋 CSV 컬럼 목록:")
for col in df.columns:
    print("-", col)
