# main.py
import streamlit as st
from PIL import Image
import uuid
import tempfile
import folium
from streamlit_folium import st_folium

# Import service modules and configuration
from services import detection, captioning, llm, geo
import config

# ------------------------------------------------------------------
# Custom CSS Styles and Page Configuration
st.set_page_config(page_title="🚧 City Agent", layout="wide")
st.markdown(
    """
    <style>
        .score-badge {
            font-size: 1.2rem;
            padding: 0.5rem 1.2rem;
            border-radius: 10px;
            display: inline-block;
            font-weight: 600;
        }
        .stApp {
            background-color: #f8f8f8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen;
            padding: 2rem;
        }
        .img-fixed {
            max-height: 220px;
            object-fit: contain;
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .output-box {
            background-color: #f2f2f2;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown("# 🚧 Agente de Triagem de Buracos")


def display_tag(label, value, icon):
    st.markdown(f"- {icon} **{label}:** `{value}`")


# ------------------------------------------------------------
# Presentation-only helper: Render a folium mini-map.
# (This is pure UI code, so it's kept here.)
def render_mini_map(lat, lon, facility_flags, radius=config.AMENITY_RADIUS):
    m = folium.Map(
        location=[lat, lon],
        zoom_start=config.FOLIUM_DEFAULT_ZOOM_START,
        control_scale=False,
        zoom_control=False,
        dragging=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        box_zoom=False,
        touchZoom=False,
        keyboard=False,
        tiles=config.FOLIUM_TILE_TYPE,
    )

    # Pothole marker
    folium.Marker(
        [lat, lon],
        tooltip="📍 Pothole Location",
        icon=folium.Icon(
            color=config.POTHOLE_MARKER_COLOR,
            icon=config.POTHOLE_MARKER_ICON,
            prefix="fa",
        ),
    ).add_to(m)

    # 500m radius circle
    folium.Circle(
        location=[lat, lon],
        radius=radius,
        color=config.RADIUS_CIRCLE_COLOR,
        fill=True,
        fill_opacity=config.RADIUS_CIRCLE_FILL_OPACITY,
    ).add_to(m)

    # Facility markers from query results
    for facility in facility_flags:
        tag = facility.get("tag", "unknown")
        emoji = facility.get("emoji", "🏷️")
        elements = facility.get("results", {}).get("elements", [])
        for el in elements:
            f_lat = el.get("lat") or el.get("center", {}).get("lat")
            f_lon = el.get("lon") or el.get("center", {}).get("lon")
            name = el.get("tags", {}).get("name", "Unnamed")
            if f_lat and f_lon:
                folium.Marker(
                    [f_lat, f_lon],
                    tooltip=f"{emoji} {tag.title()}: {name}",
                    icon=folium.Icon(
                        color=config.FACILITY_MARKER_COLOR,
                        icon=config.FACILITY_MARKER_ICON,
                        prefix="fa",
                    ),
                ).add_to(m)

    st.markdown("### 🗺️ Facility Map")
    st_folium(m, width=config.FOLIUM_MAP_WIDTH, height=config.FOLIUM_MAP_HEIGHT)

# ------------------------------------------------------------
# Main application code

# File Uploader
uploaded_file = st.file_uploader(
    "📤 Drop or select a road image", type=["jpg", "jpeg", "png"]
)
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    image_id = str(uuid.uuid4())

    # --- Top 3-Column Layout ---
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.subheader("🖼️ Original Image")
        st.image(image, use_container_width=True)

    # Step 1: Detection using YOLO
    with st.spinner("Step 1: Detecting potholes..."):
        model = detection.load_model()
        annotated_img, pothole_areas, avg_area, severity = detection.detect_potholes(
            model, image
        )

        # In column 2, show the detection results.
        with col2:
            st.subheader("✅ Initial Detection")
            st.image(annotated_img, channels="BGR", use_container_width=True)

    # Placeholder for final AI output in column 3.
    with col3:
        st.subheader("📝 Output")
        output_placeholder = st.empty()

    st.success("Image uploaded. Running full pipeline...")

    with st.expander("✅ Step 1: Detection Results"):
        severity_color = config.SEVERITY_COLORS.get(severity, "#000000")
        st.markdown(
            f'<span class="score-badge" style="background:{severity_color}; color:white;">Severity: {severity}</span>',
            unsafe_allow_html=True,
        )
        st.json(
            {
                "potholes_detected": len(pothole_areas),
                "average_area": avg_area,
                "severity": severity,
            }
        )

    # Step 2: Geo enrichment (services/geo.py)
    st.markdown("### 📍 Digite o endereço")
    address_input = st.text_input(
        "Endereço", placeholder="Ex: Avenida Paulista 1000, São Paulo"
    )

    if address_input:

        with st.spinner("Step 2: Gathering geo location data..."):
            lat, lon, display_name = geo.forward_geocode(address_input)
            st.success(f"📌 Coordinates: `{lat:.5f}, {lon:.5f}`")
            st.markdown(f"**🏠 Full Address:** _{display_name}_")

        with st.spinner("Step 2: Enriching data..."):
            # 🧭 Geo step
            geo_info = geo.reverse_geocode(lat, lon)
            st.success(f"Data enriched")

        # 🌐 Display all raw JSONs
        with st.expander("📍 Step 2: Location Summary"):
            display_name = geo_info.get("display_name", "Unknown location")
            city = geo_info.get("address", {}).get("city", "Unknown city")
            road = geo_info.get("address", {}).get("road", "Unknown road")
            lat_short = f"{lat:.5f}"
            lon_short = f"{lon:.5f}"

            st.markdown(f"**📌 Address:** _{display_name}_")
            st.markdown(f"**🧭 Coordinates:** `{lat_short}, {lon_short}`")
            st.markdown(f"**🏙️ City:** `{city}` — **🛣️ Road:** `{road}`")

            st.json(geo_info)

        with st.spinner("Step 2: Seaching for amenities in the vicinity..."):

            all_amenities = geo.query_all_amenities(lat, lon)
            organized_amenities = geo.organize_amenities_by_type(all_amenities)

            # 🏥 Facilities
            facility_flags = geo.query_nearby_amenities(
                lat,
                lon,
                types=[
                    ("hospital", "🚑"),
                    ("school", "🏫"),
                    ("police", "👮"),
                    ("subway_entrance", "🚇"),
                ],
            )

        # 🏥 Facility Overview
        with st.expander("🏥 Step 2: Critical Facilities Nearby"):
            critical_threshold_m = 200  # 🚨 Alert zone
            for item in facility_flags:
                tag = item["tag"]
                emoji = item["emoji"]
                results = item.get("results", {}).get("elements", [])
                if not results:
                    continue

                for facility in results:
                    name = facility.get("tags", {}).get("name", "Unnamed Facility")
                    f_lat = facility.get("lat") or facility.get("center", {}).get(
                        "lat"
                    )
                    f_lon = facility.get("lon") or facility.get("center", {}).get(
                        "lon"
                    )
                    if f_lat is None or f_lon is None:
                        continue

                    from geopy.distance import geodesic
                    distance = geodesic((lat, lon), (f_lat, f_lon)).meters

                    alert = distance < critical_threshold_m

                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.7); padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 0.5rem; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                            <h4 style="margin-bottom: 0.25rem;">{emoji} {name}</h4>
                            <p style="margin: 0.25rem 0;">📏 Distance: <code>{distance:.1f} m</code></p>
                            <p style="margin: 0.25rem 0;">🏷️ Type: <code>{tag}</code></p>
                            {"<p style='color: red;'>⚠️ Within critical zone!</p>" if alert else ""}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # 🏷️ Amenity Types
        with st.expander("🏷️ Step 2: Amenity Types Found"):
            tag_groups = list(organized_amenities.keys())
            st.markdown(
                f"**Found `{len(all_amenities)}` amenities** in `{len(tag_groups)}` types."
            )
            for tag in tag_groups:
                st.markdown(f"- `{tag}`: `{len(organized_amenities[tag])}`")
            st.json(organized_amenities)

        with st.spinner("Step 2: Gathering traffic data..."):
            road_name = geo_info.get("address", {}).get("road")

            traffic_data = geo.query_traffic_data(lat, lon, street_name=road_name)

        # 🚦 Traffic Summary
        with st.expander("🚗 Step 2: Road & Traffic Info"):
            tags = traffic_data.get("tags", {})
            if "maxspeed" in tags or "lanes" in tags or "surface" in tags:
                speed = tags.get("maxspeed", "unknown")
                lanes = tags.get("lanes", "unknown")
                surface = tags.get("surface", "unknown")

                st.markdown("**🛣️ Road Attributes:**")
                display_tag("Road Type", tags.get("highway", "—"), "🛣️")
                display_tag("Max Speed", tags.get("maxspeed", "—") + " km/h", "🚦")
                display_tag("Lanes (total)", tags.get("lanes", "—"), "🚧")
                display_tag("Bus Lanes", tags.get("lanes:bus", "—"), "🚌")
                display_tag(
                    "Bus Lane Hours", tags.get("lanes:bus:conditional", "—"), "⏰"
                )
                display_tag("Lighting", tags.get("lit", "—"), "💡")
                display_tag("Surface", tags.get("surface", "—"), "🧱")
                display_tag("Oneway", tags.get("oneway", "—"), "↩️")

                # Optional conditions
                if "motor_vehicle:conditional" in tags:
                    display_tag(
                        "Motor Vehicle Restriction",
                        tags["motor_vehicle:conditional"],
                        "🚘",
                    )
                if "foot:conditional" in tags:
                    display_tag(
                        "Pedestrian Restriction", tags["foot:conditional"], "🚶‍♂️"
                    )
                if "bicycle:conditional" in tags:
                    display_tag("Bike Access", tags["bicycle:conditional"], "🚴‍♀️")
                if "parking:both" in tags:
                    display_tag("Parking", tags["parking:both"], "🅿️")
                st.json(traffic_data)
            else:
                st.warning("No relevant road traffic tags found.")

        # # Step 3: LLM Insight & Summary (services/llm.py)
        with st.spinner("Step 3: Gathering AI Insights..."):
            # Save image to a temporary file for LLM image processing.
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                image.save(tmp.name)
                image_path = tmp.name

            llm_insight = llm.generate_llm_insight(image_path)

        with st.expander("📤 Step 3: LLaMA Triage Insight"):
            st.json(llm_insight)

        with st.spinner("🧠 Step 5: Generating final triage summary..."):
            # Only if geo data is available.
            if address_input and lat and lon:
                final_summary = llm.generate_triage_summary(
                    geo_info=geo_info,
                    lat=lat,
                    lon=lon,
                    caption=llm_insight.get("caption"),
                    tags=llm_insight.get("tags"),
                    severity=severity,
                    traffic_data=traffic_data,
                    facility_flags=facility_flags,
                    organized_amenities=organized_amenities,
                )

            with output_placeholder.container():
                st.markdown(
                    f"""
                    <div style="background:#f2f2f2; padding:1rem; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                        <h4>🧾 AI Report</h4>
                        <p><strong>📈 Severity:</strong> <code>{severity}</code></p>
                        <p><strong>🏷️ Tags:</strong> {", ".join([f"`{tag}`" for tag in llm_insight.get("tags", tags)])}</p>
                        <hr>
                        <p><strong>🧠 Summary:</strong><br><em>{final_summary}</em></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with st.expander("🧠 Step 4 : Final triage summary"):
            st.markdown(final_summary)

        with st.spinner("Step 5: Rendering mini map..."):
            # Step 5: Render facility map.
            render_mini_map(lat, lon, facility_flags)
