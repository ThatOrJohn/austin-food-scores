import gradio as gr
import plotly.express as px
import pandas as pd
import os
import requests

from datetime import datetime, timedelta


API_URL = "https://data.austintexas.gov/resource/ecmv-9xxi.json"
API_TOKEN = os.getenv('AUSTIN_DATA_API_TOKEN')


def initialize_service(odata_url):
    session = requests.Session()
    response = session.get(odata_url + "/$metadata")
    response.raise_for_status()  # Ensure the request was successful
    schema = Schema.from_xml(response.content)
    return Service(service_root=odata_url, schema=schema, connection=session)


def fetch_inspection_data(lat, lon, radius=800):
    # Get latest inspection scores for the past 1.5 years within an 800 meter radius
    try:
        now = datetime.now(tz=None) - timedelta(days=548)
        formatted_date = now.strftime("%Y-%m-%dT00:00:00.000")

        params = {
            "$select": "restaurant_name, inspection_date, score, address",
            "$where": f"within_circle(address, {lat}, {lon}, {radius}) AND inspection_date >= '{formatted_date}'",
            "$group": "restaurant_name, inspection_date, address, score",
            "$having": "inspection_date = max(inspection_date)",
            "$limit": 250,
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        # Convert response to a DataFrame
        if data:
            df = pd.DataFrame(data)
            df = df.rename(
                columns={"restaurant_name": "Name", "score": "Score"})

            # Extract latitude and longitude
            df["latitude"] = df["address"].apply(
                lambda addr: addr.get(
                    "latitude") if addr and "latitude" in addr else None
            )
            df["longitude"] = df["address"].apply(
                lambda addr: addr.get(
                    "longitude") if addr and "longitude" in addr else None
            )

            df.to_csv(r'data.csv', index=None, sep=' ', mode='a')

            # Convert latitude and longitude columns to float
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

            # Drop rows where latitude or longitude is missing
            df = df.dropna(subset=["latitude", "longitude"])

            return df
        else:
            return pd.DataFrame(columns=["Name", "Score", "latitude", "longitude", "address"])
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame(columns=["Name", "Score", "latitude", "longitude", "address"])


def generate_inspection_map(lat, lon):
    # lat = 30.262189
    # lon = -97.723689
    try:
        lat, lon = float(lat), float(lon)
        inspection_data = fetch_inspection_data(lat, lon)

        if inspection_data.empty:
            return px.scatter_mapbox(
                title="No Inspection Data Found",
                lat=[],
                lon=[],
            )

        def categorize_score(score):
            if score >= 90:
                return "#8FBC8F"
            elif 70 <= score < 90:
                return "#FEFE22"
            else:
                return "red"

        marker_size = 3  # You can modify this value to test different marker sizes
        inspection_data["MarkerSize"] = marker_size

        inspection_data["Score"] = pd.to_numeric(
            inspection_data["Score"], errors="coerce")
        inspection_data["Color"] = inspection_data["Score"].apply(
            categorize_score)
        # Plot inspection data on the map
        fig = px.scatter_mapbox(
            inspection_data,
            lat="latitude",
            lon="longitude",
            hover_name="Name",
            hover_data={"Score": True,
                        "inspection_date": True,
                        "MarkerSize": False,
                        "Color": False,
                        "latitude": False,
                        "longitude": False},
            color="Color",
            size="MarkerSize",
            zoom=15,
            title="Restaurant Inspection Scores",
            height=500,
        )
        fig.update_layout(mapbox_style="open-street-map",
                          showlegend=False)

        return fig
    except Exception as e:
        print(f"Error generating map: {e}")
        return px.scatter_mapbox(title="Error Generating Map")


with gr.Blocks() as demo:
    gr.Markdown("### Austin Restaurant Inspection Scores ")
    with gr.Row():
        lat_field = gr.Textbox(label="Latitude", interactive=False)
        lon_field = gr.Textbox(label="Longitude", interactive=False)
    map_plot = gr.Plot(label="Map")
    fetch_button = gr.Button("Update Location")

    with gr.Row():
        gr.Textbox(label="Score Explanation",
                   value="""Inspection scores are captured during routine inspections of food facilities. All routine inspections start at 100 and begin counting down as violations are observed. A perfect score is 100 and can range all the way down to 0, with a "passing" score being 70 or above."""
                   )

    def update_ui(lat, lon):
        return generate_inspection_map(lat, lon)

    fetch_button.click(
        update_ui, inputs=[lat_field, lon_field], outputs=map_plot
    )

    demo.load(
        None,
        [],
        [lat_field, lon_field],
        js="""
        async () => {
            if (navigator.geolocation) {
                const startTime = performance.now();
                return new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            const endTime = performance.now();
                            const timeTaken = (endTime - startTime).toFixed(2);
                            console.log(`Time to fetch location: ${timeTaken} ms`);
                            const lat = position.coords.latitude.toFixed(6);
                            const lon = position.coords.longitude.toFixed(6);
                            resolve([lat, lon]);
                        },
                        (error) => {
                            console.error('Error fetching location', error);
                            resolve(['Error', 'Error']);
                        }
                    );
                });
            } else {
                return ['Geolocation not supported', 'Geolocation not supported'];
            }
        }
        """
    )

demo.launch()
