# IoT Smart Indoor Climate and Air Quality Monitor

## Overview

The IoT Smart Indoor Climate and Air Quality Monitor is an Internet of Things (IoT) system designed to continuously monitor indoor environmental conditions and provide short-term predictions using machine learning.

The system measures temperature, relative humidity, and indoor air quality using low-cost environmental sensors connected to an ESP8266-based NodeMCU development board. Sensor readings are transmitted to the ThingSpeak cloud platform, where historical data is stored. A Python-based machine learning pipeline retrieves historical sensor data, trains a Polynomial Regression model, and forecasts environmental conditions for the next one hour.

A web-based dashboard displays both current sensor readings and predicted values, providing users with historical trends and short-term forecasts.

---

## Features

- Continuous monitoring of indoor temperature
- Continuous monitoring of relative humidity
- Indoor air quality monitoring using the MQ135 gas sensor
- Cloud-based data storage using ThingSpeak
- Local LCD display for real-time monitoring
- REST API integration for data retrieval
- Machine learning-based forecasting
- Interactive web dashboard for data visualization
- Historical data analysis

---

## System Architecture

```
                    +----------------+
                    |   DHT11 Sensor |
                    +----------------+
                            |
                            |
                    +----------------+
                    | MQ135 Sensor   |
                    +----------------+
                            |
                            |
                    +----------------+
                    | NodeMCU ESP8266|
                    +----------------+
                            |
                     Wi-Fi Communication
                            |
                            |
                    +----------------+
                    | ThingSpeak     |
                    | Cloud Storage  |
                    +----------------+
                            |
               -----------------------------
               |                           |
               |                           |
      Historical Data              REST API Access
               |                           |
               -----------------------------
                            |
                    Python ML Pipeline
                            |
              Polynomial Regression Model
                            |
                One-Hour Forecast Generation
                            |
                    Web Dashboard (Gradio)
```

---

## Hardware Components

| Component | Purpose |
|------------|---------|
| NodeMCU ESP8266 | Main microcontroller with Wi-Fi connectivity |
| DHT11 | Temperature and humidity sensing |
| MQ135 | Indoor air quality monitoring |
| 16×2 LCD Display (I2C) | Local visualization of sensor readings |
| Breadboard | Circuit prototyping |
| Jumper Wires | Hardware connections |
| USB Power Supply | System power |

---

## Software Stack

### Embedded Development

- Arduino IDE
- ESP8266 Board Package
- DHT Sensor Library
- ThingSpeak Library
- LiquidCrystal_I2C Library

### Machine Learning

- Python
- Google Colab
- NumPy
- Pandas
- Scikit-learn
- Matplotlib

### Cloud Services

- ThingSpeak

### Web Technologies

- Gradio

---

## Data Pipeline

1. Environmental data is collected by the DHT11 and MQ135 sensors.
2. The NodeMCU processes sensor readings.
3. Sensor data is uploaded to ThingSpeak using HTTP requests.
4. Historical data is retrieved from ThingSpeak through its REST API.
5. The data is cleaned and processed using Pandas.
6. Polynomial Regression models are trained on the previous two days of sensor data.
7. The trained models generate forecasts for the next one hour.
8. Historical and predicted values are displayed on a web dashboard.

---

## Machine Learning Model

The forecasting module employs Polynomial Regression to capture nonlinear trends in the collected environmental data.

### Training Data

- Previous 2 days of sensor readings

### Prediction Horizon

- Next 1 hour

### Predicted Variables

- Temperature (°C)
- Temperature (°F)
- Relative Humidity (%)
- Air Quality Index

### Workflow

```
Historical Sensor Data
        │
        ▼
Data Cleaning
        │
        ▼
Feature Engineering
        │
        ▼
Polynomial Regression
        │
        ▼
Model Training
        │
        ▼
One-Hour Forecast
        │
        ▼
Visualization
```

---

## Dashboard

The dashboard provides:

- Current sensor readings
- Historical sensor data
- Forecasted environmental conditions
- Temperature trends
- Humidity trends
- Air quality trends

**Note**

The public deployment is currently unavailable because the IoT device is no longer publishing live sensor data to ThingSpeak.

---

## Repository Structure

```
IoT-Smart-Indoor-Climate-Monitor/
│
├── Arduino/
│   └── mdp.ino
│
├── Machine_Learning/
│   └── Prediction_Model.ipynb
│
├── Dashboard/
│   └── app.py
│
├── Images/
│   ├── hardware.jpg
│   ├── dashboard.png
│   ├── forecast.png
│   └── thingspeak.png
│
├── Report/
│   └── Project_Report.pdf
│
├── requirements.txt
│
└── README.md
```

---

## Potential Applications

### Smart Buildings

- HVAC optimization
- Indoor environmental monitoring
- Predictive climate control

### Hospitals and Healthcare Facilities

- Environmental monitoring in patient rooms
- Controlled storage environments
- Monitoring of isolation wards

### Laboratories

- Regulation of temperature and humidity for sensitive experiments
- Continuous monitoring of laboratory air quality

### Data Centers

- Prevention of overheating
- Humidity regulation for electronic equipment
- Predictive maintenance support

### Warehouses

- Monitoring environmental conditions for sensitive inventory
- Cold storage monitoring

### Educational Institutions

- Classroom environmental monitoring
- Indoor air quality assessment

### Smart Homes

- Home automation integration
- Predictive HVAC control
- Indoor comfort optimization

### Industrial Facilities

- Air quality monitoring
- Detection of hazardous environmental conditions
- Worker safety enhancement

---

## Future Work

The current implementation can be extended in several directions:

- Long Short-Term Memory (LSTM) forecasting
- XGBoost-based regression models
- Transformer-based time series forecasting
- Automatic HVAC control using predicted values
- MQTT-based communication
- ESP32 deployment
- Multi-room monitoring
- Mobile application development
- Docker-based deployment
- Integration with cloud databases
- Anomaly detection for sensor faults
- Reinforcement learning for energy optimization

---

## My Contributions

Although this project originated as a collaborative undergraduate project, my primary contributions included:

- Integration of the IoT device with ThingSpeak Cloud
- Development of the machine learning prediction pipeline
- Historical data processing using Python
- Forecast visualization
- Development of the web dashboard
- REST API integration
- End-to-end deployment of the prediction system

---

## Resources

### Google Colab Notebook

https://colab.research.google.com/drive/1STGGWq2MqBBIlUy76ZFsT9dXE4PaAXZl?usp=sharing

### Live Dashboard

https://51fc01b1f11b65eb6d.gradio.live/

*(Currently unavailable because live sensor data is no longer being published.)*

---

## Authors

- Aaryan Nilesh Kumbhar
- Amudapuram Rishi
- Aviral Sanjeev Kapur
- Vijayasaravanan S U
- T Bala Ezhilselvan

**Faculty Supervisor**

Dr. Bhuvaneswari A

School of Computer Science and Engineering

Vellore Institute of Technology, Chennai

---

## License

This project was developed for academic and educational purposes. It may be used for learning, research, and non-commercial applications with appropriate attribution.
