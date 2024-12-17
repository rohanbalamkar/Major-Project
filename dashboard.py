import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import requests
import pandas as pd

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Health Monitor Dashboard"

# FastAPI endpoint
FASTAPI_URL = "http://127.0.0.1:8000/data"  # Update this if the server is running on another machine

# Layout
app.layout = html.Div([
    html.H1("Health Monitor Dashboard", style={'textAlign': 'center'}),
    dcc.Interval(id='update-interval', interval=1000, n_intervals=0),  # Refresh every second
    dcc.Graph(id='bpm-graph'),
    dcc.Graph(id='gsr-graph')
])

# Callback to update graphs
@app.callback(
    [Output('bpm-graph', 'figure'),
     Output('gsr-graph', 'figure')],
    [Input('update-interval', 'n_intervals')]
)
def update_graphs(n):
    try:
        # Fetch data from the FastAPI server
        response = requests.get(FASTAPI_URL)
        data = response.json()

        # Convert data to a pandas DataFrame
        df = pd.DataFrame(data)

        # Ensure we have valid data before plotting
        if df.empty:
            return go.Figure(), go.Figure()

        # Parse timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Create BPM graph
        bpm_fig = go.Figure(
            data=go.Scatter(x=df['timestamp'], y=df['bpm'], mode='lines+markers', name="BPM"),
            layout=go.Layout(title="Heart Rate (BPM)", xaxis_title="Time", yaxis_title="BPM")
        )

        # Create GSR graph
        gsr_fig = go.Figure(
            data=go.Scatter(x=df['timestamp'], y=df['gsr'], mode='lines+markers', name="GSR"),
            layout=go.Layout(title="GSR (Stress Level)", xaxis_title="Time", yaxis_title="GSR")
        )

        return bpm_fig, gsr_fig

    except Exception as e:
        print(f"Error: {e}")
        return go.Figure(), go.Figure()


if __name__ == '__main__':
    app.run_server(debug=True)
