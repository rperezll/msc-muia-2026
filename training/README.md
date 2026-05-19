# msc-muia-2026 - Training

Entrenamiento del LSTM Autoencoder para detección de anomalías en producción solar. Ejecutable en **Google Colab** (recomendado con GPU) o local con `uv`.

## Comandos

```bash
# instalar dependencias
uv sync

# lint notebook
uv run ruff check lstm_autoencoder_solar_anomaly_detection.ipynb

# formatear notebook
uv run ruff format lstm_autoencoder_solar_anomaly_detection.ipynb
```

## Dataset

[Solar Power Generation Data](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data/data) (Kaggle, descargado el 21/03/2026). Cuatro CSV (generación + clima × 2 plantas).

| Variable              | Descripción                                                       |
| --------------------- | ----------------------------------------------------------------- |
| `DATE_TIME`           | Timestamp a intervalos de 15 min                                  |
| `PLANT_ID`            | Planta 1 o 2 (el detector lo usa para enrutar al modelo) correcto |
| `SOURCE_KEY`          | Inversor (generación) o sensor meteorológico (clima)              |
| `DC_POWER`            | Potencia DC generada por los paneles                              |
| `AC_POWER`            | Potencia AC tras conversión en el inversor                        |
| `DAILY_YIELD`         | Energía acumulada desde inicio del día                            |
| `TOTAL_YIELD`         | Energía acumulada total del inversor                              |
| `AMBIENT_TEMPERATURE` | Temperatura del aire                                              |
| `MODULE_TEMPERATURE`  | Temperatura de la superficie del panel                            |
| `IRRADIATION`         | Porcentaje de irradiancia solar                                   |

## Contrato de exportación

El notebook entrena 3 seeds × 2 plantas y elige el ganador por PR-AUC. El detector espera siempre **4 archivos para las 2 plantas** en rutas fijas:

- `models/keras/plant_1/`
- `models/keras/plant_2/`

| Archivo                  | Contenido                                                        |
| ------------------------ | ---------------------------------------------------------------- |
| `model_lstm_solar.keras` | Pesos y arquitectura del LSTM Autoencoder                        |
| `model_mlp_head.keras`   | Cabezal MLP (64→32→1) que predice `AC_POWER` desde el bottleneck |
| `scaler_solar.pkl`       | `MinMaxScaler` ajustado sobre el set de entrenamiento (sano)     |
| `config_solar.json`      | Configuración (ver abajo)                                        |

### Esquema de `config_solar.json`

| Campo                  | Tipo        | Descripción                                                                                                           |
| ---------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------- |
| `threshold`            | `float`     | Umbral F1-óptimo sobre validación                                                                                     |
| `sun_threshold`        | `float`     | Irradiación mínima para considerar que hay sol                                                                        |
| `time_steps`           | `int`       | Longitud de ventana temporal (32 = 8 h)                                                                               |
| `features`             | `list[str]` | Features ordenadas (el orden define el eje 1 del tensor)                                                              |
| `scoring_strategy`     | `str`       | Estrategia ganadora: `A_mae_global` \| `B_mae_power` \| `C_p95_window` \| `D_p95_power` \| `E_mlp_only` \| `F_hybrid` |
| `scoring_power_idx`    | `list[int]` | Índices de `DC_POWER` y `AC_POWER` en `features`                                                                      |
| `mlp_head_target_idx`  | `int`       | Índice de `AC_POWER` en `features`                                                                                    |
| `bottleneck_layer_idx` | `int`       | Índice de la capa LSTM(8) en el AE (fijo: `3`)                                                                        |
| `training_scope`       | `str`       | `plant_1` o `plant_2`                                                                                                 |
| `training_seed`        | `int`       | Seed del utilizado para el entrenamiento del ganador                                                                  |
| `dataset_sha256`       | `object`    | Hashes SHA-256 de los 4 CSV de Kaggle (trazabilidad)                                                                  |
| `metrics`              | `object`    | `roc_auc`, `pr_auc`, `precision`, `recall`, `f1`, `tp/fp/tn/fn`, `abs_errors`                                         |
