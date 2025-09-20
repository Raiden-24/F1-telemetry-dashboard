import streamlit as st
import pandas as pd
import json
from kafka import KafkaConsumer
import time
import subprocess
import sys
import os

# --- Configuration ---
KAFKA_TOPIC = 'telemetry-stream'
KAFKA_SERVER = 'localhost:9092'

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="F1 Live Telemetry",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Anomaly Detector Class (No changes) ---
class AnomalyDetector:
    def __init__(self):
        self.last_speed = 0

    def check_anomalies(self, data):
        anomalies = []
        if data.get('RPM', 0) > 12000:
            anomalies.append(("High RPM Alert", f"Engine RPM critical: {data.get('RPM')} RPM", "error"))
        if data.get('DRS', 0) >= 8 and data.get('Brake'):
            anomalies.append(("DRS Malfunction", "DRS open while braking detected!", "error"))
        if data.get('Brake') and data.get('Speed', 0) < self.last_speed - 15:
            anomalies.append(("Potential Lock-up", f"Rapid speed drop under braking. Speed: {data.get('Speed')} km/h", "warning"))
        self.last_speed = data.get('Speed', 0)
        return anomalies

# --- Main Dashboard Logic ---
def main():
    st.title("F1 Live Telemetry Dashboard")
    st.caption("Driver: HAM | Lap: Pole Lap (2020 Styrian GP)")

    if 'producer_process' not in st.session_state:
        st.session_state.producer_process = None
    
    # THE FIX: Add previous_gear to session_state for tracking shifts
    if 'previous_gear' not in st.session_state:
        st.session_state.previous_gear = 'N'
    
    # Button to start the data stream
    if st.button("▶️ Start Live Telemetry Stream", type="primary"):
        python_executable = sys.executable
        producer_script_path = os.path.join(os.path.dirname(__file__), "producer.py")

        if os.path.exists(producer_script_path):
            st.session_state.producer_process = subprocess.Popen([python_executable, producer_script_path])
            st.success("Telemetry stream started! Listening for data...")
            # Reset anomalies and gear for the new run
            st.session_state.anomalies_log = []
            st.session_state.previous_gear = 'N' 
            time.sleep(2)
        else:
            st.error(f"Error: producer.py not found at {producer_script_path}")

    st.divider()

    # Create placeholders for the live data
    st.header("Live Metrics", anchor=False)
    
    main_metrics_cols = st.columns(3)
    speed_placeholder = main_metrics_cols[0].empty()
    rpm_placeholder = main_metrics_cols[1].empty()
    lap_time_placeholder = main_metrics_cols[2].empty()

    secondary_metrics_cols = st.columns(3)
    gear_placeholder = secondary_metrics_cols[0].empty()
    drs_placeholder = secondary_metrics_cols[1].empty()
    status_placeholder = secondary_metrics_cols[2].empty()
    
    st.subheader("Driver Inputs", anchor=False)
    throttle_placeholder = st.empty()
    brake_placeholder = st.empty()
    
    st.divider()
    
    alerts_placeholder = st.empty()

    # Initialize with default values
    speed_placeholder.metric("Speed", "0 km/h")
    rpm_placeholder.metric("Engine RPM", "0")
    lap_time_placeholder.metric("Lap Time", "0.00 s")
    gear_placeholder.metric("Gear", "N")
    drs_placeholder.metric("DRS", "⚪ INACTIVE")
    status_placeholder.metric("Status", "STANDBY")
    throttle_placeholder.progress(0, text="Throttle")
    brake_placeholder.progress(0, text="Brake")

    # Only try to connect to Kafka if the stream has been started
    if st.session_state.producer_process:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_SERVER,
                auto_offset_reset='latest',
                consumer_timeout_ms=5000, # Increased timeout for stability
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            
            if 'anomaly_detector' not in st.session_state:
                st.session_state.anomaly_detector = AnomalyDetector()
            if 'anomalies_log' not in st.session_state:
                st.session_state.anomalies_log = []

            # The "live" loop
            for message in consumer:
                data = message.value

                # Update metrics
                speed_placeholder.metric("Speed", f"{data.get('Speed', 0)} km/h")
                rpm_placeholder.metric("Engine RPM", f"{data.get('RPM', 0):,}")
                lap_time_placeholder.metric("Lap Time", f"{data.get('Time', 0.0):.2f} s")
                
                # --- THE FIX FOR GEAR SHIFT INDICATION ---
                current_gear = str(data.get('Gear', 'N')) # Use 'Gear' which we renamed in producer.py
                gear_delta = None
                # Check if both current and previous gears are numbers to compare them
                if current_gear.isnumeric() and st.session_state.previous_gear.isnumeric():
                    delta_val = int(current_gear) - int(st.session_state.previous_gear)
                    if delta_val != 0:
                        gear_delta = f"{delta_val: d}" # Format as "+1" or "-1"
                
                # Update the gear metric with the delta
                gear_placeholder.metric("Gear", current_gear, delta=gear_delta)
                # Store the current gear for the next iteration
                st.session_state.previous_gear = current_gear
                # ---------------------------------------------
                
                drs_value = "🟢 ACTIVE" if data.get('DRS', 0) >= 8 else "⚪ INACTIVE"
                drs_placeholder.metric("DRS", drs_value)
                status_placeholder.metric("Status", "STREAMING", "RUNNING")
                
                # Update progress bars (normalized to 0.0-1.0)
                throttle_placeholder.progress(data.get('Throttle', 0) / 100, text=f"Throttle ({data.get('Throttle', 0)}%)")
                brake_val = 1.0 if data.get('Brake') else 0.0
                brake_placeholder.progress(brake_val, text="Brake")

                # Update alerts
                anomalies = st.session_state.anomaly_detector.check_anomalies(data)
                if anomalies:
                    for _, msg, level in anomalies:
                        st.session_state.anomalies_log.insert(0, (msg, level))
                
                with alerts_placeholder.container(border=True):
                    st.subheader("System Alerts", anchor=False)
                    if not st.session_state.anomalies_log:
                        st.info("No anomalies detected. System nominal.")
                    else:
                        for msg, level in st.session_state.anomalies_log[:5]:
                            if level == "error":
                                st.error(msg, icon="🚨")
                            else:
                                st.warning(msg, icon="⚠️")
            
            status_placeholder.metric("Status", "FINISHED", "COMPLETE")
            st.info("Telemetry stream finished.")


        except Exception as e:
            st.error(f"Failed to process stream: {e}")
            st.info("Ensure Docker Kafka container is running and producer has started.")

if __name__ == "__main__":
    main()

