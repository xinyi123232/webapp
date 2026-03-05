import streamlit as st
import json
import folium
from pathlib import Path
from streamlit_folium import st_folium

script_dir = Path(__file__).parent


@st.cache_data
def load_hex():
    with open(script_dir/data/baseline/"hex.geojson") as f:
        return json.load(f)

@st.cache_data
def load_stations():
    with open(script_dir/data/baseline/"stations.geojson") as f:
        return json.load(f)

@st.cache_data
def load_metrics():
    with open(script_dir/data/baseline/"metrics.json") as f:
        return json.load(f)

hex_data = load_hex()
station_data = load_stations()
metrics = load_metrics()


st.set_page_config(layout="wide")

# Layout
left, right = st.columns([1, 2])

# ---- LEFT PANEL ----
with left:

    st.title("EV Charging Station Location Optimization")

    mode = st.radio(
        "Planning Mode",
        ["Current Network"]
    )

    st.markdown("---")

    st.subheader("Network Metrics")



    st.metric("Existing Stations", metrics["existing_stations"])
    st.metric("Area Covered", f"{metrics['area_covered']}%")
    st.metric("Demand Covered", f"{metrics['demand_covered']}%")

    st.markdown("---")

    with st.expander("Assumptions"):
        st.write("Distances are straight-line, not travel time.")
        st.write("Locations are based on public map data.")
        st.write("Results show eligible locations, not confirmed projects.")
        st.write("Implementation feasibility depends on land, power supply, and cost.")

# ---- RIGHT PANEL ----
with right:
    # Hex styling
    def style_hex(feature):
        covered = feature["properties"]["covered"]
        # demand = feature["properties"]["demand_level"]
        if covered:
            fill_color = "#38AADD"
        else:
            fill_color = "red"
        return {
            "fillColor": fill_color,
            "color": "black",
            "weight": 0.4,
            "fillOpacity": 0.7,
        }

    def build_map(hex_data, station_data):

        m = folium.Map(location=[14.5995, 121.03], zoom_start=11, tiles="CartoDB Positron")

        folium.GeoJson(
            hex_data,
            style_function=style_hex
        ).add_to(m)

        folium.GeoJson(
            station_data,
            marker=folium.Marker(
                #popup=folium.Popup(html_popup, max_width=250),
                #tooltip=f"Existing: {row['EVCS Name']}",
                icon=folium.Icon(color='blue', icon='bolt', prefix='fa'))
        ).add_to(m)

        folium.GeoJson(
            station_data,
            marker=folium.Circle(
                radius=1000,   # 1KM in meters
                color="#38AADD",
                fill=True,
                fill_opacity=.1,
                weight=1
            )
        ).add_to(m)
        return m


    m = build_map(hex_data, station_data)
    st_folium(m, width=1000, height=700)
    # m = folium.Map(location=[14.5995, 121.03], zoom_start=11, tiles="CartoDB Positron")
    


    # folium.GeoJson(
    #     hex_data,
    #     style_function=style_hex
    #     # tooltip=folium.GeoJsonTooltip(
    #     #     fields=["demand_level"],
    #     #     aliases=["Demand Level:"]
    #     # )
    # ).add_to(m)

        

    #     # folium.Circle(
    #     #     location=[row['Latitude'], row['Longitude']],
    #     #     radius=1000,   # 1KM in meters
    #     #     color="#38AADD",
    #     #     fill=True,
    #     #     fill_opacity=.1,
    #     #     weight=1
    #     # ).add_to(coverage_group)


    # # Stations
    # folium.GeoJson(
    #     station_data,
    #     marker=folium.Marker(
    #         #popup=folium.Popup(html_popup, max_width=250),
    #         #tooltip=f"Existing: {row['EVCS Name']}",
    #         icon=folium.Icon(color='blue', icon='bolt', prefix='fa'))
    # ).add_to(m)

    # folium.GeoJson(
    #     station_data,
    #     marker=folium.Circle(
    #         radius=1000,   # 1KM in meters
    #         color="#38AADD",
    #         fill=True,
    #         fill_opacity=.1,
    #         weight=1
    #     )
    # ).add_to(m)

    # st_folium(m, width=1000, height=700)








