import streamlit as st
import json
import folium
from pathlib import Path
from streamlit_folium import st_folium
import branca.colormap as cm
from branca.element import Element
import numpy as np


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
city_boundaries = load_city_boundaries()


st.set_page_config(layout="wide")
st.markdown("""
<style>
/* Remove default Streamlit padding to make map edge-to-edge */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 0rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
}

/* Hide header */
header {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


left, right = st.columns([2, 8], gap="small")


# ---- LEFT PANEL ----
with left:
    with st.container(height=650, border=False):

        st.markdown('<div class="left-panel">', unsafe_allow_html=True)
        st.markdown("### EV Charging Station Optimization")
        
        mode = st.radio(
        "Planning Mode",
        ["Current Network", "Add 50 Stations", "Universal Coverage"]
        )
        scenario_path = "data/baseline"
    
        if mode == "Add 50 Stations":
    
            demand_focus = st.selectbox(
                "Demand Focus",
                ["Activity Priority", "Mobility Priority", "Resident Priority"]
            )
            
            if demand_focus == "Activity Priority":
                scenario_path = "data/add50_balanced"
            elif demand_focus == "Mobility Priority":
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
            st.metric("Demand Covered Activity Priority", f"{metrics['demand_covered_balanced']}%")
            st.metric("Demand Covered Mobility Priority", f"{metrics['demand_covered_traffic']}%")
            st.metric("Demand Covered Resident Priority", f"{metrics['demand_covered_activity']}%")
    
        elif mode == "Add 50 Stations":
            st.metric("New Stations Added", metrics["new_stations_added"])
            st.metric("Total Stations", metrics["total_stations"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            st.metric("Area Improvement Over Current", f"+{metrics['area_improvement']}%")
            st.metric("Demand Covered", f"{metrics['demand_covered']}%")
            st.metric("Demand Improvement Over Current", f"+{metrics['demand_improvement']}%")
    
        elif mode == "Universal Coverage":
            st.metric("New Stations Required to Maximize Coverage", metrics["new_stations"])
            st.metric("Total Stations (current + new)", metrics["total_stations"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            
    
            if metrics["uncovered"] == 0:
                st.success("All serviceable areas covered.")
            else:
                st.metric("Uncovered Areas",f"{metrics['uncovered']}%")
                
        st.markdown("---")
    
        if mode == "Current Network":
            emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
    
            show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
            show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
            show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap")
        elif mode == "Add 50 Stations":
            if demand_focus == "Activity Priority":
                emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
                show_heatmap_demand_score_B = False
                show_heatmap_demand_score_C = False
                
            elif demand_focus == "Mobility Priority":
                emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                show_heatmap_demand_score_A = False
                show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
                show_heatmap_demand_score_C = False
            else:
                emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                show_heatmap_demand_score_A = False
                show_heatmap_demand_score_B = False
                show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap") 
    
        elif mode == "Universal Coverage":
            emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
            show_heatmap_demand_score_A = False
            show_heatmap_demand_score_B = False
            show_heatmap_demand_score_C = False
    
        st.markdown("</div>", unsafe_allow_html=True)
    
            
        # emphasize_gaps = st.checkbox("Highlight Coverage Gaps") 
        # show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
        # show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
        # show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap")
    
    
        # st.markdown("---")
    
        # with st.expander("Assumptions"):
        #     st.write("Distances are straight-line, not travel time.")
        #     st.write("Locations are based on public map data.")
        #     st.write("Results show eligible locations, not confirmed projects.")
        #     st.write("Implementation feasibility depends on land, power supply, and cost.")

# ---- RIGHT PANEL ----
with right:
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    # Hex styling

    status_colors = {
        "uncovered": "red",
        "existing": "#38AADD",
        "new_coverage": "orange",
        "new_coverage_SCLP": "green"
    }

    def style_hex(feature):
    
        status = feature["properties"].get("color_status")
    
        color = status_colors.get(status, "gray")


        
        if emphasize_gaps:
    
            if status == "uncovered":
                return {
                    "fillColor": "red",
                    "color": "black",
                    "weight": 0.3,
                    "fillOpacity": 0.9
                }
    
            else:
                return {
                    "fillColor": color,
                    "color": "black",
                    "weight": 0.1,
                    "fillOpacity": 0.1
                }
    
        # Normal view
        return {
            "fillColor": color,
            "color": "black",
            "weight": 0.1,
            "fillOpacity": 0.1
        }


    status_colors_stations = {
        "existing": ["blue", "#38AADD"],
        "MCLP": ["orange","orange"],
        "SCLP": ["green","green"]  
        }
    
    def style_station(feature):
        a = feature.get('properties', {}).get('status')
        return status_colors_stations.get(a)
        
    # color = style_station(station_data)

    def build_map(hex_data, station_data):
        m = folium.Map(location=[14.5995, 121.03], zoom_start=11, tiles="CartoDB Positron")
        
        EVCS = folium.FeatureGroup(name='Electric Vehicle Charging Stations with 1KM Service Coverage')
        Service_Coverage_and_Hex = folium.FeatureGroup(name="Colored Coverage Area Hex")
        Demand_Heatmap_Activity_Priority= folium.FeatureGroup(name="Activity Priority Demand Heatmap")
        Demand_Heatmap_Mobility_Priority= folium.FeatureGroup(name="Mobility Priority Demand Heatmap")
        Demand_Heatmap_Resident_Priority= folium.FeatureGroup(name="Resident Priority Demand Heatmap")

        
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
        ).add_to(Service_Coverage_and_Hex
                )

        
        first_feature = station_data['features'][0]
        color_icon_radius = style_station(first_feature)
        
        folium.GeoJson(
            station_data,
            marker=folium.Marker(
                #popup=folium.Popup(html_popup, max_width=250),
                #tooltip=f"Existing: {row['EVCS Name']}",
                icon=folium.Icon(color=color_icon_radius[0], icon='bolt', prefix='fa'))
        ).add_to(EVCS)
    
        folium.GeoJson(
            station_data,
            marker=folium.Circle(
                radius=1000,   # 1KM in meters
                color=color_icon_radius[1],
                fill=True,
                fill_opacity=0,
                weight=1
            )
        ).add_to(EVCS)
        EVCS.add_to(m)
        Service_Coverage_and_Hex.add_to(m)


        
        ### show_heatmap_demand_score_A
        if show_heatmap_demand_score_A:
            # classifier = mc.NaturalBreaks(
            #     hex_data["properties"]["demand_score_A_Contrast"],
            #     k=7
            #     )
            colormap = cm.StepColormap(
                colors=cm.linear.YlOrRd_07.colors,
                index=[0.01812406,0.04711549,0.08538441,0.13938344,0.23276964,0.38180516,0.60640651],
                vmin=0.0,
                vmax=0.7081203248065904
                )
        
            def style_function_demand_score(feature):
              value = feature["properties"]["demand_score_A_Contrast"]
            
              return {
                  "fillColor": colormap(value),
                  "color": "black",
                  "weight": 0.3,
                  "fillOpacity": 0.6,
            }
        
        
        
            folium.GeoJson(
                hex_data,
                style_function=style_function_demand_score,
                tooltip=folium.GeoJsonTooltip(
                    fields=["hex_id", "demand_score_A"],
                    aliases=["Hex ID:", "Demand:"],
                )
            ).add_to(Demand_Heatmap_Activity_Priority)
            Demand_Heatmap_Activity_Priority.add_to(m)



        
        ### show_heatmap_demand_score_B
        if show_heatmap_demand_score_B:
            colormap = cm.StepColormap(
                colors=cm.linear.YlOrRd_07.colors,
                index=[0.01482183, 0.04042263, 0.07413142, 0.12199452, 0.19731733, 0.31187647, 0.52160928],
                vmin=0.0,
                vmax=0.521609281897208
                )
        
            def style_function_demand_score(feature):
              value = feature["properties"]["demand_score_B_Contrast"]
            
              return {
                  "fillColor": colormap(value),
                  "color": "black",
                  "weight": 0.3,
                  "fillOpacity": 0.6,
            }
        
        
        
            folium.GeoJson(
                hex_data,
                style_function=style_function_demand_score,
                tooltip=folium.GeoJsonTooltip(
                    fields=["hex_id", "demand_score_B"],
                    aliases=["Hex ID:", "Demand:"],
                )
            ).add_to(Demand_Heatmap_Mobility_Priority)
            Demand_Heatmap_Mobility_Priority.add_to(m)

        


        ### show_heatmap_demand_score_C
        if show_heatmap_demand_score_C:
            colormap = cm.StepColormap(
                colors=cm.linear.YlOrRd_07.colors,
                index=[0.01445328, 0.03363341, 0.05778048, 0.09272426, 0.14310257, 0.23223499, 0.4],
                vmin=0.0,
                vmax=0.4
                )
        
            def style_function_demand_score(feature):
              value = feature["properties"]["demand_score_C_Contrast"]
            
              return {
                  "fillColor": colormap(value),
                  "color": "black",
                  "weight": 0.3,
                  "fillOpacity": 0.6,
            }
        
        
        
            folium.GeoJson(
                hex_data,
                style_function=style_function_demand_score,
                tooltip=folium.GeoJsonTooltip(
                    fields=["hex_id", "demand_score_C"],
                    aliases=["Hex ID:", "Demand:"],
                )
            ).add_to(Demand_Heatmap_Resident_Priority)
            Demand_Heatmap_Resident_Priority.add_to(m)
            
        # css = """
        # <style>
        #     .leaflet-control-layers-list {
        #         font-size: 14px; /* Change the font size */
        #         /* You can add other styles here, e.g., width, height, etc. */
        #     }
        # </style>
        # """
        # m.get_root().header.add_child(Element(css))
        
        folium.LayerControl().add_to(m)
        # position='topleft'
        custom_css = """
        <style>
            .leaflet-control-layers-list {
                width: 200px; /* Adjust width as needed */
                font-size: 14px; /* Adjust font size as needed */
            }
            .leaflet-control-layers-label {
                font-size: 14px; /* Adjust label font size as needed */
            }
        </style>
        """
        

        m.get_root().header.add_child(Element(custom_css))

        
        # legend_html = """
        # <div style="
        # position: fixed;
        # bottom: 50px;
        # left: 50px;
        # width: 220px;
        # z-index:9999;
        # font-size:14px;
        # background-color:white;
        # border:2px solid grey;
        # border-radius:6px;
        # padding:10px;
        # ">
        
        # <b>Map Legend</b><br>
        
        # <br><b>Stations</b><br>
        
        # <i style="color:blue;" class="fa fa-bolt"></i> Existing Station<br>
        # <i style="color:orange;" class="fa fa-bolt"></i> MCLP Station<br>
        # <i style="color:green;" class="fa fa-bolt"></i> SCLP Station<br>
        
        # <br><b>Coverage Status</b><br>
        
        # <span style="background:#38AADD;width:12px;height:12px;display:inline-block"></span>
        # Covered (Existing)<br>
        
        # <span style="background:orange;width:12px;height:12px;display:inline-block"></span>
        # New Coverage (MCLP)<br>
        
        # <span style="background:green;width:12px;height:12px;display:inline-block"></span>
        # New Coverage (SCLP)<br>
        
        # <span style="background:red;width:12px;height:12px;display:inline-block"></span>
        # Uncovered Area<br>
        
        # </div>
        # """


        
        # legend = MacroElement()
        # legend._template = Template(legend_html)
        
        # m.get_root().add_child(legend)
        
        # st.cache_data.clear()
        return m


    m = build_map(hex_data, station_data)
    
    st_folium(m, width=None, height=650)
    st.markdown("</div>", unsafe_allow_html=True)

































