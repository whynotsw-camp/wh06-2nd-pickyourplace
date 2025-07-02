import pandas as pd
import os

def load_centers_data():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/center__raw.xlsx"))
    return pd.read_excel(path)