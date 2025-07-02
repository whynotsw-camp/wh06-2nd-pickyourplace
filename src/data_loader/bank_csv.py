import pandas as pd
import os

def load_banks_data():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/bank__raw.csv"))
    return pd.read_csv(path)