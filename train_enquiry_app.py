"""
Train Enquiry App
------------------
A Streamlit app for looking up trains and stations, and exploring the
route/traffic analysis from the accompanying notebook (train_schedule_analysis.ipynb).

Run with:
    streamlit run train_enquiry_app.py

Expects "Dataset1.csv" in the same folder.
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Train Enquiry", page_icon="🚆", layout="wide")

DATA_PATH = "Dataset1.csv"


# ----------------------------------------------------------------------
# Data loading & preparation
# ----------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.sort_values(["Train_No", "SN"]).reset_index(drop=True)

    # Parse times (keep original strings for display, parsed for math)
    df["Arrival_dt"] = pd.to_datetime(df["Arrival_time"], format="%H:%M:%S", errors="coerce")
    df["Departure_dt"] = pd.to_datetime(df["Departure_Time"], format="%H:%M:%S", errors="coerce")
    return df


@st.cache_data
def build_train_routes(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("Train_No")

    routes = pd.DataFrame({
        "Start_Station": grouped["Station_Name"].first(),
        "End_Station": grouped["Station_Name"].last(),
        "Stops": grouped.size(),
        "Total_Distance": grouped["Distance"].max(),
    }).reset_index()

    def calc_duration(train):
        start = train["Departure_dt"].iloc[0]
        end = train["Arrival_dt"].iloc[-1]
        if pd.isna(start) or pd.isna(end):
            return pd.NaT
        if end <= start:
            end = end + pd.Timedelta(days=1)
        return end - start

    duration = grouped.apply(calc_duration).reset_index(name="Journey_Duration")
    routes = routes.merge(duration, on="Train_No", how="left")
    routes["Journey_Hours"] = routes["Journey_Duration"].dt.total_seconds() / 3600

    def classify_route(hours):
        if pd.isna(hours):
            return "Unknown"
        if hours <= 3:
            return "Short"
        elif hours <= 8:
            return "Medium"
        return "Long"

    routes["Route_Type"] = routes["Journey_Hours"].apply(classify_route)
    return routes


@st.cache_data
def build_station_frequency(df: pd.DataFrame) -> pd.DataFrame:
    freq = (
        df.groupby("Station_Name")["Train_No"]
        .nunique()
        .reset_index(name="Train_Frequency")
        .sort_values("Train_Frequency", ascending=False)
    )
    return freq


def format_timedelta(td):
    if pd.isna(td):
        return "N/A"
    total_minutes = int(td.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


df = load_data(DATA_PATH)
train_routes = build_train_routes(df)
station_frequency = build_station_frequency(df)

# ----------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------
st.sidebar.title("🚆 Train Enquiry")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Train Lookup", "Station Lookup", "Route Analysis"],
)

# ----------------------------------------------------------------------
# Overview
# ----------------------------------------------------------------------
if page == "Overview":
    st.title("Train Schedule Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", f"{len(df):,}")
    col2.metric("Unique Trains", f"{df['Train_No'].nunique():,}")
    col3.metric("Unique Stations", f"{df['Station_Name'].nunique():,}")
    col4.metric("Duplicate Rows", f"{df.duplicated().sum():,}")

    st.subheader("Route Type Distribution")
    route_counts = train_routes["Route_Type"].value_counts()
    st.bar_chart(route_counts)

    st.subheader("Sample Data")
    st.dataframe(df.drop(columns=["Arrival_dt", "Departure_dt"]).head(20), use_container_width=True)

# ----------------------------------------------------------------------
# Train Lookup
# ----------------------------------------------------------------------
elif page == "Train Lookup":
    st.title("Train Lookup")

    train_numbers = sorted(df["Train_No"].unique())
    train_no = st.selectbox("Select or type a Train Number", train_numbers)

    if train_no:
        train_df = df[df["Train_No"] == train_no].sort_values("SN")
        route_info = train_routes[train_routes["Train_No"] == train_no].iloc[0]

        st.subheader(f"Train {train_no}: {route_info['Start_Station']} → {route_info['End_Station']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stops", int(route_info["Stops"]))
        c2.metric("Total Distance", f"{int(route_info['Total_Distance'])} km")
        c3.metric("Journey Duration", format_timedelta(route_info["Journey_Duration"]))
        c4.metric("Route Type", route_info["Route_Type"])

        st.subheader("Full Schedule")
        display_cols = [
            "SN", "Station_Code", "Station_Name", "Arrival_time",
            "Departure_Time", "Distance", "1A", "2A", "3A", "SL",
        ]
        st.dataframe(train_df[display_cols], use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Station Lookup
# ----------------------------------------------------------------------
elif page == "Station Lookup":
    st.title("Station Lookup")

    stations = sorted(df["Station_Name"].unique())
    station = st.selectbox("Select or type a Station Name", stations)

    if station:
        station_df = df[df["Station_Name"] == station].sort_values("Departure_dt")
        st.subheader(f"Trains passing through {station}")
        st.metric("Number of Trains", station_df["Train_No"].nunique())

        display_cols = [
            "Train_No", "SN", "Arrival_time", "Departure_Time",
            "Distance", "1A", "2A", "3A", "SL",
        ]
        st.dataframe(station_df[display_cols], use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Route Analysis
# ----------------------------------------------------------------------
elif page == "Route Analysis":
    st.title("Route & Traffic Analysis")

    st.subheader("Average Journey Duration by Route Type")
    avg_duration = (
        train_routes[train_routes["Route_Type"] != "Unknown"]
        .groupby("Route_Type")["Journey_Hours"]
        .mean()
        .reset_index()
    )
    st.bar_chart(avg_duration.set_index("Route_Type"))

    st.subheader("Top 10 High-Traffic Stations")
    top_stations = station_frequency.head(10)
    st.bar_chart(top_stations.set_index("Station_Name"))

    st.subheader("Route Type Distribution Across Top 10 (Long-route) Stations")
    df_with_route = df.merge(
        train_routes[["Train_No", "Route_Type"]], on="Train_No", how="left"
    )
    pivot = pd.pivot_table(
        df_with_route,
        index="Station_Name",
        columns="Route_Type",
        values="Train_No",
        aggfunc=pd.Series.nunique,
        fill_value=0,
    )
    if "Long" in pivot.columns:
        top10 = pivot.sort_values("Long", ascending=False).head(10)
        st.bar_chart(top10[[c for c in ["Long", "Medium", "Short"] if c in top10.columns]])

    st.subheader("Dominant Station per Route Type")
    for route_type in ["Long", "Medium", "Short"]:
        if route_type in pivot.columns and not pivot[route_type].empty:
            station = pivot[route_type].idxmax()
            count = pivot[route_type].max()
            st.write(f"**{route_type}**: {station} ({count} trains)")
