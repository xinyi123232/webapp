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
        
city_boundaries = load_city_boundaries()



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

    st.subheader("Metrics")

    if mode == "Current Network":
        st.metric("Existing Stations", metrics["existing_stations"])
        st.metric("Area Covered", f"{metrics['area_covered']}%")
        st.metric("Demand Covered Balanced", f"{metrics['demand_covered_balanced']}%")
        st.metric("Demand Covered Traffic", f"{metrics['demand_covered_traffic']}%")
        st.metric("Demand Covered Activity", f"{metrics['demand_covered_activity']}%")

    elif mode == "Add 50 Stations":
        st.metric("New Stations Added", metrics["new_stations_added"])
        st.metric("Total Stations", metrics["total_stations"])
        st.metric("Area Covered", f"{metrics['area_covered']}%")
        st.metric("Area Improvement Over Current", f"+{metrics['area_improvement']}%")
        st.metric("Demand Covered", f"{metrics['demand_covered']}%")
        st.metric("Demand Improvement Over Current", f"+{metrics['demand_improvement']}%")

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

    status_colors = {
    "uncovered": "red",
    "existing": "#38AADD",
    "new_coverage": "orange",
    "new_coverage_SCLP": "green"
}
    
    def style_hex(feature):
        status = feature["properties"].get("color_status")
        return {
            "fillColor": status_colors.get(status),
            "color": "black",
            "weight": 0.4,
            "fillOpacity": 0.6,
        }
    
    def style_station(feature):
        status = feature["properties"]["status"]
    
        if status == "Existing":
            color = "blue"
        else:
            color = "green"
    
        return {
            "radius": 5,
            "fillColor": color,
            "color": color,
            "fillOpacity": 1
        }

    

    def build_map(hex_data, station_data):
        m = folium.Map(location=[14.5995, 121.03], zoom_start=11, tiles="CartoDB Positron")
        EVCS = folium.FeatureGroup(name='Electric Vehicle Charging Stations')
        Service_Coverage_and_Hex = folium.FeatureGroup(name="1KM Service Coverage and Colored Hex")
        
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
        ).add_to(Service_Coverage_and_Hex)

        folium.GeoJson(
            station_data,
            marker=folium.Marker(
                #popup=folium.Popup(html_popup, max_width=250),
                #tooltip=f"Existing: {row['EVCS Name']}",
                icon=folium.Icon(color='blue', icon='bolt', prefix='fa'))
        ).add_to(EVCS)

        folium.GeoJson(
            station_data,
            marker=folium.Circle(
                radius=1000,   # 1KM in meters
                color="#38AADD",
                fill=True,
                fill_opacity=.1,
                weight=1
            )
        ).add_to(Service_Coverage_and_Hex)
        EVCS.add_to(m)
        Service_Coverage_and_Hex.add_to(m)
        folium.LayerControl(position='topleft',collapsed=False).add_to(m)
        st.cache_data.clear()
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

    # st_folium(m, width=1000, height=700
