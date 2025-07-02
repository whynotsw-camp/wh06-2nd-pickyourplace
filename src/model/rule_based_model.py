# rule_based_model.py 
import os
import pandas as pd
import numpy as np

category_mapping = {
    "transport": ["bus_stop", "subway_station"],
    "living": ["store", "convenience", "market", "library", "bank", "park"],
    "medical": ["pharmacy", "hospital"],
    "safety": ["police_office", "cctv", "street_light", "safety_bell", "crime_rate"],
    "education": ["school"],
    "housing": ["real_estate"]
}

raw_weights = {
    "transport": 56.0,
    "living": 37.9 + 24.7,
    "medical": 29.7,
    "safety": 44.2,
    "education": 16.7,
    "housing": 33.1
}

reverse_features = {'crime_rate', 'real_estate'}
density_features = {'cctv', 'street_light', 'safety_bell', 'police_office', 'bus_stop', 'subway_station'}

def log_scale(series):
    return np.log1p(series)

def calculate_weights(user_scores):
    weighted_scores = {k: raw_weights.get(k, 0) * user_scores.get(k, 0) for k in raw_weights}
    total = sum(weighted_scores.values())
    if total == 0:
        return raw_weights
    return {k: v / total for k, v in weighted_scores.items()}

def compute_score(df, feature_to_category, weights):
    for feature, category in feature_to_category.items():
        if feature not in df.columns:
            continue
        values = log_scale(df[feature])
        df[category] = df.get(category, 0) + values

    for category in weights:
        if category not in df:
            df[category] = 0.0

        min_val = df[category].min()
        max_val = df[category].max()
        if max_val > min_val:
            norm = (df[category] - min_val) / (max_val - min_val)
            if any(f in reverse_features for f, cat in feature_to_category.items() if cat == category):
                norm = 1 - norm
            df[category + '_norm'] = norm
        else:
            df[category + '_norm'] = 0.5

    df['final_score'] = sum(df[cat + '_norm'] * weights[cat] for cat in weights)
    df['final_score'] = (df['final_score'] * 100).round(2)

    # # 재정규화 부분
    # ## 💡 1. 최종 점수 계산
    # df['final_score'] = sum(df[cat + '_norm'] * weights[cat] for cat in weights)

    # ## ✅ 2. 점수를 0~100으로 재정규화
    # min_score = df['final_score'].min()
    # max_score = df['final_score'].max()
    # if max_score > min_score:
    #     df['final_score'] = ((df['final_score'] - min_score) / (max_score - min_score)) * 100
    # else:
    #     df['final_score'] = 50

    # ## 💡 3. 소수점 정리
    # df['final_score'] = df['final_score'].round(2)

    return df


def load_and_score_counts(count_dir, processed_dir, user_input_scores):
    feature_to_category = {feature: cat for cat, features in category_mapping.items() for feature in features}
    df_merged = None

    for file in os.listdir(count_dir):
        if not file.endswith("__counts.csv") or file == "cctv_gu__counts.csv":
            continue

        file_path = os.path.join(count_dir, file)
        feature = file.replace("__counts.csv", "")
        df = pd.read_csv(file_path, dtype={'dong_code': str, 'gu_code': str})

        if 'counts' not in df.columns:
            print(f"[스킵] '{file}'에는 'counts' 컬럼이 없습니다.")
            continue

        print(f"[로드] '{file}' → feature: {feature}, shape: {df.shape}")

        df = df.rename(columns={'counts': feature})
        df = df[['gu_code', 'dong_code', feature]].drop_duplicates(subset=['gu_code', 'dong_code'])

        if df_merged is None:
            df_merged = df
        else:
            df_merged = pd.merge(df_merged, df, on=['gu_code', 'dong_code'], how='outer')

    if df_merged is None:
        return pd.DataFrame()

    # crime_rate 파일 추가 병합
    crime_file = os.path.join(processed_dir, "crime_rate__processed.csv")
    if os.path.exists(crime_file):
        df_crime = pd.read_csv(crime_file, dtype={'gu_code': str})
        df_crime = df_crime.rename(columns={'total_rate': 'crime_rate'})
        df_crime = df_crime[['gu_code', 'crime_rate']].drop_duplicates('gu_code')
        df_merged = pd.merge(df_merged, df_crime, on='gu_code', how='left')

    # real_estate 파일 추가 병합
    real_estate_file = os.path.join(processed_dir, "real_estate_dong_avg__processed.csv")
    if os.path.exists(real_estate_file):
        df_real = pd.read_csv(real_estate_file, dtype={'dong_code': str})
        df_real = df_real.rename(columns={'평당금액(원)': 'real_estate'})
        df_real = df_real[['dong_code', 'real_estate']].drop_duplicates('dong_code')
        df_merged = pd.merge(df_merged, df_real, on='dong_code', how='left')

    # ✅ 중복 컬럼 제거
    df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]
    df_merged = df_merged.fillna(0)
    print("[DEBUG] 병합된 컬럼 리스트:", df_merged.columns.tolist())

    weights = calculate_weights(user_input_scores)
    df_scored = compute_score(df_merged, feature_to_category, weights)

    # return df_scored[['gu_code', 'dong_code', 'final_score']].sort_values(by='final_score', ascending=False)

    feature_cols = list(feature_to_category.keys()) + ['crime_rate', 'real_estate']
    keep_cols = ['gu_code', 'dong_code', 'final_score'] + [col for col in feature_cols if col in df_scored.columns]
    return df_scored[keep_cols].sort_values(by='final_score', ascending=False)


__all__ = ['load_and_score_counts', 'category_mapping', 'raw_weights']
