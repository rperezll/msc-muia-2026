# [MQTT] Telemetría solar emitida por el simulador en tiempo real
MQTT_TOPIC_TELEMETRY = "telemetry/solar"
# [MQTT] Comandos de control para el simulador (play, pause)
MQTT_TOPIC_SIMULATOR_CONTROL = "simulator/control"
# [MQTT] Estado actual del simulador (playing, paused, stopped)
MQTT_TOPIC_SIMULATOR_STATUS = "simulator/status"
# [MQTT] Briefing de anomalía detectada
MQTT_TOPIC_DETECTOR_ANOMALY = "detector/anomaly"
# [MQTT] Eventos terminales del ciclo de vida de jobs del explainer (completed / failed)
MQTT_TOPIC_JOB_EVENT = "explainer/job_event"

# [RabbitMQ] Cola de trabajo con reportes de anomalías
RABBITMQ_QUEUE_ANOMALIES = "anomalies"
# [RabbitMQ] Cola de eventos de ciclo de vida de jobs del explainer
RABBITMQ_QUEUE_JOB_EVENTS = "job_events"
