import dash
from dash import dcc, html
from dash.dependencies import Input, Output, Interval
import redis
import json
import plotly.graph_objs as go

# Redis configuration
REDIS_HOST = "localhost"  # Change to your Redis host
REDIS_PORT = 6379  # Change to your Redis port
REDIS_KEY = "jorgesilva-proj3-output"

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Redis Data Dashboard"

# Layout
app.layout = html.Div(
    [
        html.H1("Real-Time Redis Data Dashboard", style={"textAlign": "center"}),
        dcc.Graph(id="memory-caching-graph"),
        dcc.Graph(id="cpu-usage-graph"),
        dcc.Interval(
            id="update-interval",
            interval=5 * 1000,  # Update every 5 seconds
            n_intervals=0,
        ),
    ]
)


# Callback to update the graphs
@app.callback(
    [Output("memory-caching-graph", "figure"), Output("cpu-usage-graph", "figure")],
    [Input("update-interval", "n_intervals")],
)
def update_graphs(n_intervals):
    try:
        # Fetch data from Redis
        data = r.get(REDIS_KEY)
        if data:
            data_dict = json.loads(data)

            # Memory caching figure
            memory_caching_fig = go.Figure(
                data=[
                    go.Indicator(
                        mode="gauge+number",
                        value=data_dict.get("percent-memory-caching", 0),
                        title={"text": "Memory Caching (%)"},
                        gauge={"axis": {"range": [0, 100]}},
                    )
                ]
            )

            # CPU usage figure
            cpu_keys = [
                key for key in data_dict if key.startswith("avg-util-cpu_percent")
            ]
            cpu_values = [data_dict[key] for key in cpu_keys]
            cpu_cores = [key.split("-")[-1] for key in cpu_keys]

            cpu_usage_fig = go.Figure(
                data=[
                    go.Bar(
                        x=cpu_cores,
                        y=cpu_values,
                        text=[f"{v:.2f}%" for v in cpu_values],
                        textposition="auto",
                    )
                ]
            )
            cpu_usage_fig.update_layout(
                title="CPU Usage by Core (%)",
                xaxis_title="CPU Core",
                yaxis_title="Usage (%)",
            )

            return memory_caching_fig, cpu_usage_fig
        else:
            raise Exception("No data found in Redis")
    except Exception as e:
        # Handle errors (e.g., Redis connection issue, missing data)
        memory_caching_fig = go.Figure(
            data=[
                go.Indicator(
                    mode="number", value=0, title={"text": "Memory Caching (%)"}
                )
            ]
        )
        cpu_usage_fig = go.Figure()
        cpu_usage_fig.update_layout(
            title="Error fetching CPU data",
            xaxis_title="CPU Core",
            yaxis_title="Usage (%)",
        )
        return memory_caching_fig, cpu_usage_fig


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
