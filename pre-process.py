import fastf1
import json
import pandas as pd

def save_telemetry_data():
    """
    Fetches telemetry data once and saves it to a JSON file
    to be used by the deployed Streamlit app.
    """
    print("Loading telemetry data from FastF1...")
    # Using a cache is good practice and speeds up subsequent runs
    fastf1.Cache.enable_cache('cache') 
    
    try:
        session = fastf1.get_session(2020, 'Styrian Grand Prix', 'Q')
        session.load(telemetry=True, laps=True)
        lap = session.laps.pick_driver('HAM').pick_fastest()
        telemetry = lap.get_car_data().add_distance()
        
        print("Data loaded. Processing...")
        
        telemetry = telemetry[['Time', 'Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS']]
        telemetry['Time'] = telemetry['Time'].dt.total_seconds()
        telemetry.rename(columns={'nGear': 'Gear'}, inplace=True)
        
        records = telemetry.to_dict('records')
        
        with open('telemetry_data.json', 'w') as f:
            json.dump(records, f)
            
        print("Successfully saved data to telemetry_data.json")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    save_telemetry_data()

