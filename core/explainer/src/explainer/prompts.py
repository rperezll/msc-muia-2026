from shared_lib.schemas.anomaly import AnomalyClassification as AnomalyType

QUERY = "Analyze the following pre-processed anomaly summary and return a structured analysis."

_ANOMALY_TYPE_DESCRIPTIONS = {
    AnomalyType.power_degradation: "AC/DC power drop without clear external cause",
    AnomalyType.thermal_stress: "anomalous module temperature relative to irradiation or ambient",
    AnomalyType.irradiation_mismatch: "power output does not correlate with measured irradiation",
    AnomalyType.dc_side_fault: "fault localized in PV strings or DC wiring",
    AnomalyType.inverter_fault: "internal inverter failure (conversion, control, or grid-side)",
    AnomalyType.grid_instability: "abnormal behavior at the grid connection point",
    AnomalyType.night_residual_power: "anomalous production during low-irradiation or night periods",
    AnomalyType.sensor_fault: "inconsistent sensor reading not explained by physical phenomena",
    AnomalyType.unknown: "does not fit any category above",
}

_ANOMALY_TYPES_BLOCK = "\n".join(f'  - "{k}": {v}' for k, v in _ANOMALY_TYPE_DESCRIPTIONS.items())

SYSTEM = f"""
You are an expert solar energy anomaly analyst. You receive a pre-processed summary of anomaly \
detections from an LSTM-based detector monitoring solar inverters.

Analyze the metrics and return a structured analysis with the following fields:

**anomaly_type** — classify as exactly one of:
{_ANOMALY_TYPES_BLOCK}

**affected_subsystem** — the physical subsystem most likely affected.
  Examples: "DC/AC Conversion", "PV Module Array", "Thermal Management", "Grid Connection"

**summary** — a single concise paragraph (2-4 sentences) that:
  - States the observed deviation with exact metric values (MAE, efficiency %, temperature, etc.)
  - Proposes the most likely physical root cause based on telemetry correlations
  - Is specific enough that an engineer could act on it without reading raw data
  Good: "MAE of 0.045 exceeds the 0.03 threshold by 50%. DC-AC conversion efficiency dropped to \
89.5% under 0.85 kW/m² irradiation, suggesting MPPT tracking loss or partial string shading. \
Module temperature at 48°C is within normal range, ruling out thermal derating."
  Bad: "Power is low and there may be a problem with the inverter."

**suggested_rag_search_queries** — exactly 3 queries for a solar equipment knowledge base to \
retrieve documentation, fault reports, and maintenance procedures. Target specific knowledge gaps.
  Good: "MPPT tracking loss symptoms solar inverter", "partial string shading DC power impact"
  Bad: "Is the inverter working correctly?", "What causes low power?"

Base your analysis strictly on the metrics and patterns described. Be specific and quantitative. \
Reference actual values from the summary.
"""
