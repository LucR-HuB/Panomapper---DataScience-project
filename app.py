import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
from folium.raster_layers import WmsTileLayer
import json
import requests
import os
from shapely.geometry import shape, Point

st.set_page_config(layout="wide")

'''
# 🌍 Welcome to PanoMapper! 🛸
'''



########################### LOADING TILES GEOJSON FROM GOOGLE DRIVE #################################

# URL
tiles_url = "https://drive.google.com/uc?id=10JA-3LG6QMX_mC9Z2Ll1z8xT5Oc5La5Y"

# File download
response_tiles = requests.get(tiles_url)
response_tiles.raise_for_status()

# Loading file as GeoJSON
tiles_geojson = json.loads(response_tiles.text)

########################### LOADING DETECTIONS GEOJSON FROM GOOGLE DRIVE #############################

# URL
detections_url = "https://drive.google.com/uc?id=18GQ7-AlPia92Um6wTPyqXpMeVyVqcJkd"

# File download
response_detections = requests.get(detections_url)
response_detections.raise_for_status()

# Loading file as GeoJSON
detections_geojson = json.loads(response_detections.text)


##################################### BASE MAP CREATION ############################################

# Instanciating a folium map centered on Bordeaux
latitude = 44.856177683344065
longitude = -0.5624631313653328

m = folium.Map(location=[latitude, longitude], zoom_start=13)

# Adding sat images from WMS ortho geoportail to the map
base_url = "https://wxs.ign.fr/essentiels/geoportail/wmts"
final_url = "https://wxs.ign.fr/essentiels/geoportail/wmts?layer=ORTHOIMAGERY.ORTHOPHOTOS&tilematrixset=PM&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/jpeg&TileCol={x}&TileRow={y}&TileMatrix={z}&STYLE=normal"

m = folium.Map(location=[latitude, longitude], zoom_start=13, tiles=final_url, attr='IGN-F/Géoportail', max_zoom = 19)


##################################### USER ADRESS ############################################

'''

## Type your address below to start detection in your neibourhood! :robot_face:
'''
address = st.text_input('  ')
address_coordinates = ''


# Function to retrieve Lat/Lon from address using Nominatim API
def geocode(address):

        url = "https://nominatim.openstreetmap.org/search?"
        response = requests.get(url, params={
            'q': address,
            'format': 'json'
        })
        if response.status_code == 200:
            json_response = response.json()
            if len(json_response) > 0:
                return [json_response[0]['lat'], json_response[0]['lon']]
        return [0, 0]

# Retrieving Lat/Lon of the address and updating the map
if address:
    address_coordinates = geocode(address)
    m = folium.Map(location=[address_coordinates[0], address_coordinates[1]], zoom_start=13, tiles=final_url, attr='IGN-F/Géoportail', max_zoom = 19)
    folium.Marker(location=address_coordinates, tooltip=address).add_to(m)


##################################### RETRIEVING TILE NAMES FROM USER ADDRESS ############################################

# Retrieving name of the tile covering the address

tile_name = ''

if address_coordinates:
    for tile in tiles_geojson["features"]:
        tile_geom = shape(tile["geometry"])
        if tile_geom.contains(Point(address_coordinates[1], address_coordinates[0])):
            tile_name = tile["properties"]["NOM"]
            # st.write(f'{tile_name}')


# Retrieving surrounding tiles

if tile_name:

    tile_line = int(tile_name[8:12])
    tile_row = int(tile_name[13:17])

    tile_west = tile_name[:8] + '0' + str(tile_line-5) + tile_name[12:]
    tile_east = tile_name[:8] + '0' + str(tile_line+5) + tile_name[12:]
    tile_north = tile_name[:13] + str(tile_row+5) + tile_name[17:]
    tile_south = tile_name[:13] + str(tile_row-5) + tile_name[17:]
    tile_north_west = tile_name[:8] + '0' + str(tile_line-5) + '-' + str(tile_row+5) + tile_name[17:]
    tile_south_west = tile_name[:8] + '0' + str(tile_line-5) + '-' + str(tile_row-5) + tile_name[17:]
    tile_north_east = tile_name[:8] + '0' + str(tile_line+5) + '-' + str(tile_row+5) + tile_name[17:]
    tile_south_east = tile_name[:8] + '0' + str(tile_line+5) + '-' + str(tile_row-5) + tile_name[17:]

    tile_list = [tile_name, tile_west, tile_east, tile_north, tile_south, tile_north_west, tile_south_west, tile_south_west, tile_north_east, tile_south_east]

    # Checking if the tiles all exist

    final_tile_list = []

    for tile in tiles_geojson["features"]:
        if tile["properties"]["NOM"] in tile_list:
            final_tile_list.append(tile["properties"]["NOM"])
            final_tile_list = list(set(final_tile_list))


##################################### ASKING THE USER FOR A DETECTION RADIUS ############################################

# small_radius = st.button("5km2")
# big_radius = st.button("200km2")

##################################### FILTERING THE DETECTIONS ############################################


filtered_detections = []


if tile_name:
    for tile in final_tile_list:
        for feature in detections_geojson['features']:
            if feature['properties']['tile'] == tile:
                filtered_detections.append(feature)
    detections_geojson['features'] = filtered_detections

# if small_radius:
#     if tile_name:
#         for feature in detections_geojson['features']:
#             if feature['properties']['tile'] == tile_name:
#                 filtered_detections.append(feature)
#     detections_geojson['features'] = filtered_detections


##################################### ADDING THE DETECTIONS TO THE MAP ############################################

'''
## Start detection
'''

run_detection = st.button("DETECT!")

# Instanciating a detection feature group
detections_layer = folium.FeatureGroup(name='detections')

# Adding the filtered detections to the feature group
if run_detection:
    for detection in detections_geojson["features"]:
        geojson = folium.GeoJson(detection, name="detection", highlight_function=lambda x: {'weight': 3, 'color': 'green', 'fillOpacity': 0.5},
                                           tooltip=folium.GeoJsonTooltip(fields=['tile'], aliases=['Nom']))
        geojson.add_to(detections_layer)

# Adding the feature group to the map
if filtered_detections:
    detections_layer.add_to(m)


##################################### DISPLAYING THE MAP ############################################


folium_static(m, width=1800, height=800)


##################################### TILES DISPLAY ############################################

# # Tile Layer group
# tile_layer = folium.FeatureGroup(name='tiles')

# # Addding tiles to the map
# for tile in tiles_geojson["features"]:
#     properties = tile["properties"]
#     name = properties["NOM"]
#     geojson = folium.GeoJson(tile, name=name, highlight_function=lambda x: {'weight': 3, 'fillOpacity': 0.5},
#                                            tooltip=folium.GeoJsonTooltip(fields=['NOM'], aliases=['Nom']))
#     geojson.add_to(tilrs_layer)

# # Adding tiles to map
# tiles_layer.add_to(m)










# Detections Bx (centroides)
# https://drive.google.com/file/d/1i38Fh7_e9-_h6vGV0mOXKxci2rrq9FeJ/view?usp=share_link

# Detections Bx (polygones)
# https://drive.google.com/file/d/18GQ7-AlPia92Um6wTPyqXpMeVyVqcJkd/view?usp=share_link


# Nb par communes
# https://drive.google.com/file/d/1tT2dUtoKPTF6O0xLnVogby7ws4QoisU6/view?usp=share_link

# Dalles
# https://drive.google.com/file/d/10JA-3LG6QMX_mC9Z2Ll1z8xT5Oc5La5Y/view?usp=share_link
