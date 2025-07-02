import requests
from dotenv import load_dotenv
import os

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

# 경도, 위도 순서 
def reverse_geocode(longitude: float, latitude: float) -> str:
    """
    위도/경도로 주소(도로명 주소)를 반환하는 함수 (카카오 API 사용)
    """
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    params = {"x": longitude, "y": latitude}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            address = data['documents'][0]['address']['address_name']
            return address
        else:
            print(f"[요청 실패] status_code={response.status_code}")
            return None
    except Exception as e:
        print(f"[예외 발생] {e}")
        return None
