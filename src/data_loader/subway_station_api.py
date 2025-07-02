import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TDATA_SUBWAY_API_KEY")
url = f"https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/TaimsKsccDvSubwayStationGeom/1.0?apikey={API_KEY}"

# 요청
response = requests.get(url)

if response.status_code == 200:
    try:
        data = response.json()

        # 리스트 바로 DataFrame으로 변환
        df = pd.DataFrame(data)

        # 컬럼명 직관적으로 리네이밍 (선택)
        df.rename(columns={
            "outStnNum": "station_id",
            "stnKrNm": "station_name",
            "lineNm": "line_name",
            "convX": "longitude",
            "convY": "latitude"
        }, inplace=True)

        # 저장
        os.makedirs("data/raw", exist_ok=True)
        df.to_csv("data/raw/subway_station__raw.csv", index=False, encoding="utf-8-sig")
        print(f"[완료] 총 {len(df)}개 지하철역 데이터 저장 완료")

    except Exception as e:
        print(f"[예외 발생] JSON 파싱 오류: {e}")
else:
    print(f"[오류] 응답 실패: {response.status_code} / {response.text}")
