import fastf1
import pandas as pd
import time
import json
from kafka import KafkaProducer
import sys

# --- Configuration ---
# This is the "channel" or "topic" our car will broadcast data to.
KAFKA_TOPIC = 'telemetry-stream'
# This is the address of the Kafka server we started with Docker.
KAFKA_SERVER = 'localhost:9092'

# --- Functions ---
def get_telemetry_data():
    """
    Fetches and prepares telemetry data for a specific, exciting F1 lap.
    We'll use Lewis Hamilton's incredible 2020 Styrian GP pole lap in the wet.
    """
    print("Loading telemetry data from FastF1...")
    # Using the cache makes subsequent runs much faster.
    fastf1.Cache.enable_cache('cache') 
    
    try:
        # Load the session data
        session = fastf1.get_session(2020, 'Styrian Grand Prix', 'Q')
        session.load(telemetry=True, laps=True) # Ensure telemetry is loaded
        
        # Get the specific lap for HAM's fastest qualifying lap
        lap = session.laps.pick_driver('HAM').pick_fastest()
        telemetry = lap.get_car_data().add_distance()
        
        print(f"Data loaded successfully for {lap.Driver} Lap {lap.LapNumber} (Time: {lap.LapTime}).")
        
        # We select only the columns we need for our dashboard.
        telemetry = telemetry[['Time', 'Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS', 'Distance']]
        
        # Convert the 'Time' column from a timedelta object to total seconds (a float).
        telemetry['Time'] = telemetry['Time'].dt.total_seconds()
        # Rename 'nGear' to 'Gear' for a cleaner name.
        telemetry.rename(columns={'nGear': 'Gear'}, inplace=True)
        
        return telemetry.to_dict('records') # Convert the DataFrame to a list of dictionaries.

    except Exception as e:
        print(f"Error loading data from FastF1: {e}")
        print("This might be due to a network issue or the session data not being available.")
        return None

def create_kafka_producer():
    """Creates and returns a Kafka producer, with retry logic for connection."""
    print(f"Attempting to connect to Kafka at {KAFKA_SERVER}...")
    try:
        # The value_serializer tells the producer how to convert our data (a Python dict)
        # into bytes that Kafka can understand. We use JSON for this.
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_SERVER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Successfully connected to Kafka.")
        return producer
    except Exception as e:
        print(f"FATAL ERROR: Could not connect to Kafka. Is the Docker container running?")
        print(f"Error details: {e}")
        # sys.exit(1) exits the script if we can't connect.
        sys.exit(1)

# --- Main Execution ---
if __name__ == "__main__":
    telemetry_records = get_telemetry_data()
    
    if telemetry_records:
        kafka_producer = create_kafka_producer()
        
        print("\n--- Starting Live Telemetry Stream ---")
        # We loop through each row (timestamp) of the telemetry data.
        for record in telemetry_records:
            # Add a 'Timestamp' key for our anomaly detector to use.
            record['Timestamp'] = time.time()
            
            # Send the record to our Kafka topic.
            kafka_producer.send(KAFKA_TOPIC, record)
            
            # Print a small summary to the console.
            print(f"Sent: Time={record['Time']:.2f}s, Speed={record['Speed']}km/h, RPM={record['RPM']}, Gear={record['Gear']}")
            
            # This delay simulates the real-time nature of the data stream.
            time.sleep(0.05) 
            
        print("\n--- Telemetry Stream Finished ---")
        kafka_producer.flush() # Ensure all messages are sent before exiting.
        kafka_producer.close()

