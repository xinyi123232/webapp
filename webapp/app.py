import streamlit as st
import json
import folium
from pathlib import Path
from streamlit_folium import st_folium
import branca.colormap as cm
from branca.element import Element
import numpy as np

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

script_dir = Path(__file__).parent

@st.cache_resource
def load_scenario(scenario_path):
    
    base_path = script_dir / scenario_path
    with open(base_path / "hex.geojson") as f:
        hex_data = json.load(f)
    with open(base_path / "stations.geojson") as f:
        station_data = json.load(f)
    with open(base_path / "metrics.json") as f:
        metrics = json.load(f)

    return hex_data, station_data, metrics



@st.cache_resource
def load_city_boundaries():
    with open(script_dir/"data"/"city_boundaries.geojson") as f:
        return json.load(f)
        
  
city_boundaries = load_city_boundaries()

@st.cache_resource
def load_existing_stations():
    with open(script_dir/"data"/"baseline"/"stations.geojson") as f:
        return json.load(f)
          
existing_stations = load_existing_stations()

left, right = st.columns([2, 8], gap="small")

@st.dialog("How to Use This Dashboard", dismissible=False)
def help_dialog():

    st.markdown("""
### Dashboard Guide

**Planning Mode**
- :blue[Current Network] is the set of existing facilities that are already established and operating within the Metro Manila.
- :red[Efficiency], as represented by the :red[Maximal Covering Location Problem (MCLP)], focuses on maximizing the total number of people served given limited resources.
- :green[Equity], as represented by the :green[Set Covering Location Problem (SCLP)], focuses on selecting the minimum number of stations required to cover all demand areas within the service radius

**Map Functions**
- Demand Heatmaps → visualize demand intensity
- Click stations → view facility and optimization details

**Navigation**
- Zoom and pan to explore the network
    """)

    if st.button("Understood"):
        st.session_state.show_help = False
        st.rerun()

if "show_help" not in st.session_state:
    st.session_state.show_help = True
if st.session_state.show_help:
    help_dialog()
    
# ---- LEFT PANEL ----
with left:
    with st.container(height=650, border=False):
        st.markdown('<div class="left-panel">', unsafe_allow_html=True)
        st.markdown("### EV Charging Station Optimization")


        if st.button("How to use this dashboard"):
            st.session_state.show_help = True
            st.rerun()
        
        mode = st.radio(
        "Planning Mode",
        ["Current Network", "Efficiency", "Equity","Efficiency and Equity"]
        )
        scenario_path = "data/baseline"
    
        if mode == "Efficiency":
    
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
    
        elif mode == "Equity":
    
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

        elif mode == "Efficiency and Equity":
            # scenario_path = "data/efficiency_and_equity"
            scenario_path = "data/add50_balanced"
    
        # hex_data, station_data, metrics = load_scenario(scenario_path)

        if "scenario_data" not in st.session_state or st.session_state.get("current_path") != scenario_path:
            st.session_state.scenario_data = load_scenario(scenario_path)
            st.session_state.current_path = scenario_path

        hex_data, station_data, metrics = st.session_state.scenario_data
    
        st.markdown("---")
    
        st.subheader("Metrics")
    
        if mode == "Current Network":
            st.metric("Existing Stations", metrics["existing_stations"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            st.metric("Demand Covered Activity Priority", f"{metrics['demand_covered_balanced']}%")
            st.metric("Demand Covered Mobility Priority", f"{metrics['demand_covered_traffic']}%")
            st.metric("Demand Covered Resident Priority", f"{metrics['demand_covered_activity']}%")
    
        elif mode == "Efficiency":
            st.metric("New Stations Added", metrics["new_stations_added"])
            # st.metric("Total Stations", metrics["total_stations"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            st.metric("Area Improvement Over Current", f"+{metrics['area_improvement']}%")
            st.metric("Demand Covered", f"{metrics['demand_covered']}%")
            st.metric("Demand Improvement Over Current", f"+{metrics['demand_improvement']}%")
    
        elif mode == "Equity":
            st.metric("New Stations Required to Maximize Coverage", metrics["new_stations"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            st.metric("Uncovered Areas",f"{metrics['uncovered']}%")

        elif mode == "Efficiency and Equity":
            st.metric("New Stations Added", metrics["new_stations_added"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            st.metric("Area Improvement Over Current", f"+{metrics['area_improvement']}%")
            st.metric("Demand Covered", f"{metrics['demand_covered']}%")
            st.metric("Demand Improvement Over Current", f"+{metrics['demand_improvement']}%")
                
        st.markdown("---")
    
        if mode == "Current Network":
            # emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
            emphasize_existing = st.checkbox("Highlight Existing Coverage")
            emphasize_new = False
            show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
            show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
            show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap")
        elif mode == "Efficiency":
            if demand_focus == "Activity Priority":
                # emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                emphasize_existing = st.checkbox("Highlight Existing Coverage")
                emphasize_new = st.checkbox("Highlight New Coverage")
                show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
                show_heatmap_demand_score_B = False
                show_heatmap_demand_score_C = False
                
            elif demand_focus == "Mobility Priority":
                # emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                emphasize_existing = st.checkbox("Highlight Existing Coverage")
                emphasize_new = st.checkbox("Highlight New Coverage")
                show_heatmap_demand_score_A = False
                show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
                show_heatmap_demand_score_C = False
            else:
                # emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                emphasize_existing = st.checkbox("Highlight Existing Coverage")
                emphasize_new = st.checkbox("Highlight New Coverage")
                show_heatmap_demand_score_A = False
                show_heatmap_demand_score_B = False
                show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap") 
    
        elif mode == "Equity":
            # emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
            emphasize_existing = st.checkbox("Highlight Existing Coverage")
            emphasize_new = st.checkbox("Highlight New Coverage")
            show_heatmap_demand_score_A = False
            show_heatmap_demand_score_B = False
            show_heatmap_demand_score_C = False

        elif mode == "":
            emphasize_existing = st.checkbox("Highlight Existing Coverage")
            emphasize_new = st.checkbox("Highlight New Coverage")
            show_heatmap_demand_score_A = False
            show_heatmap_demand_score_B = False
            show_heatmap_demand_score_C = False
    
        st.markdown("</div>", unsafe_allow_html=True)
    
        # st.markdown("---")
    
        # with st.expander("Assumptions"):
        #     st.write("Distances are straight-line, not travel time.")
        #     st.write("Locations are based on public map data.")
        #     st.write("Results show eligible locations, not confirmed projects.")
        #     st.write("Implementation feasibility depends on land, power supply, and cost.")

# ---- RIGHT PANEL ----
with right:
    status_colors = {
        "uncovered": ["none", "0"],
        "existing": ["#38AADD", "0.1"],
        "new_coverage": ["red", "0.1"],
        "new_coverage_SCLP": ["green", "0.1"]
    }

    def style_hex(feature):
        status = feature["properties"].get("color_status")
        color = status_colors.get(status, "gray")
                
        if emphasize_existing:
            if status == "existing":
                return {
                    "fillColor": color[0],
                    "color": "black",
                    "weight": 0.3,
                    "fillOpacity": 0.9
                }

            else:
                return {
                    "fillColor": color[0],
                    "color": "black",
                    "weight": 0.1,
                    "fillOpacity": color[1]
                }
                

        if emphasize_new:
            if status == "new_coverage" or status == "new_coverage_SCLP":
                return {
                    "fillColor": color[0],
                    "color": "black",
                    "weight": 0.3,
                    "fillOpacity": 0.9
                }

            else:
                return {
                    "fillColor": color[0],
                    "color": "black",
                    "weight": 0.1,
                    "fillOpacity": color[1]
                }
        return {
            "fillColor": color[0],
            "color": "black",
            "weight": 0.1,
            "fillOpacity": color[1]
        }
        
    status_colors_stations = {
        "Existing": ["blue", "#38AADD",1000],
        "MCLP": ["red","red",1000],
        "SCLP": ["green","green",1000],
        "SCLP_500": ["green","green",500],
        "SCLP_2000": ["green","green",2000],             
        }
    
    def style_station(feature):
        a = feature.get('properties', {}).get('status')
        return status_colors_stations.get(a)
    
    
    def build_map(hex_data, station_data):
        m = folium.Map(location=[14.5995, 121.03], zoom_start=11, tiles="CartoDB Positron",prefer_canvas=True)
        
        EVCS = folium.FeatureGroup(name='EV Charging Stations')
        Existing_EVCS = folium.FeatureGroup(name='Existing EV Charging Stations')
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
        
        first_feature = station_data['features'][0]
        color_icon_radius = style_station(first_feature)


        if mode == "Current Network":
            folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level_A","demand_level_B","demand_level_C"],
                    aliases=["Coverage Status:", "Activity Demand Level:", "Mobility Demand Level:", "Resident Demand Level:"],
                    labels=True)).add_to(Service_Coverage_and_Hex)

            
            folium.GeoJson(
                
                station_data,
            
                tooltip=folium.GeoJsonTooltip(
                    fields=["full_id"
                    # , "address"
                    ],
                    aliases=["Station:"
                    # , "Address:"
                    ],
                    sticky=False
                ),
            
                popup=folium.GeoJsonPopup(
                    fields=[
                        "candidate_type",
                        "status",
                        # "priority_rank",
                        # "demand_score",
                        "y_epsg4326",
                        "x_epsg4326",
                        "google_maps_link"
                    ],
            
                    aliases=[
                        "Facility Type:",
                        "Status:",
                        # "Priority Rank:",
                        # "Demand Contribution Score:",
                        "Latitude:",
                        "Longitude:",
                        ""
                    ],
            
                    localize=True,
                    labels=True
                ),
            
                marker=folium.Marker(
                    icon=folium.Icon(
                        color=color_icon_radius[0],
                        icon="bolt",
                        prefix="fa"
                    )
                )
            
            ).add_to(EVCS)


        elif mode == "Efficiency":
            
            if demand_focus == "Activity Priority":
                folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level"],
                    aliases=["Coverage Status:", "Activity Demand Level:"],
                    labels=True)
).add_to(Service_Coverage_and_Hex)

                folium.GeoJson(
                existing_stations,
                marker=folium.CircleMarker(radius=3,color="#38AADD",fill=True,
        fill_opacity=.6,
        weight=.6)).add_to(Existing_EVCS)


                
                folium.GeoJson(
                    station_data,
                    tooltip=folium.GeoJsonTooltip(
                        fields=["full_id"
                        ],
                        aliases=["Station:"
                        ],
                        sticky=False
                    ),
                
                    popup=folium.GeoJsonPopup(
                        fields=[
                            "candidate_type",
                            "Potential",
                            "rank",
                            "contribution_w",
                            "contribution_share",
                            "y_epsg4326",
                            "x_epsg4326",
                            "google_maps_link"
                        ],
                
                        aliases=[
                            "Facility Type:",
                            "Status:",
                            "Priority Rank:",
                            "Demand Contribution Score:",
                            "Demand Contribution Share:",
                            "Latitude:",
                            "Longitude:",
                            ""
                        ],
                
                        localize=True,
                        labels=True
                    ),
                
                    marker=folium.Marker(
                        icon=folium.Icon(
                            color=color_icon_radius[0],
                            icon="bolt",
                            prefix="fa"
                        )
                    )
                
                ).add_to(EVCS)
                Existing_EVCS.add_to(m)
                
            elif demand_focus == "Mobility Priority":
                folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level"],
                    aliases=["Coverage Status:", "Mobility Demand Level:"],
                    labels=True)).add_to(Service_Coverage_and_Hex)
                folium.GeoJson(
                existing_stations,
                marker=folium.CircleMarker(radius=3,color="#38AADD",fill=True,
                    fill_opacity=.6,weight=.6)).add_to(Existing_EVCS)


                
                folium.GeoJson(
                    station_data,
                
                    tooltip=folium.GeoJsonTooltip(
                        fields=["full_id"
                        # , "address"
                        ],
                        aliases=["Station:"
                        # , "Address:"
                        ],
                        sticky=False
                    ),
                
                    popup=folium.GeoJsonPopup(
                        fields=[
                            "candidate_type",
                            "Potential",
                            "rank",
                            "contribution_w",
                            "contribution_share",
                            "y_epsg4326",
                            "x_epsg4326",
                            "google_maps_link"
                        ],
                
                        aliases=[
                            "Facility Type:",
                            "Status:",
                            "Priority Rank:",
                            "Demand Contribution Score:",
                            "Demand Contribution Share:",
                            "Latitude:",
                            "Longitude:",
                            ""
                        ],
                
                        localize=True,
                        labels=True,
                    ),
                
                    marker=folium.Marker(
                        icon=folium.Icon(
                            color=color_icon_radius[0],
                            icon="bolt",
                            prefix="fa"
                        )
                    )
                
                ).add_to(EVCS)
                Existing_EVCS.add_to(m)
                

            else:
                folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level"],
                    aliases=["Coverage Status:", "Resident Demand Level:"],
                    labels=True)).add_to(Service_Coverage_and_Hex)

                folium.GeoJson(
                existing_stations,
                marker=folium.CircleMarker(radius=3,color="#38AADD",fill=True,
        fill_opacity=.6,
        weight=.6)).add_to(Existing_EVCS)


                
                folium.GeoJson(
                    station_data,
                
                    tooltip=folium.GeoJsonTooltip(
                        fields=["full_id"
                        ],
                        aliases=["Station:"
                        ],
                        sticky=False
                    ),
                
                    popup=folium.GeoJsonPopup(
                        fields=[
                            "candidate_type",
                            "Potential",
                            "rank",
                            "contribution_w",
                            "contribution_share",
                            "y_epsg4326",
                            "x_epsg4326",
                            "google_maps_link"
                        ],
                
                        aliases=[
                            "Facility Type:",
                            "Status:",
                            "Priority Rank:",
                            "Demand Contribution Score:",
                            "Demand Contribution Share:",
                            "Latitude:",
                            "Longitude:",
                            ""
                        ],
                
                        localize=True,
                        labels=True,
                    ),
                
                    marker=folium.Marker(
                        icon=folium.Icon(
                            color=color_icon_radius[0],
                            icon="bolt",
                            prefix="fa"
                        )
                    )
                
                ).add_to(EVCS)
                Existing_EVCS.add_to(m)

        elif mode == "Equity":
            folium.GeoJson(
                hex_data,
                style_function=style_hex
            ).add_to(Service_Coverage_and_Hex)

            folium.GeoJson(
            existing_stations,
            marker=folium.CircleMarker(radius=3,color="#38AADD",fill=True,
    fill_opacity=.6,
    weight=.6)).add_to(Existing_EVCS)

            
            
            folium.GeoJson(
                station_data,
            
                tooltip=folium.GeoJsonTooltip(
                    fields=["full_id"
                    # , "address"
                    ],
                    aliases=["Station:"
                    # , "Address:"
                    ],
                    sticky=False
                ),
            
                popup=folium.GeoJsonPopup(
                    fields=[
                        "candidate_type",
                        "Potential",
                        "y_epsg4326",
                        "x_epsg4326",
                        "google_maps_link"
                    ],
            
                    aliases=[
                        "Facility Type:",
                        "Status:",
                        "Latitude:",
                        "Longitude:",
                        ""
                    ],
            
                    localize=True,
                    labels=True
                ),
            
                marker=folium.Marker(
                    icon=folium.Icon(
                        color=color_icon_radius[0],
                        icon="bolt",
                        prefix="fa"
                    )
                )
            
            ).add_to(EVCS)


            Existing_EVCS.add_to(m)

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
                    fields=["demand_score_A"],
                    aliases=["Demand:"],
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
                    fields=["demand_score_B"],
                    aliases=["Demand:"],
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
                    fields=["demand_score_C"],
                    aliases=["Demand:"],
                )
            ).add_to(Demand_Heatmap_Resident_Priority)
            Demand_Heatmap_Resident_Priority.add_to(m)
        
        folium.LayerControl().add_to(m)

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
        return m


    m = build_map(hex_data, station_data)
    
    st_folium(m, width=None, height=650, returned_objects=[])



