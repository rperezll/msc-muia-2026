# msc-muia-2026 - Models

```text
models/
├── 📂 keras/
    └── LSTM Resultado del entrenamiento de /training
├── 📂 ollama/
    └── Presets de configuración para ejecutar modelos con Ollama
```

## Instanciar modelos de Ollama

```bash
cd ollama

# qwen2.5-coder:7b-instruct-q4_K_M
ollama create qwen-nuc -f qwen3.mf

# gemma3:4b-it-qat
ollama create gemma-nuc -f gemma.mf
```
