# Despliegue en Railway

## Archivos necesarios
- servidor.py
- requirements_servidor.txt
- Procfile (ver abajo)

## Procfile
```
web: gunicorn servidor:app
```

## Pasos
1. Crear cuenta en railway.app
2. "New Project" → "Deploy from GitHub"
3. Subir estos 3 archivos a un repositorio GitHub nuevo
4. Railway detecta automáticamente el Procfile y despliega
5. Te da una URL pública tipo: https://tuapp.railway.app

## Conectar Tally
1. En Tally → tu formulario → "Integrations" → "Webhooks"
2. URL: https://tuapp.railway.app/webhook
3. Método: POST
4. Cada respuesta nueva llega automáticamente al servidor

## Endpoints disponibles
- POST /webhook  → recibe respuesta nueva de Tally
- GET  /estado   → estado actual del corpus y prompt generado
- POST /cargar_corpus → carga corpus inicial (solo una vez)
