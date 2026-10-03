"""
AI-Based Smart Parking Management System
Machine Learning Models Module
"""

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def generate_dataset(n_samples=2000):
    np.random.seed(42)
    time          = np.random.randint(0, 24, n_samples)
    day           = np.random.randint(0, 7,  n_samples)
    num_cars      = np.random.randint(0, 101, n_samples)
    traffic_level = np.random.randint(0, 3,  n_samples)

    peak_boost = np.where(
        ((time >= 8)  & (time <= 10)) |
        ((time >= 17) & (time <= 19)) |
        (day >= 5), 15, 0
    ).astype(int)

    adjusted_cars = np.clip(num_cars + peak_boost, 0, 100)
    status = np.where(adjusted_cars < 40, 0, np.where(adjusted_cars < 70, 1, 2))

    X = np.column_stack([time, day, num_cars, traffic_level])
    return X, status, num_cars, traffic_level, time


class ParkingMLSystem:
    STATUS_LABELS  = {0: "Available", 1: "Moderate", 2: "Full"}
    AREA_LABELS    = {0: "Area A – Less Crowded", 1: "Area B – Moderate", 2: "Area C – Highly Crowded"}
    AREA_RECOMMEND = {
        0: ("A", "✅ Area A is your best bet – low crowd, easy parking!"),
        1: ("B", "⚠️  Area B has moderate occupancy – park quickly."),
        2: ("C", "🔴 Area C is highly crowded – consider Area A or B."),
    }

    def __init__(self):
        self.lr_model    = None
        self.rf_model    = None
        self.km_model    = None
        self.ts_model    = None
        self.scaler_km   = StandardScaler()
        self.lr_accuracy = 0.0
        self.rf_accuracy = 0.0
        self._cluster_map = {}
        self._hourly_avg  = np.zeros(24)

    def train_all_models(self):
        print("🔄 Generating synthetic dataset...")
        X, y, num_cars, traffic_level, time_arr = generate_dataset(2000)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print("🧠 Training Logistic Regression...")
        self.lr_model = LogisticRegression(max_iter=500, random_state=42)
        self.lr_model.fit(X_train, y_train)
        self.lr_accuracy = round(accuracy_score(y_test, self.lr_model.predict(X_test)) * 100, 2)

        print("🌲 Training Random Forest...")
        self.rf_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        self.rf_model.fit(X_train, y_train)
        self.rf_accuracy = round(accuracy_score(y_test, self.rf_model.predict(X_test)) * 100, 2)

        print("📊 Training K-Means Clustering...")
        km_features = np.column_stack([num_cars, traffic_level])
        km_scaled   = self.scaler_km.fit_transform(km_features)
        self.km_model = KMeans(n_clusters=3, random_state=42, n_init=10)
        self.km_model.fit(km_scaled)
        centroids  = self.km_model.cluster_centers_
        sorted_idx = np.argsort(centroids[:, 0])
        self._cluster_map = {int(sorted_idx[i]): i for i in range(3)}

        print("📈 Training Time Series Forecaster...")
        self._hourly_avg = np.array([
            np.mean(num_cars[time_arr == h]) if np.any(time_arr == h) else 50
            for h in range(24)
        ])
        X_ts = np.arange(24).reshape(-1, 1)
        self.ts_model = LinearRegression()
        self.ts_model.fit(X_ts, self._hourly_avg)

        print(f"\n✅ All models trained!")
        print(f"   LR Accuracy: {self.lr_accuracy}%")
        print(f"   RF Accuracy: {self.rf_accuracy}%\n")

    def predict_lr(self, time_hour, day, num_cars, traffic_level):
        X     = np.array([[time_hour, day, num_cars, traffic_level]])
        pred  = int(self.lr_model.predict(X)[0])
        proba = self.lr_model.predict_proba(X)[0]
        return {
            "status": self.STATUS_LABELS[pred],
            "status_code": pred,
            "confidence": round(float(max(proba)) * 100, 1),
            "probabilities": {
                "Available": round(float(proba[0]) * 100, 1),
                "Moderate":  round(float(proba[1]) * 100, 1),
                "Full":      round(float(proba[2]) * 100, 1),
            }
        }

    def predict_rf(self, time_hour, day, num_cars, traffic_level):
        X     = np.array([[time_hour, day, num_cars, traffic_level]])
        pred  = int(self.rf_model.predict(X)[0])
        proba = self.rf_model.predict_proba(X)[0]
        return {
            "status": self.STATUS_LABELS[pred],
            "status_code": pred,
            "confidence": round(float(max(proba)) * 100, 1),
            "probabilities": {
                "Available": round(float(proba[0]) * 100, 1),
                "Moderate":  round(float(proba[1]) * 100, 1),
                "Full":      round(float(proba[2]) * 100, 1),
            }
        }

    def predict_cluster(self, num_cars, traffic_level):
        X        = np.array([[num_cars, traffic_level]])
        X_scaled = self.scaler_km.transform(X)
        raw      = int(self.km_model.predict(X_scaled)[0])
        mapped   = self._cluster_map.get(raw, 1)
        area_code, recommendation = self.AREA_RECOMMEND[mapped]
        return {
            "cluster_label": self.AREA_LABELS[mapped],
            "cluster_id": mapped,
            "recommended_area": area_code,
            "recommendation": recommendation,
        }

    def predict_time_series(self, current_hour, num_hours_ahead=6):
        forecasts = []
        for i in range(1, num_hours_ahead + 1):
            future_hour = (current_hour + i) % 24
            hist_val = float(self._hourly_avg[future_hour])
            lr_val   = float(self.ts_model.predict([[future_hour]])[0])
            blended  = round(max(0.0, min(100.0, 0.6 * hist_val + 0.4 * lr_val)), 1)

            if blended < 40:   demand, color = "Low",    "#00ff88"
            elif blended < 70: demand, color = "Medium", "#ffd700"
            else:              demand, color = "High",   "#ff4d6d"

            forecasts.append({
                "hour": future_hour,
                "hour_label": f"{future_hour:02d}:00",
                "cars": blended,
                "demand": demand,
                "color": color,
            })
        return forecasts

    def predict_all(self, time_hour, day, num_cars, traffic_level):
        lr = self.predict_lr(time_hour, day, num_cars, traffic_level)
        rf = self.predict_rf(time_hour, day, num_cars, traffic_level)
        km = self.predict_cluster(num_cars, traffic_level)
        ts = self.predict_time_series(time_hour, num_hours_ahead=6)

        agreement = (
            "🎯 Both models AGREE" if lr["status"] == rf["status"]
            else "⚡ Models DISAGREE – RF is more accurate"
        )
        days_map = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
                    4:"Friday",5:"Saturday",6:"Sunday"}
        return {
            "lr_status": lr["status"], "lr_status_code": lr["status_code"],
            "lr_confidence": lr["confidence"], "lr_proba": lr["probabilities"],
            "lr_accuracy": self.lr_accuracy,
            "rf_status": rf["status"], "rf_status_code": rf["status_code"],
            "rf_confidence": rf["confidence"], "rf_proba": rf["probabilities"],
            "rf_accuracy": self.rf_accuracy,
            "agreement": agreement,
            "cluster_label": km["cluster_label"], "cluster_id": km["cluster_id"],
            "recommended_area": km["recommended_area"], "recommendation": km["recommendation"],
            "forecast": ts,
            "day_name": days_map.get(day, "Monday"),
            "time_hour": time_hour, "num_cars": num_cars, "traffic_level": traffic_level,
        }


if __name__ == "__main__":
    system = ParkingMLSystem()
    system.train_all_models()
    result = system.predict_all(9, 1, 55, 2)
    for k, v in result.items():
        print(f"  {k}: {v}")
