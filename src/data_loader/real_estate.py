import pandas as pd
import os


"""CSV 파일에서 필요한 컬럼만 추출"""
def load_real_estate_csv(filename):
    current_dir = os.path.dirname(__file__)  # 현재 스크립트 위치
    input_dir = os.path.abspath(os.path.join(current_dir, "../../data/raw"))
    input_file = os.path.join(input_dir, filename)

    df = pd.read_csv(input_file, encoding="cp949")

    # 필요한 컬럼만 추출
    selected_columns = df[['자치구명', '법정동명', '건물면적(㎡)', '물건금액(만원)']].dropna().reset_index(drop=True)
    return selected_columns


"""CSV 저장 함수"""
def save_to_csv(data, filename):
    current_dir = os.path.dirname(__file__)
    output_dir = os.path.abspath(os.path.join(current_dir, "../../data/raw"))
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, filename)
    data.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"CSV 저장 완료: {output_file}")


if __name__ == "__main__":
    try:
        extracted_data = load_real_estate_csv("서울시 부동산 실거래가 정보.csv")
        save_to_csv(extracted_data, "real_estate__raw.csv")

    except Exception as e:
        print(f"전체 처리 중 에러 발생: {e}")
