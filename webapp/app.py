import streamlit as st
import json
import folium
from pathlib import Path
from streamlit_folium import st_folium

script_dir = Path(__file__).parent

@st.cache_data
def load_scenario(scenario_path):
    base_path = script_dir / scenario_path
    with open(base_path / "hex.geojson") as f:
        hex_data = json.load(f)
    with open(base_path / "stations.geojson") as f:
        station_data = json.load(f)
    with open(base_path / "metrics.json") as f:
        metrics = json.load(f)

    return hex_data, station_data, metrics

@st.cache_data
def load_city_boundaries():
    with open(script_dir/"data"/"city_boundaries.geojson") as f:
        return json.load(f)

# @st.cache_data
# def load_stations():
#     with open(script_dir/"data"/"baseline"/"stations.geojson") as f:
#         return json.load(f)

# @st.cache_data
# def load_metrics():
#     with open(script_dir/"data"/"baseline"/"metrics.json") as f:
#         return json.load(f)

city_boundaries = load_city_boundaries()
# station_data = load_stations()
# metrics = load_metrics()


st.set_page_config(layout="wide")

# Layout
left, right = st.columns([1, 2])

# ---- LEFT PANEL ----
with left:

    st.title("EV Charging Station Location Optimization")

    mode = st.radio(
    "Planning Mode",
    ["Current Network", "Add 50 Stations", "Universal Coverage"]
    )
    scenario_path = "data/baseline"

    if mode == "Add 50 Stations":

        demand_focus = st.selectbox(
            "Demand Focus",
            ["Balanced", "Traffic Priority", "Activity Priority"]
        )

        if demand_focus == "Balanced":
            scenario_path = "data/add50_balanced"
        elif demand_focus == "Traffic Priority":
            scenario_path = "data/add50_traffic"
        else:
            scenario_path = "data/add50_activity"

    elif mode == "Universal Coverage":

        service_standard = st.selectbox(
            "Service Standard",
            ["500 meters (Very Strict)",
            "1000 meters (Standard)",
            "2000 meters (Relaxed)"]
        )

        if "500" in service_standard:
            scenario_path = "data/universal_500"
        elif "1000" in service_standard:
            scenario_path = "data/universal_1000"
        else:
            scenario_path = "data/universal_2000"

    hex_data, station_data, metrics = load_scenario(scenario_path)

    st.markdown("---")

    st.subheader("Network Metrics")

    if mode == "Current Network":
        st.metric("Existing Stations", metrics["existing_stations"])
        st.metric("Area Covered", f"{metrics['area_covered']}%")
        st.metric("Demand Covered", f"{metrics['demand_covered']}%")

    elif mode == "Add 50 Stations":
        st.metric("New Stations Added", 50)
        st.metric("Total Stations", metrics.get("total_stations", 0))
        # st.metric("Total Stations", metrics["total_stations"])
        st.metric("Area Covered", f"{metrics['area_covered']}%")
        st.metric("Demand Covered", f"{metrics['demand_covered']}%")
        # st.metric("Improvement Over Current", f"+{metrics['improvement']}%")

    elif mode == "Universal Coverage":
        st.metric("New Stations Required", metrics["new_stations"])
        st.metric("Total Stations", metrics["total_stations"])
        st.metric("Area Covered", "100%")

        if metrics["uncovered"] == 0:
            st.success("All serviceable areas covered.")
        else:
            st.metric("Uncovered Areas", metrics["uncovered"])

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
        city_boundaries,
        name="City Boundaries",
        style_function=lambda feature: {
            "fillColor": "none",
            "color": "black",
            "weight": 3,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(fields=["ADM3_EN"])
    ).add_to(m)

        
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

















