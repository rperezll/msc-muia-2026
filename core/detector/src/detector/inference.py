from __future__ import annotations

import json
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from shared_lib.config import keras_plant_dir
from shared_lib.logger import get_logger

log = get_logger("inference")


class AnomalyDetector:
    """Carga los artefactos de una planta y expone predicción de anomalías"""

    def __init__(self, plant_id: int, threshold_key: str = "threshold") -> None:
        plant_dir = keras_plant_dir(plant_id)

        with open(plant_dir / "config_solar.json", encoding="utf-8") as f:
            model_config: dict = json.load(f)

        self.features: list[str] = model_config["features"]
        self.time_steps: int = model_config["time_steps"]
        self.threshold: float = model_config.get(threshold_key, model_config["threshold"])
        self._sun_threshold: float = model_config.get("sun_threshold", 0.1)
        self._scoring_strategy: str = model_config["scoring_strategy"]
        self._power_idx: list[int] = model_config.get("scoring_power_idx", [])
        self._mlp_target_idx: int = model_config.get("mlp_head_target_idx", 0)

        if "IRRADIATION" not in self.features:
            raise ValueError(f"plant_{plant_id}: 'IRRADIATION' no está en features")
        self._irr_idx: int = self.features.index("IRRADIATION")

        self._model: tf.keras.Model = tf.keras.models.load_model(
            plant_dir / "model_lstm_solar.keras"
        )
        self._mlp_head: tf.keras.Model = tf.keras.models.load_model(
            plant_dir / "model_mlp_head.keras"
        )
        self._scaler = joblib.load(plant_dir / "scaler_solar.pkl")

        bottleneck_idx: int = model_config["bottleneck_layer_idx"]
        self._encoder = tf.keras.Model(
            inputs=self._model.inputs,
            outputs=self._model.layers[bottleneck_idx].output,
        )

        log.info(
            "Modelo cargado — plant_id=%d, features=%d, time_steps=%d, scoring=%s, threshold=%.6f",
            plant_id,
            len(self.features),
            self.time_steps,
            self._scoring_strategy,
            self.threshold,
        )

    def predict(self, window: np.ndarray) -> tuple[float, bool]:
        if self._is_night(window):
            return 0.0, False
        scaled = self._scale(window)
        error = self._reconstruction_error(scaled)
        score = self._score(scaled, error)
        return score, score > self.threshold

    def _is_night(self, window: np.ndarray) -> bool:
        return float(window[:, self._irr_idx].max()) < self._sun_threshold

    def _scale(self, window: np.ndarray) -> np.ndarray:
        df = pd.DataFrame(window, columns=self._scaler.feature_names_in_)
        return self._scaler.transform(df)

    def _reconstruction_error(self, scaled: np.ndarray) -> np.ndarray:
        input_data = scaled[np.newaxis, ...]
        reconstruction = self._model.predict(input_data, verbose=0)
        return np.abs(reconstruction[0] - scaled)

    def _score(self, scaled: np.ndarray, error: np.ndarray) -> float:
        strategy = self._scoring_strategy
        if strategy == "A_mae_global":
            return float(np.mean(error))
        if strategy == "B_mae_power":
            return float(np.mean(error[:, self._power_idx]))
        if strategy == "C_p95_window":
            return float(np.percentile(np.mean(error, axis=1), 95))
        if strategy == "D_p95_power":
            return float(np.percentile(np.mean(error[:, self._power_idx], axis=1), 95))
        if strategy == "E_mlp_only":
            return abs(scaled[-1, self._mlp_target_idx] - self._mlp_predict(scaled))
        if strategy == "F_hybrid":
            d_score = float(np.percentile(np.mean(error[:, self._power_idx], axis=1), 95))
            e_score = abs(scaled[-1, self._mlp_target_idx] - self._mlp_predict(scaled))
            return d_score + e_score
        raise ValueError(f"scoring_strategy desconocida: {self._scoring_strategy!r}")

    def _mlp_predict(self, scaled: np.ndarray) -> float:
        input_data = scaled[np.newaxis, ...]
        bottleneck = self._encoder.predict(input_data, verbose=0)
        return float(self._mlp_head.predict(bottleneck, verbose=0)[0, 0])
