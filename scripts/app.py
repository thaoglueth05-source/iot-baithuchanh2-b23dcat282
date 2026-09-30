import pandas as pd
import plotly.express as px
import streamlit as st
from influxdb_client import InfluxDBClient

INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "dxrrru-xQrAhwpzRntGDQ4MwUF087rVWkYV5JSKRTGmjdt1grLPcju3tNx7m5Iw-ea8ZpTg1W9i2DF2D6S2wxg=="
INFLUX_ORG = "thaoglueth05@gmail.com"

st.set_page_config(page_title="IoT Monitoring Dashboard", layout="wide")
st.title("IoT Real-time & Data Preprocessing Dashboard")

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


@st.cache_data(ttl=5)
def load_data(bucket, measurement, start="-24h"):
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: {start})
        |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    try:
        df = client.query_api().query_data_frame(query, org=INFLUX_ORG)
        df = _as_one_frame(df)
    except Exception as e:
        st.warning(f"Loi query {bucket}/{measurement}: {e}")
        return pd.DataFrame()

    if df.empty or "_time" not in df.columns:
        return pd.DataFrame()

    df["_time"] = pd.to_datetime(df["_time"], utc=True)
    df = df.sort_values("_time")
    drop_cols = [c for c in ("result", "table") if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df

lookback = st.sidebar.selectbox("Khoang thoi gian", ["-1h", "-6h", "-24h", "0"], index=3)
flux_start = "0" if lookback == "0" else lookback

tab1, tab2 = st.tabs(["Real-time Raw Data", "Preprocessed Data"])

with tab1:
    st.subheader("Du lieu tho (iot_raw / sensor_telemetry)")
    raw_df = load_data("iot_raw", "sensor_telemetry", start=flux_start)

    if raw_df.empty:
        st.warning("Dang cho du lieu tho...")
    else:
        last = raw_df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nhiet do", f"{float(last.get('temperature', float('nan'))):.2f} C")
        c2.metric("Do am", f"{float(last.get('humidity', float('nan'))):.2f} %")
        c3.metric("Khoang cach", f"{float(last.get('distance_cm', float('nan'))):.2f} cm")
        c4.metric("So mau", str(len(raw_df)))

        y_cols = [c for c in ("temperature", "humidity") if c in raw_df.columns]
        if y_cols:
            st.plotly_chart(
                px.line(raw_df, x="_time", y=y_cols, title="Nhiet do & Do am tho"),
                use_container_width=True,
            )
        if "distance_cm" in raw_df.columns:
            st.plotly_chart(
                px.line(raw_df, x="_time", y="distance_cm", title="Khoang cach"),
                use_container_width=True,
            )
        st.dataframe(raw_df.tail(15), use_container_width=True)

with tab2:
    st.subheader("Du lieu da tien xu ly (iot_cleaned / sensor_cleaned)")
    cleaned_df = load_data("iot_cleaned", "sensor_cleaned", start=flux_start)

    if cleaned_df.empty:
        st.info("Chua co du lieu cleaned. Chay: python preprocess.py")
    else:
        y_clean = [c for c in ("temperature", "temp_rolling_avg") if c in cleaned_df.columns]
        if y_clean:
            st.plotly_chart(
                px.line(cleaned_df, x="_time", y=y_clean, title="Nhiet do vs rolling mean"),
                use_container_width=True,
            )
        st.dataframe(cleaned_df.tail(10), use_container_width=True)

if st.sidebar.button("Tai lai"):
    st.cache_data.clear()
    st.rerun()