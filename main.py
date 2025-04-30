import pandas as pd
import geopandas as gpd
import folium
import json
from shapely.geometry import shape

# File paths (assuming they are in the same directory as the Python script)
csv_file_path = 'data.csv'
geojson_file_path = 'up_districts.geojson'

# Load the CSV file
data = pd.read_csv(csv_file_path)

# Load the GeoJSON file
with open(geojson_file_path, 'r') as f:
    geojson_data = json.load(f)

# Extract district names and geometry to create a simplified GeoDataFrame
simplified_geo_data = []
for feature in geojson_data['features']:
    geometry = shape(feature['geometry'])
    district_name = feature['properties']['district']
    simplified_geo_data.append({
        'District': district_name,
        'geometry': geometry
    })

# Create a new GeoDataFrame for the GeoJSON data
simplified_gdf = gpd.GeoDataFrame(simplified_geo_data)

# Merge the GeoDataFrame with the CSV data
merged_gdf = simplified_gdf.merge(data, on='District', how='left')

# Calculate total NDRF, SDRF, and PAC units across all districts
total_ndrf = merged_gdf['NDRF'].sum(skipna=True)
total_sdrf = merged_gdf['SDRF'].sum(skipna=True)
total_pac = merged_gdf['PAC'].sum(skipna=True)

# Create a Folium map centered on Uttar Pradesh with a white background
map_center = [26.8467, 80.9462]  # Approximate center of UP
up_map = folium.Map(location=map_center, zoom_start=7, tiles='cartodb positron')

# Create separate GeoJson layers for NDRF, PAC, and SDRF
ndrf_layer = folium.FeatureGroup(name="NDRF", show=True)
pac_layer = folium.FeatureGroup(name="PAC", show=False)
sdrf_layer = folium.FeatureGroup(name="SDRF", show=False)

# Function to style districts based on presence of NDRF, PAC, or SDRF
def style_function(color):
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 1.5,
        'fillOpacity':1.0
    }

# Add GeoJSON layers with appropriate coloring and popups for each
for _, row in merged_gdf.iterrows():
    district_name = row['District']
    
    # Retrieve NDRF, SDRF, and PAC values (default to 0 if NaN)
    ndrf = int(row['NDRF']) if pd.notnull(row['NDRF']) else 0
    sdrf = int(row['SDRF']) if pd.notnull(row['SDRF']) else 0
    pac = int(row['PAC']) if pd.notnull(row['PAC']) else 0
    
    # Popup content displaying NDRF, SDRF, and PAC
    popup_content = f"<strong>{district_name}</strong><br>NDRF: {ndrf}<br>SDRF: {sdrf}<br>PAC: {pac}"

    # NDRF Layer (colored red)
    if ndrf > 0:
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: style_function('red'),
            tooltip=folium.Tooltip(popup_content)
        ).add_to(ndrf_layer)
    
    # PAC Layer (colored yellow)
    if pac > 0:
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: style_function('blue'),
            tooltip=folium.Tooltip(popup_content)
        ).add_to(pac_layer)
    
    # SDRF Layer (colored green)
    if sdrf > 0:
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: style_function('yellow'),
            tooltip=folium.Tooltip(popup_content)
        ).add_to(sdrf_layer)

# Add layers to the map
ndrf_layer.add_to(up_map)
pac_layer.add_to(up_map)
sdrf_layer.add_to(up_map)

# Add a boundary layer for all districts
folium.GeoJson(
    geojson_data,
    style_function=lambda x: {
        'fillOpacity': 0,
        'color': 'black',
        'weight': 2
    }
).add_to(up_map)

# Add layer control toggle
folium.LayerControl(collapsed=False).add_to(up_map)

# Add a custom legend with totals
legend_html = f'''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 250px; height: 150px; 
            background-color: white; z-index:9999; font-size:14px; 
            border:2px solid grey; padding: 10px;">
    <h4 style="margin-top: 0;">Legend</h4>
    <i style="background: red; width: 18px; height: 18px; display: inline-block;"></i> NDRF (Total: {total_ndrf})<br>
    <i style="background: green; width: 18px; height: 18px; display: inline-block;"></i> SDRF (Total: {total_sdrf})<br>
    <i style="background: yellow; width: 18px; height: 18px; display: inline-block;"></i> PAC (Total: {total_pac})<br>
</div>
'''

# Add the legend to the map
up_map.get_root().html.add_child(folium.Element(legend_html))

# Save the map to an HTML file
map_file_path = 'up_ndrf_sdrf_pac_map_with_white_background.html'
up_map.save(map_file_path)

print(f"Map saved to {map_file_path}")
