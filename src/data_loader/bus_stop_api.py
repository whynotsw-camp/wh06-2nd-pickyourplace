from dotenv import load_dotenv
import os
import requests
import pandas as pd

load_dotenv()

try: 
    API_KEY = os.getenv("SEOUL_API_KEY")
    if API_KEY is None:
        raise ValueError("'.env' 파일에 'SEOUL_API_KEY'가 정의되어 있지 않습니다.")
except Exception as e:
    print(f"[환경 변수 오류] {e}")
    API_KEY = None  # 방어적으로 None 설정

def fetch_bus_stop_data(start: int = 1, end: int = 11290) -> list:
    """
    서울시 버스정류소 위치 데이터를 JSON으로 수집하여 리스트 형태로 반환
    """
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/busStopLocationXyInfo/{start}/{end}/"
    response = requests.get(url)

    print(f"[DEBUG] 요청 URL: {url}")
    print(f"[DEBUG] 응답 코드: {response.status_code}")

    if response.status_code == 200:
        try:
            data = response.json()
            if 'busStopLocationXyInfo' not in data:
                print("[❌ 오류] 'busStopLocationXyInfo' 키가 응답에 없습니다.")
                print("[응답 전체 내용]", data)
                return []
            if 'row' not in data['busStopLocationXyInfo']:
                print("[❌ 오류] 'row' 데이터가 응답에 없습니다.")
                print("[응답 전체 내용]", data)
                return []

            print("[✅ 성공] 데이터 파싱 성공")
            return data['busStopLocationXyInfo']['row']

        except (ValueError, KeyError) as e:
            print(f"[❌ 예외 발생] JSON 파싱 실패: {e}")
            print("응답 내용:", response.text)
            return []
    elif response.status_code == 400:
        print("[❌ 잘못된 요청] 파라미터 또는 인증 키 오류")
    elif response.status_code == 401:
        print("[❌ 인증 실패] API 키가 유효하지 않음")
    elif response.status_code == 500:
        print("[❌ 서버 오류] 서울시 OpenAPI 서버 문제")
    else:
        print(f"[❌ 기타 오류] 응답 코드: {response.status_code}")

    return []


def fetch_bus_stop_data_all() -> list:
    """
    서울시 버스정류장 데이터를 1000건 단위로 끊어서 전부 가져옴
    """
    all_data = []
    start = 1
    step = 1000
    total = 11290  # 전체 정류장 수

    while start <= total:
        end = min(start + step - 1, total)
        print(f"[INFO] 요청 구간: {start} ~ {end}")
        chunk = fetch_bus_stop_data(start, end)
        all_data.extend(chunk)
        start += step

    return all_data


def save_to_csv(data: list, output_path: str = "data/raw/bus_stop__raw.csv"):
    """
    수집된 데이터를 CSV 파일로 저장
    """
    if not data:
        print("[❌ 저장 실패] 저장할 데이터가 없습니다.")
        return

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[✅ 저장 완료] CSV 파일이 저장되었습니다 → {output_path}")


# --- 실행용 테스트 코드 ---
if __name__ == "__main__":
    print("[TEST] 서울시 버스정류장 데이터를 수집하고 CSV로 저장합니다...")

    bus_data = fetch_bus_stop_data_all()
    save_to_csv(bus_data)
