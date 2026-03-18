import streamlit as st
import json
import folium
from pathlib import Path
from streamlit_folium import st_folium
import branca.colormap as cm
from branca.element import Element
import numpy as np

#

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

@st.dialog("How to Use This Dashboard", dismissible=False)
def help_dialog():

    st.markdown("""
### Dashboard Guide

**Planning Mode**
- Current Network → existing charging stations
- Efficiency → optimization expansion scenario
- Equity → maximum service coverage

**Map Functions**
- Highlight Coverage Gaps → shows uncovered areas
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
        ["Current Network", "Efficiency", "Equity"]
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
    
        hex_data, station_data, metrics = load_scenario(scenario_path)
    
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
            st.metric("Total Stations", metrics["total_stations"])
            st.metric("Area Covered", f"{metrics['area_covered']}%")
            st.metric("Area Improvement Over Current", f"+{metrics['area_improvement']}%")
            st.metric("Demand Covered", f"{metrics['demand_covered']}%")
            st.metric("Demand Improvement Over Current", f"+{metrics['demand_improvement']}%")
    
        elif mode == "Equity":
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
            emphasize_existing = st.checkbox("Highlight Existing Coverage")
            emphasize_new = False
            show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
            show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
            show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap")
        elif mode == "Efficiency":
            if demand_focus == "Activity Priority":
                emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                emphasize_existing = st.checkbox("Highlight Existing Coverage")
                emphasize_new = st.checkbox("Highlight New Coverage")
                show_heatmap_demand_score_A = st.checkbox("Show Activity Priority Demand Heatmap ")
                show_heatmap_demand_score_B = False
                show_heatmap_demand_score_C = False
                
            elif demand_focus == "Mobility Priority":
                emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                emphasize_existing = st.checkbox("Highlight Existing Coverage")
                emphasize_new = st.checkbox("Highlight New Coverage")
                show_heatmap_demand_score_A = False
                show_heatmap_demand_score_B = st.checkbox("Show Mobility Priority Demand Heatmap")
                show_heatmap_demand_score_C = False
            else:
                emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
                emphasize_existing = st.checkbox("Highlight Existing Coverage")
                emphasize_new = st.checkbox("Highlight New Coverage")
                show_heatmap_demand_score_A = False
                show_heatmap_demand_score_B = False
                show_heatmap_demand_score_C = st.checkbox("Show Resident Priority Demand Heatmap") 
    
        elif mode == "Equity":
            emphasize_gaps = st.checkbox("Highlight Coverage Gaps")
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
    # st.markdown('<div class="map-container">', unsafe_allow_html=True)
    # Hex styling

    status_colors = {
        "uncovered": False,
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
                
        if emphasize_existing:
            if status == "existing":
                return {
                    "fillColor": color,
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
                

        if emphasize_new:
            if status == "new_coverage" or status == "new_coverage_SCLP":
                return {
                    "fillColor": color,
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
        
#     def hex_popup(feature):
#         status = feature["properties"].get("color_status")
#         demand = feature["properties"].get("demand_level")
    
#         if status == "uncovered":
#             coverage = "Not Covered"
#         else:
#             coverage = "Covered"
    
#         html = f"""
#         <b>Coverage Status:</b> {coverage}<br>
#         <b>Demand Level:</b> {demand}
#         """
    
#         return folium.Popup(html, max_width=250)

#     hex_tooltip = folium.GeoJsonTooltip(
#     fields=["demand_level"],
#     aliases=["Demand Level:"],
#     sticky=False
# )


    status_colors_stations = {
        "Existing": ["blue", "#38AADD",1000],
        "MCLP": ["orange","orange",1000],
        "SCLP": ["green","green",1000],
        "SCLP_500": ["green","green",500],
        "SCLP_2000": ["green","green",2000],             
        }
    
    def style_station(feature):
        a = feature.get('properties', {}).get('status')
        return status_colors_stations.get(a)
        
    # color = style_station(station_data)

    def build_map(hex_data, station_data):
        m = folium.Map(location=[14.5995, 121.03], zoom_start=11, tiles="CartoDB Positron",prefer_canvas=True)
        
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
        
        first_feature = station_data['features'][0]
        color_icon_radius = style_station(first_feature)


        if mode == "Current Network":
        #     folium.GeoJson(hex_data,
        #                    style_function=style_hex,
        #                    popup=folium.GeoJsonPopup(
        #                        fields=["color_status","demand_level_A","demand_level_B","demand_level_C"],
        #                        aliases=["Coverage Status:", "Activity Demand Level:", "Mobility Demand Level:", "Resident Demand Level:"],
        #                        labels=True
        #                   )
        # ).add_to(Service_Coverage_and_Hex)
            folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level_A","demand_level_B","demand_level_C"],
                    aliases=["Coverage Status:", "Activity Demand Level:", "Mobility Demand Level:", "Resident Demand Level:"],
                    labels=True),
               tooltip=folium.GeoJsonTooltip(
    fields=["demand_level_A","demand_level_B","demand_level_C"],
    aliases=["Activity Demand Level:", "Mobility Demand Level:", "Resident Demand Level:"],
    sticky=False)
).add_to(Service_Coverage_and_Hex)

            
            folium.GeoJson(
                
                station_data,
            
                tooltip=folium.GeoJsonTooltip(
                    fields=["full_id"
                    # , "address"
                    ],
                    aliases=["Station Name:"
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
                        "x_epsg4326"
                    ],
            
                    aliases=[
                        "Facility Type:",
                        "Status:",
                        # "Priority Rank:",
                        # "Demand Contribution Score:",
                        "Latitude:",
                        "Longitude:"
                    ],
            
                    localize=True,
                    labels=True,
                    # style="""
                    #     background-color: white;
                    #     border: 1px solid gray;
                    #     border-radius: 4px;
                    #     padding: 5px;
                    # """
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
                    labels=True),
               tooltip=folium.GeoJsonTooltip(
                    fields=["demand_level"],
                    aliases=["Activity Demand Level:"],
                    sticky=False)
).add_to(Service_Coverage_and_Hex)


                
                folium.GeoJson(
                    station_data,
                
                    tooltip=folium.GeoJsonTooltip(
                        fields=["full_id"
                        # , "address"
                        ],
                        aliases=["Station Name:"
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
                            "x_epsg4326"
                        ],
                
                        aliases=[
                            "Facility Type:",
                            "Status:",
                            "Priority Rank:",
                            "Demand Contribution Score:",
                            "Demand Contribution Share:",
                            "Latitude:",
                            "Longitude:"
                        ],
                
                        localize=True,
                        labels=True,
                        # style="""
                        #     background-color: white;
                        #     border: 1px solid gray;
                        #     border-radius: 4px;
                        #     padding: 5px;
                        # """
                    ),
                
                    marker=folium.Marker(
                        icon=folium.Icon(
                            color=color_icon_radius[0],
                            icon="bolt",
                            prefix="fa"
                        )
                    )
                
                ).add_to(EVCS)
            
                
            elif demand_focus == "Mobility Priority":
                folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level"],
                    aliases=["Coverage Status:", "Mobility Demand Level:"],
                    labels=True),
               tooltip=folium.GeoJsonTooltip(
                    fields=["demand_level"],
                    aliases=["Mobility Demand Level:"],
                    sticky=False)
).add_to(Service_Coverage_and_Hex)


                
                folium.GeoJson(
                    station_data,
                
                    tooltip=folium.GeoJsonTooltip(
                        fields=["full_id"
                        # , "address"
                        ],
                        aliases=["Station Name:"
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
                            "x_epsg4326"
                        ],
                
                        aliases=[
                            "Facility Type:",
                            "Status:",
                            "Priority Rank:",
                            "Demand Contribution Score:",
                            "Demand Contribution Share:",
                            "Latitude:",
                            "Longitude:"
                        ],
                
                        localize=True,
                        labels=True,
                        # style="""
                        #     background-color: white;
                        #     border: 1px solid gray;
                        #     border-radius: 4px;
                        #     padding: 5px;
                        # """
                    ),
                
                    marker=folium.Marker(
                        icon=folium.Icon(
                            color=color_icon_radius[0],
                            icon="bolt",
                            prefix="fa"
                        )
                    )
                
                ).add_to(EVCS)
                

            else:
                folium.GeoJson(hex_data,
                style_function=style_hex,
                popup=folium.GeoJsonPopup(
                    fields=["covered","demand_level"],
                    aliases=["Coverage Status:", "Resident Demand Level:"],
                    labels=True),
               tooltip=folium.GeoJsonTooltip(
                    fields=["demand_level"],
                    aliases=["Resident Demand Level:"],
                    sticky=False)
).add_to(Service_Coverage_and_Hex)


                
                folium.GeoJson(
                    station_data,
                
                    tooltip=folium.GeoJsonTooltip(
                        fields=["full_id"
                        # , "address"
                        ],
                        aliases=["Station Name:"
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
                            "x_epsg4326"
                        ],
                
                        aliases=[
                            "Facility Type:",
                            "Status:",
                            "Priority Rank:",
                            "Demand Contribution Score:",
                            "Demand Contribution Share:",
                            "Latitude:",
                            "Longitude:"
                        ],
                
                        localize=True,
                        labels=True,
                        # style="""
                        #     background-color: white;
                        #     border: 1px solid gray;
                        #     border-radius: 4px;
                        #     padding: 5px;
                        # """
                    ),
                
                    marker=folium.Marker(
                        icon=folium.Icon(
                            color=color_icon_radius[0],
                            icon="bolt",
                            prefix="fa"
                        )
                    )
                
                ).add_to(EVCS)

        elif mode == "Equity":
            folium.GeoJson(
                hex_data,
                style_function=style_hex
                # ,
                # popup=folium.GeoJsonPopup(
                #     fields=["covered"],
                #     aliases=["Coverage Status:"],
                #     labels=True)
            ).add_to(Service_Coverage_and_Hex)


            
            folium.GeoJson(
                station_data,
            
                tooltip=folium.GeoJsonTooltip(
                    fields=["full_id"
                    # , "address"
                    ],
                    aliases=["Station Name:"
                    # , "Address:"
                    ],
                    sticky=False
                ),
            
                popup=folium.GeoJsonPopup(
                    fields=[
                        "candidate_type",
                        "Potential",
                        # "priority_rank",
                        # "demand_score",
                        "y_epsg4326",
                        "x_epsg4326"
                    ],
            
                    aliases=[
                        "Facility Type:",
                        "Status:",
                        # "Priority Rank:",
                        # "Demand Contribution Score:",
                        "Latitude:",
                        "Longitude:"
                    ],
            
                    localize=True,
                    labels=True,
                    # style="""
                    #     background-color: white;
                    #     border: 1px solid gray;
                    #     border-radius: 4px;
                    #     padding: 5px;
                    # """
                ),
            
                marker=folium.Marker(
                    icon=folium.Icon(
                        color=color_icon_radius[0],
                        icon="bolt",
                        prefix="fa"
                    )
                )
            
            ).add_to(EVCS)

        

        

            
        


        

        
        # folium.GeoJson(
        #     station_data,
        #     marker=folium.Marker(
        #         #popup=folium.Popup(html_popup, max_width=250),
        #         tooltip=f"Existing: {row['full_id']}",
        #         icon=folium.Icon(color=color_icon_radius[0], icon='bolt', prefix='fa'))
        # ).add_to(EVCS)
    
        folium.GeoJson(
            station_data,
            marker=folium.Circle(
                radius=color_icon_radius[2],   # 1KM in meters
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
        
        st.cache_data.clear()
        return m


    m = build_map(hex_data, station_data)
    
    st_folium(m, width=None, height=650, returned_objects=[])
    # st.markdown("</div>", unsafe_allow_html=True)

















































































