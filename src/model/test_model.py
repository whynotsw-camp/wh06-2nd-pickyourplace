import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from model.rule_based_model import load_and_score_counts

user_input_scores = {
    "transport": 10,
    "living": 7,
    "safety": 5,
    "education": 3,
    "medical": 8,
    "housing": 2
}

df_result = load_and_score_counts(
    count_dir="data/processed_counts",
    processed_dir="data/processed",
    user_input_scores=user_input_scores
)

print(df_result.head(10))