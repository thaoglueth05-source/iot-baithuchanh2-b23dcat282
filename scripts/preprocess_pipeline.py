import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "dxrrru-xQrAhwpzRntGDQ4MwUF087rVWkYV5JSKRTGmjdt1grLPcju3tNx7m5Iw-ea8ZpTg1W9i2DF2D6S2wxg=="
INFLUX_ORG = "thaoglueth05@gmail.com"
RAW_BUCKET = "iot_raw"
CLEANED_BUCKET = "iot_cleaned"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)

def _as_one_frame(df):
    if isinstance(df, list):
        frames = [x for x in df if x is not None and not getattr(x, "empty", True)]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
    if df is None:
        return pd.DataFrame()
    return df

def fetch_raw_data():
    query = f'''
    from(bucket: "{RAW_BUCKET}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "sensor_telemetry")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    try:
        df = client.query_api().query_data_frame(query, org=INFLUX_ORG)
        df = _as_one_frame(df)
        print("Query raw: rows =", 0 if df.empty else len(df), "| columns =", list(df.columns))
        if df.empty or "_time" not in df.columns:
            return pd.DataFrame()
        df["_time"] = pd.to_datetime(df["_time"], utc=True)
        df = df.set_index("_time").sort_index()
        drop_cols = [c for c in ("result", "table") if c in df.columns]
        if drop_cols:
            df = df.drop(columns=drop_cols)
        return df
    except Exception as e:
        print(f"Loi truy van InfluxDB: {e}")
        return pd.DataFrame()


def clean_and_preprocess(df):
    if df.empty:
        return df

    features = ["temperature", "humidity", "distance_cm"]
    valid_features = [col for col in features if col in df.columns]
    if not valid_features:
        print("Khong thay cot cam bien. Cot hien co:", list(df.columns))
        return pd.DataFrame()

    work = df[valid_features].astype(float)
    work = work.interpolate(method="time").ffill().bfill()

    for col in valid_features:
        q1 = work[col].quantile(0.25)
        q3 = work[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            work[col] = np.clip(work[col], q1 - 1.5 * iqr, q3 + 1.5 * iqr)

    resampled = work.resample("1min").mean().dropna()
    if resampled.empty:
        print("Resample 1Min rong, thu 15s...")
        resampled = work.resample("15s").mean().dropna()
    if resampled.empty:
        resampled = work.copy()

    if "temperature" in resampled.columns:
        resampled["temp_rolling_avg"] = (
            resampled["temperature"].rolling(window=3, min_periods=1).mean()
        )
        resampled["temp_delta"] = resampled["temperature"].diff().fillna(0.0)

    mean = resampled[valid_features].mean()
    std = resampled[valid_features].std(ddof=0).replace(0, 1.0)
    for col in valid_features:
        resampled[f"{col}_scaled"] = (resampled[col] - mean[col]) / std[col]

    return resampled


def save_cleaned_data(df):
    if df.empty:
        print("Khong co du lieu de luu!")
        return

    write_api = client.write_api(write_options=SYNCHRONOUS)
    n = 0
    for timestamp, row in df.iterrows():
        point = Point("sensor_cleaned").tag("device_id", "esp32_01").time(timestamp)
        for col in df.columns:
            if pd.notna(row[col]):
                point.field(col, float(row[col]))
        write_api.write(bucket=CLEANED_BUCKET, org=INFLUX_ORG, record=point)
        n += 1
    print(f"--> Da ghi {n} dong vao bucket '{CLEANED_BUCKET}'.")


if __name__ == "__main__":
    raw_df = fetch_raw_data()
    if raw_df.empty:
        print("No raw data found in 'iot_raw'!")
        print("Kiem tra INFLUX_ORG phai la thaoglueth05@gmail.com")
    else:
        print("Raw rows:", len(raw_df))
        cleaned_df = clean_and_preprocess(raw_df)
        print("Clean rows:", len(cleaned_df))
        print(cleaned_df.head())
        save_cleaned_data(cleaned_df)
    client.close()