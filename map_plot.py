import folium
import datetime
import points
from points import haversine

def plot_location(user_lat, user_lon, show_radii, points_df=None):
    """
    Creates a folium map centered on the user's position and adds markers and circles for each location.
    
    The circle's color indicates:
      - Gray: the location is inactive
      - Green: the location is active and the user is within the radius
      - Red: the location is active but the user is outside the radius
    
    If points_df is provided, it is used instead of loading points from storage.
    """
    m = folium.Map(location=[user_lat, user_lon], zoom_start=12, control_scale=True)
    folium.Marker(
        [user_lat, user_lon],
        #popup="Jouw positie",
        tooltip="Hier ben jij, piraat! 🏴‍☠️",
        icon=folium.Icon(color='blue')
    ).add_to(m)
    
    if points_df is None:
        df = points.load_points()
    else:
        df = points_df

    if not df.empty:
        current_date = datetime.datetime.utcnow()
        for _, row in df.iterrows():
            loc_lat = row["latitude"]
            loc_lon = row["longitude"]
            loc_radius = row["radius"]
            available_from = row["available_from"]
            available_to = row["available_to"]
            location_text = row["pointer_text"]
            is_active = available_from <= current_date <= available_to
            distance = haversine(user_lat, user_lon, loc_lat, loc_lon)
            
            # Determine circle color:
            if not is_active:
                circle_color = "gray"
            else:
                if distance <= loc_radius:
                    circle_color = "green"
                else:
                    circle_color = "red"
            
            if show_radii:
                folium.Circle(
                    location=[loc_lat, loc_lon],
                    radius=loc_radius * 1000,  # convert km to m
                    color=circle_color,
                    fill=True,
                    fill_color=circle_color,
                    fill_opacity=0.3
                ).add_to(m)
            
            if is_active:
                popup_text = f"{location_text}<br>Straal: {loc_radius:.2f} km<br>Afstand: {distance:.2f} km"
            else:
                popup_text = f"{location_text}<br>Beschikbaar: {available_from.date()} tot {available_to.date()}"
            
            folium.Marker(
                [loc_lat, loc_lon],
                #popup=popup_text,
                tooltip=popup_text,
                icon=folium.Icon(color=circle_color)
            ).add_to(m)
    return m
