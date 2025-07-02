import requests
import pandas as pd

# 1. 기본 정보 설정
API_KEY = '여기에_본인_API_KEY_입력'  # 예: '546846484774686938334d77666f4e'
SERVICE_NAME = 'SeoulPublicLibraryInfo'
BASE_URL = 'http://openapi.seoul.go.kr:8088'

START_INDEX = 1
END_INDEX = 1000  # 한 번에 가져올 최대 row 수

# 2. URL 생성 함수
def build_url(api_key, service, start, end):
    return f"{BASE_URL}/{api_key}/json/{service}/{start}/{end}"

# 3. API 호출 및 처리 함수
def fetch_library_info(start=1, end=1000):
    url = build_url(API_KEY, SERVICE_NAME, start, end)
    print(f"📡 요청 URL: {url}")
    
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API 호출 실패: {response.status_code}")

    data = response.json()
    records = data.get(SERVICE_NAME, {}).get('row', [])
    
    return pd.DataFrame(records)

# 4. 전체 데이터 가져오기 (예: 1000건 기준, 페이지 분할 필요 시 반복)
df = fetch_library_info(1, 1000)

# 5. 필요한 컬럼만 추출 (예시)
columns = ['LBRRY_NAME', 'ADRES', 'XCNTS', 'YDNTS']  # 도서관명, 주소, 경도, 위도
df = df[columns]

# 6. CSV로 저장
df.to_csv('data/raw/library_info.csv', index=False, encoding='utf-8-sig')
print("📁 저장 완료: data/raw/library_info.csv")
