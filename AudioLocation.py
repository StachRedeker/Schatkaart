import streamlit as st
from streamlit_js_eval import get_geolocation
import folium
import datetime
import pandas as pd
import base64
import streamlit.components.v1 as components

import auth
import points
from map_plot import plot_location
import voice_memo

# Set page config with centered layout and custom favicon.
st.set_page_config(
    page_title="Stachs Schatkaart",
    page_icon="favicon.png",
    layout="centered"
)

# Custom CSS to force a max-width on the container for desktop responsiveness.
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 800px;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Stachs Schatkaart 🏴‍☠️")
st.markdown("""
Ahoy, Kapitein Kim! 

Met je verjaardag in zicht is het tijd om je zeilen te hijsen en op zoek te gaan naar de schatten die de wereld je te bieden heeft.
Jij bent de kapiteit van je eigen schip. Niemand anders zal jouw koers bepalen.
Bereid je voor op een avontuur vol verborgen rijkdommen en gevaarlijke wateren! Of geluidsfragmentjes van mij. Dat kan ook. ☠️🏝️

Groet, 
Scheepsman Stach
""")

username, authenticated = auth.authenticate()
if authenticated:
    show_radii = st.checkbox("Toon radii", value=True, 
                             help="Laat de 	radii zien rond iedere locatie. Die lijken misschien vijandig water, maar als je je in de radius bevindt, kun je de schat opgraven.")
    hide_inactive = st.checkbox("Verberg inactieve schatten", value=False, 
                                help="Verberg schatten die momenteel niet actief zijn (buiten de datumperiode).")
    
    loc = None
    if st.checkbox("Bepaal mijn locatie", help="Klik hier om jouw positie te bepalen. Hiervoor gebruiken we je browserlocatie. Arr!"):
        loc = get_geolocation()
        st.write("Arr! Hier zijn je coördinaten:", loc)
        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            df_points = points.load_points()
            current_date = datetime.datetime.utcnow()
            if hide_inactive:
                df_points = df_points[df_points.apply(lambda row: row["available_from"] <= current_date <= row["available_to"], axis=1)]
            
            # Create map
            folium_map = plot_location(lat, lon, show_radii, points_df=df_points)
            map_html = folium_map.get_root().render()
            map_html = map_html.replace('width:700px', 'width:100%')
            components.html(map_html, height=500)
            
            # Change number of locations
            num_locations = st.number_input("Aantal schatten om te tonen", 
                                            min_value=1, value=10, step=1,
                                            help="Voer het aantal dichtstbijzijnde schatten in dat je in de tabel wilt zien. 10 is de standaard. Maar als je op grote jacht wil, kun je dit getal verhogen.")
            
            if st.button("Toon dichtstbijzijnde schatten"):
                # Calculate distances
                df_points["distance"] = df_points.apply(lambda row: points.haversine(lat, lon, row["latitude"], row["longitude"]), axis=1)
                closest_df = df_points.nsmallest(num_locations, "distance").copy()
                
                voice_memo_status = []
                for idx, row in closest_df.iterrows():
                    if "voice_memo" not in row or pd.isna(row["voice_memo"]) or row["voice_memo"].strip() == "":
                        voice_memo_status.append("Geen schat beschikbaar")
                    else:
                        if not (row["available_from"] <= current_date <= row["available_to"]):
                            voice_memo_status.append(
                                f"Niet actief (beschikbaar van {row['available_from'].date()} tot {row['available_to'].date()})"
                            )
                        elif row["distance"] > row["radius"]:
                            voice_memo_status.append(
                                f"Buiten bereik (afstand: {row['distance']:.2f} km, straal: {row['radius']:.2f} km)"
                            )
                        else:
                            try:
                                file_data, file_name = voice_memo.get_decrypted_voice_memo(row["voice_memo"])
                                b64 = base64.b64encode(file_data).decode()
                                # Gebruik MIME type application/octet-stream zodat er geen .mp3 wordt toegevoegd.
                                download_link = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Schat opgraven</a>'
                                voice_memo_status.append(download_link)
                            except Exception as e:
                                voice_memo_status.append(f"Fout bij decryptie: {str(e)}")
                closest_df["Schat"] = voice_memo_status
                closest_df["Afstand (km)"] = closest_df["distance"].map(lambda d: f"{d:.2f}")
                closest_df["Actieve Periode"] = closest_df.apply(
                    lambda row: f"{row['available_from'].date()} tot {row['available_to'].date()}", axis=1
                )
                display_df = closest_df.rename(columns={"pointer_text": "Locatie", "radius": "Straal (km)"})
                final_cols = ["Locatie", "Straal (km)", "Actieve Periode", "Afstand (km)", "Schat"]
                html_table = display_df[final_cols].to_html(escape=False, index=False)
                html_table = '<style>th { text-align: left !important; }</style>' + html_table
                st.markdown(f'<div style="overflow-x:auto;">{html_table}</div>', unsafe_allow_html=True)
