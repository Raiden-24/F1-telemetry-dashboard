**F1 Real-Time Telemetry & Anomaly Detection Dashboard**


**🚀 Project Overview**

This project is a high-fidelity simulation of a real-time Formula 1 telemetry data pipeline, built to showcase modern data engineering and visualization techniques. It ingests data from a source, streams it through a message broker, and displays it on a live, interactive dashboard that includes a real-time anomaly detection system.

This project was developed as a portfolio piece for a Software Engineering placement application with Red Bull Technology, demonstrating skills directly relevant to the high-performance, data-driven environment of motorsport.

**Core Features**
Live Telemetry Simulation: Replays a real F1 lap (Lewis Hamilton's 2020 Styrian GP pole lap) with live-updating metrics.

Real-time Anomaly Detection: A custom engine analyzes the incoming data stream to flag critical events like engine over-revs, DRS malfunctions, and potential wheel lock-ups under braking.

Interactive Dashboard: A clean, flicker-free user interface built with Streamlit that displays Speed, RPM, Gear (with shift indication), Throttle/Brake inputs, and live system alerts.

User-Controlled Stream: The data stream can be started on-demand directly from the web interface.

**🏛️ System Architecture**
This project has two distinct operational modes, demonstrating adaptability for both local development and cloud deployment.

**1. Local Architecture (Full Data Pipeline)**
The full version of the project runs on a local machine and utilizes a complete, multi-part data pipeline:

Data Producer (producer.py): A Python script that uses the fastf1 library to fetch real F1 telemetry data. It then acts as a live source, sending each data point as a message.

Message Broker (Kafka): An Apache Kafka server, containerized with Docker, serves as the robust, high-throughput message bus that receives data from the producer.

Stream Consumer & Dashboard (streamlit_dashboard.py): The Streamlit application connects to the Kafka topic, consumes the live data stream, runs it through the anomaly detection engine, and updates the UI elements in real-time.

**2. Deployed Architecture (Simulated Replay)**
To enable hosting on Streamlit Community Cloud (which does not support Docker), this version simulates the live stream:

Data Pre-processing (pre_process_data.py): A script is run once to fetch the F1 data and save it to a static telemetry_data.json file.

Simulated Stream (streamlit_dashboard_deploy.py): The deployed Streamlit application reads the JSON file and iterates through it with a time delay, perfectly replicating the experience of a live data feed without the need for a live Kafka backend.

**🛠️ Technologies Used**
Programming Language: Python

Dashboard Framework: Streamlit

Real-Time Streaming: Apache Kafka

Containerization: Docker & Docker Compose

Data Manipulation: Pandas

F1 Data Source: FastF1 Library

**⚙️ How to Run (Local Version)**
To run the full, local version of this project with the live Kafka pipeline:

Prerequisites:

Docker Desktop installed and running.

Python 3.10+ and a virtual environment.

Clone the Repository:

git clone [https://github.com/your-username/f1-telemetry-dashboard.git](https://github.com/your-username/f1-telemetry-dashboard.git)
cd f1-telemetry-dashboard

Set up the Environment:

**# Create and activate a virtual environment**
python -m venv venv
venv\Scripts\activate

**# Install the required Python libraries**
pip install -r requirements.txt

Launch the Kafka Server:

# This will start the Kafka container in the background
docker-compose up -d

Wait about 15 seconds, then verify the container is running with docker ps.

Run the Dashboard:

streamlit run streamlit_dashboard.py

A browser tab will open with the dashboard.

Start the Stream:

Click the "▶️ Start Live Telemetry Stream" button in the application to begin the data flow.
