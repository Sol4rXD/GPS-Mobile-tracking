import math
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import threading
import serial
import time

# Set serial port 1 (BLUEPILL BNO)
PORT_NAME_1 = "/dev/ttyACM0"
# Set serial port 2 (BLUEPILL LORA)
PORT_NAME_2 = "/dev/ttyACM1" 
# Set Baudrate
BAUDRATE = 9600

data_lat = []
data_lon = []
data_yaw = []

data_lat_1 = []
data_lon_1 = []
data_yaw_1 = []

def calculate_adjusted_azimuth(lat1, lon1, lat2, lon2, receiver_orientation_deg):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad

    # Calculate azimuth angle
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    azimuth_rad = math.atan2(y, x)
    azimuth_deg = math.degrees(azimuth_rad)

    adjusted_azimuth_deg = azimuth_deg + receiver_orientation_deg

    if adjusted_azimuth_deg < 0:
        adjusted_azimuth_deg += 360

    return adjusted_azimuth_deg


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c

    return distance

def read_serial_data():
    try:
        time.sleep(1)  
        ser1 = serial.Serial(PORT_NAME_1, BAUDRATE)
        ser2 = serial.Serial(PORT_NAME_2, BAUDRATE)
    except serial.SerialException as e:
        print(f"Serial port opening failed: {e}")
        return

    while True:
        data1 = ser1.readline().decode().strip().split(",")
        data2 = ser2.readline().decode().strip().split(",")

        if len(data1) >= 6:
            data_lat.append(float(data1[0]))
            data_lon.append(float(data1[1]))
            data_yaw.append(float(data1[3]))

        if len(data2) >= 7:
            data_lat_1.append(float(data2[0]))
            data_lon_1.append(float(data2[1]))
    ser.close()
    time.sleep(1)

app = dash.Dash(__name__)

def print_latest_data():
    while True:
        time.sleep(2)  
        print("Latest Data:", data_lat, data_lon, data_yaw)

data_print_thread = threading.Thread(target=print_latest_data)
data_print_thread.daemon = True
data_print_thread.start()

app.layout = html.Div([
    dcc.Graph(id='polar-plot'),
    dcc.Interval(
        id='update-interval',
        interval=2000,
        n_intervals=0
    )
])

def run_dash_app():
    app.run_server(debug=True, use_reloader=False)

dash_thread = threading.Thread(target=run_dash_app)
dash_thread.daemon = True
dash_thread.start()

data_thread = threading.Thread(target=read_serial_data)
data_thread.daemon = True
data_thread.start()

@app.callback(
    Output('polar-plot', 'figure'),
    Input('update-interval', 'n_intervals')
)
def update_polar_plot(n_intervals):
    print('start calculate')
    global data_yaw, data_lat, data_lon, data_lat_1, data_lon_1

    if len(data_lat) == 0 or len(data_lon) == 0 or len(data_yaw) == 0:
        return go.Figure()

    azimuth = calculate_adjusted_azimuth(data_lat[-1], data_lon[-1], data_lat_1[-1], data_lon_1[-1], data_yaw[-1])
    distance = haversine_distance(data_lat[-1], data_lon[-1], data_lat_1[-1], data_lon[-1])

    # Create the polar scatter plot
    fig = go.Figure(go.Scatterpolar(
        r=[20],  
        theta=[azimuth],
        mode='markers',
        marker=dict(size=10, color='red'),
        name='Sensor Location'
    ))

    fig.update_layout(
        title='A2',
        polar=dict(
            angularaxis=dict(
                rotation=90,
                direction='clockwise'
            ),
            radialaxis=dict(
                visible=True,
                range=[0, 45],  # Adjust the range as needed based on the maximum distance you expect
            ),
        ),
        showlegend=False
    )

    return fig

# Wait for both threads to complete
dash_thread.join()
data_thread.join()
