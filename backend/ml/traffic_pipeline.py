"""Reproducible training pipeline for explicitly synthetic traffic scenarios."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURES = ["hour", "day_of_week", "weather", "vehicle_density", "road_category", "surface"]


@dataclass(frozen=True)
class ScenarioDataset:
    frame: pd.DataFrame
    provenance: str = "synthetic_scenario"

    @classmethod
    def generate(cls, rows: int = 2_000, seed: int = 42) -> "ScenarioDataset":
        if rows < 100:
            raise ValueError("at least 100 rows are required")
        rng = np.random.default_rng(seed)
        hour = np.arange(rows) % 24
        day = (np.arange(rows) // 24) % 7
        weather = rng.choice(["clear", "rain", "fog"], rows, p=[0.68, 0.22, 0.10])
        road = rng.choice(["local", "arterial", "highway"], rows, p=[0.35, 0.45, 0.20])
        surface = rng.choice(["good", "moderate", "poor"], rows, p=[0.65, 0.25, 0.10])
        density = rng.uniform(0.15, 0.95, rows)
        morning = np.exp(-((hour - 9) ** 2) / 7)
        evening = np.exp(-((hour - 18) ** 2) / 8)
        weekday = (day < 5).astype(float)
        weather_effect = np.select([weather == "rain", weather == "fog"], [12.0, 18.0], 0.0)
        road_effect = np.select([road == "arterial", road == "highway"], [8.0, 4.0], 2.0)
        surface_effect = np.select([surface == "moderate", surface == "poor"], [5.0, 12.0], 0.0)
        congestion = (
            8
            + 31 * morning * weekday
            + 36 * evening * weekday
            + 34 * density
            + weather_effect
            + road_effect
            + surface_effect
            + rng.normal(0, 2.0, rows)
        )
        frame = pd.DataFrame(
            {
                "timestamp_index": np.arange(rows),
                "hour": hour,
                "day_of_week": day,
                "weather": weather,
                "vehicle_density": density,
                "road_category": road,
                "surface": surface,
                "congestion": np.clip(congestion, 0, 100),
            }
        )
        return cls(frame=frame)


@dataclass(frozen=True)
class ModelMetric:
    name: str
    mae: float
    rmse: float
    r2: float


@dataclass(frozen=True)
class TrainingReport:
    provenance: str
    dataset_fingerprint: str
    training_rows: int
    test_rows: int
    metrics: tuple[ModelMetric, ...]


@dataclass(frozen=True)
class TrafficPrediction:
    congestion_percent: float
    congestion_level: str
    estimated_delay_min: float
    expected_travel_time_min: float
    model_name: str
    provenance: str
    dataset_fingerprint: str


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("numeric", StandardScaler(), ["hour", "day_of_week", "vehicle_density"]),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                ["weather", "road_category", "surface"],
            ),
        ]
    )


def _fit_models(dataset: ScenarioDataset, seed: int):
    frame = dataset.frame.sort_values("timestamp_index").reset_index(drop=True)
    split = int(len(frame) * 0.8)
    train, test = frame.iloc[:split], frame.iloc[split:]
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=80, max_depth=10, random_state=seed, n_jobs=1
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=80, max_depth=3, random_state=seed
        ),
    }
    metrics: list[ModelMetric] = []
    fitted: dict[str, Pipeline] = {}
    for name, estimator in models.items():
        pipeline = Pipeline([("preprocess", _preprocessor()), ("model", estimator)])
        pipeline.fit(train[FEATURES], train["congestion"])
        fitted[name] = pipeline
        prediction = pipeline.predict(test[FEATURES])
        metrics.append(
            ModelMetric(
                name=name,
                mae=round(float(mean_absolute_error(test["congestion"], prediction)), 6),
                rmse=round(float(mean_squared_error(test["congestion"], prediction) ** 0.5), 6),
                r2=round(float(r2_score(test["congestion"], prediction)), 6),
            )
        )
    fingerprint = hashlib.sha256(
        frame.to_csv(index=False, float_format="%.8f").encode("utf-8")
    ).hexdigest()
    report = TrainingReport(
        provenance=dataset.provenance,
        dataset_fingerprint=fingerprint,
        training_rows=len(train),
        test_rows=len(test),
        metrics=tuple(metrics),
    )
    return report, fitted


def train_and_evaluate(dataset: ScenarioDataset, seed: int = 42) -> TrainingReport:
    report, _models = _fit_models(dataset, seed)
    return report


class ScenarioTrafficService:
    """Lazy-use synthetic model with its evaluation report attached to outputs."""

    def __init__(self, rows: int = 2_000, seed: int = 42) -> None:
        self.dataset = ScenarioDataset.generate(rows=rows, seed=seed)
        self.report, self.models = _fit_models(self.dataset, seed)
        self.model_name = min(self.report.metrics, key=lambda metric: metric.rmse).name

    def predict(
        self,
        *,
        hour: int,
        day_of_week: int,
        weather: str,
        vehicle_density: float,
        road_category: str,
        surface: str,
        base_travel_time_min: float,
    ) -> TrafficPrediction:
        sample = pd.DataFrame(
            [
                {
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "weather": weather,
                    "vehicle_density": vehicle_density,
                    "road_category": road_category,
                    "surface": surface,
                }
            ]
        )
        value = float(np.clip(self.models[self.model_name].predict(sample)[0], 0, 100))
        if value < 30:
            level = "low"
        elif value < 55:
            level = "moderate"
        elif value < 75:
            level = "high"
        else:
            level = "severe"
        delay = base_travel_time_min * (value / 100) * 0.65
        return TrafficPrediction(
            congestion_percent=round(value, 2),
            congestion_level=level,
            estimated_delay_min=round(delay, 2),
            expected_travel_time_min=round(base_travel_time_min + delay, 2),
            model_name=self.model_name,
            provenance="synthetic_scenario_model",
            dataset_fingerprint=self.report.dataset_fingerprint,
        )
