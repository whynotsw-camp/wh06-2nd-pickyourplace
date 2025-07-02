import requests
from dotenv import load_dotenv
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm       
import math

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', '안전비상벨위치정보.xlsx'))
print("절대경로로 확인:", file_path)

df = pd.read_excel(file_path)
df = df[["소재지지번주소"]] # 소재지지번주소만 가져옴"

result_df = pd.DataFrame(df)
output_path = "../../data/raw/safety_bell__raw.csv"
output_path_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), output_path))
output_dir = os.path.dirname(output_path_abs)

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

result_df.to_csv(output_path_abs, index=False, encoding="utf-8-sig")
print("저장 완료", output_path_abs)


print("저장 완료", output_path)
