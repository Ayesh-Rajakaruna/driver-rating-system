# 🚗 AI-Based Driver Rating System for Safety Measurement Using Multi-Sensor Data

> **MSc Software Architecture Dissertation** — University of Moratuwa, Sri Lanka  
> Author: Y.A.A.W. Rajakaruna (258278U) | Supervisor: Dr. Chathura De Silva

An AI-powered, real-time driver rating system that evaluates driving behavior using **IMU** (Inertial Measurement Unit) and **GPS** sensor data. The system classifies driving events, computes objective safety scores, and generates interpretable, human-readable safety reports for drivers, fleet managers, and transport authorities.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Detected Driving Events](#detected-driving-events)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Evaluation Metrics](#evaluation-metrics)
- [Ethical and Privacy Considerations](#ethical-and-privacy-considerations)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [References](#references)
- [License](#license)

---

## Overview

Road traffic accidents caused by unsafe driving behavior remain a major global concern. Traditional monitoring systems rely on coarse GPS-based telematics or manual observation — both of which fail to capture fine-grained driving dynamics in real time.

This system addresses those limitations by:
- Fusing **high-frequency IMU data** (accelerometer + gyroscope) with **GPS context** (speed, location, trajectory)
- Applying **supervised machine learning** to classify driving behavior
- Producing **explainable safety scores** with actionable, natural-language feedback

---

## Key Features

- 📡 **Real-time multi-sensor data acquisition** — synchronized IMU + GPS streams
- 🧠 **AI-based behavior classification** — Random Forest / LSTM models
- 📊 **Composite safety scoring** — weighted event-severity rating system
- 📝 **Interpretable safety reports** — human-readable NLG-based driver feedback
- 🔍 **Explainable AI (XAI)** — SHAP-based feature attribution for transparency
- 🔒 **Privacy-preserving** — full data anonymization pipeline
- 🧩 **Modular architecture** — each component is independently extensible

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Sensor Layer                       │
│         IMU (Accelerometer + Gyroscope) + GPS           │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│               Data Acquisition Pipeline                  │
│    Timestamping · Synchronization · Buffering           │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Data Pre-Processing                     │
│    Noise Filtering · Outlier Removal · Segmentation     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Feature Engineering                     │
│    IMU: Mean, Variance, Jerk, Peak Acceleration         │
│    GPS: Speed Stats, Trajectory Metrics                 │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Machine Learning Framework                  │
│         Random Forest  /  Sequence-Based LSTM           │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 Driver Rating Logic                      │
│       Composite Safety Score · Event Weighting          │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Report Generation Module                    │
│    SHAP Explanations · NLG Safety Reports · Dashboard   │
└─────────────────────────────────────────────────────────┘
```

---

## Detected Driving Events

| Event | Sensor Signal | Risk Level |
|---|---|---|
| Harsh Braking | High negative longitudinal acceleration (IMU) | 🔴 High |
| Sudden Acceleration | High positive longitudinal acceleration (IMU) | 🟠 Medium |
| Sharp Cornering | High lateral acceleration (IMU) | 🟠 Medium |
| Overspeeding | GPS speed threshold exceeded | 🔴 High |
| Erratic Lane Changes | Combined lateral + angular velocity (IMU) | 🟠 Medium |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Hardware | IMU Module (Accelerometer/Gyroscope), GPS Module, Arduino/ESP32 |
| Language | Python 3.x |
| Data Processing | NumPy, Pandas, SciPy |
| Machine Learning | Scikit-learn (Random Forest), TensorFlow / PyTorch (LSTM) |
| Explainability | SHAP |
| Visualization | Matplotlib, Seaborn |
| Report Generation | NLG (template-based / LLM-assisted) |
| Version Control | Git / GitHub |

---

## Project Structure

```
driver-rating-system/
│
├── data/
│   ├── raw/                    # Raw sensor recordings
│   ├── processed/              # Cleaned and segmented data
│   └── labeled/                # Annotated driving event data
│
├── src/
│   ├── acquisition/            # Sensor data collection scripts
│   ├── preprocessing/          # Noise filtering, synchronization
│   ├── features/               # Feature extraction and engineering
│   ├── models/                 # ML model training and inference
│   ├── rating/                 # Driver scoring logic
│   └── reports/                # Safety report generation
│
├── notebooks/                  # Exploratory data analysis
├── tests/                      # Unit and integration tests
├── config/                     # Configuration files
├── outputs/
│   ├── models/                 # Saved trained models
│   └── reports/                # Generated driver safety reports
│
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager
- IMU + GPS hardware (Arduino/ESP32 compatible) — *for live data collection*
- Git

### Installation

1. **Clone the repository and switch to the AI branch:**

   ```bash
   git clone https://github.com/Ayesh-Rajakaruna/driver-rating-system.git
   cd driver-rating-system
   git checkout ai
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Edit `config/settings.yaml` to adjust:
- Sensor sampling rates
- Feature window sizes
- Safety score thresholds
- Report output format

---

## Usage

### 1. Data Collection

```bash
python src/acquisition/collect_data.py --output data/raw/session_01.csv
```

### 2. Pre-processing

```bash
python src/preprocessing/preprocess.py --input data/raw/session_01.csv --output data/processed/
```

### 3. Feature Extraction

```bash
python src/features/extract_features.py --input data/processed/ --output data/labeled/
```

### 4. Model Training

```bash
python src/models/train.py --data data/labeled/ --model random_forest
```

### 5. Driver Rating & Report Generation

```bash
python src/rating/score_driver.py --session data/processed/session_01.csv
python src/reports/generate_report.py --driver-id DRV001 --output outputs/reports/
```

---

## Machine Learning Pipeline

### Feature Engineering

Features are extracted from sliding windows over sensor streams:

**IMU Features:**
- Mean, standard deviation, and variance of acceleration axes
- Jerk (rate of change of acceleration)
- Peak acceleration values
- Angular velocity statistics

**GPS Features:**
- Speed mean, max, and variance
- Trajectory smoothness metrics
- Overspeeding frequency

### Models

| Model | Use Case | Strength |
|---|---|---|
| **Random Forest** | Behavior classification | High interpretability, robust to noise |
| **LSTM** | Sequential driving patterns | Captures temporal dependencies |

### Driver Safety Score

The composite safety score is computed as:

```
Safety Score (0–100) = 100 − Σ(Event_Weight × Event_Frequency)
```

Each event type is weighted by its severity and frequency within the evaluation window.

---

## Evaluation Metrics

| Metric | Description |
|---|---|
| Accuracy | Overall correct classification rate |
| Precision | Fraction of flagged events that are true positives |
| Recall | Fraction of actual events correctly detected |
| F1-Score | Harmonic mean of precision and recall |
| Confusion Matrix | Class-wise error distribution |

---

## Ethical and Privacy Considerations

- All collected driving data is **anonymized** before processing and storage.
- Driver identity is decoupled from behavioral records.
- Data collection follows ethical guidelines of the University of Moratuwa.
- The system is designed for **coaching and safety improvement**, not punitive surveillance.

---

## Limitations

- Dataset size and diversity are constrained by available collection sessions.
- Sensor placement variability can affect feature consistency across vehicles.
- Extreme weather conditions and ADAS-equipped vehicles are outside the current scope.
- The system evaluates driving safety but does not predict individual accidents.

---

## Future Enhancements

- [ ] Integration of additional sensors (e.g., camera, LiDAR)
- [ ] Deep learning models (CNN-LSTM hybrid) for improved accuracy
- [ ] Real-time alert mechanisms for in-trip notifications
- [ ] Mobile application for driver self-monitoring
- [ ] Large-scale deployment studies with fleet operators
- [ ] Integration with insurance telematics platforms

---

## References

1. H. Eren et al., "Estimating driving behavior by a smartphone," *IEEE IV Symp.*, 2012.
2. E. Mantouka et al., "Smartphone sensing for understanding driving behavior," *Journal of Traffic and Transportation Engineering*, 2021.
3. S. Yaqoob et al., "AI-driven driver behavior assessment through vehicle and health monitoring," *IEEE Access*, 2024.
4. G. Singh et al., "A smartphone based technique to monitor driving behavior using DTW and crowdsensing," *Pervasive and Mobile Computing*, 2017.
5. S. K. Kwon et al., "Driving behavior classification using CNN-LSTM approaches and V2X communication," *Applied Sciences*, 2021.
6. K. McDonnell, "AI approaches for driver behaviour and telematics-driven risk assessment," *Ph.D. Dissertation, University of Limerick*, 2025.
7. S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," *NeurIPS*, 2017.
8. T. Young et al., "Recent trends in deep learning based NLP," *IEEE Computational Intelligence Magazine*, 2018.

---

## License

This project was developed as part of an MSc dissertation at the **University of Moratuwa, Sri Lanka**. All rights reserved by the author.

---

<p align="center">
  Developed with ❤️ at University of Moratuwa · Department of Computer Science and Engineering
</p>
