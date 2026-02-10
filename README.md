
## FitPulse: Health Anomaly Detection
FitPulse is a health analytics platform that utilizes advanced anomaly detection techniques to analyze fitness watch data, enabling users and healthcare providers to proactively monitor health metrics and identify early warning signs of irregular heart rate, sleep disturbances, and abnormal activity levels.

### Project Statement
With the surge in wearable fitness devices, vast amounts of health-related time-series data are generated daily. FitPulse leverages advanced anomaly detection techniques to intelligently analyze this data, flagging unusual health patterns and supporting preventive healthcare and personalized wellness insights.

### Features
- Upload fitness watch data (CSV format)
- Automatic preprocessing and normalization
- Time-series feature extraction (TSFresh)
- Trend modeling and anomaly detection (Prophet, clustering)
- Rule-based and model-based anomaly flagging
- Interactive Streamlit dashboard for visualizing trends and anomalies
- Downloadable reports for users and healthcare professionals

### Workflow
1. **Upload Data**: Import health metrics from fitness trackers
2. **Preprocessing**: Clean, normalize, and resample data
3. **Feature Extraction & Modeling**: Extract features, model trends, cluster patterns
4. **Anomaly Detection**: Flag unusual values using thresholds and models
5. **Visualization & Reporting**: Explore results in dashboard, export reports

### Usage
1. Clone the repository:
	```
	git clone https://github.com/sheethalkaran/FitPulse-health-anomaly-detection.git
	cd FitPulse-health-anomaly-detection
	```
2. Install dependencies:
	```
	pip install -r requirements.txt
	```
3. Run the Streamlit app:
	```
	streamlit run home.py
	```
4. Upload your fitness watch CSV file and explore the dashboard.

---

