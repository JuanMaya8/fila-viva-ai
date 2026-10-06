# Fila Viva — AI Service

Servicio de predicción de **Fila Viva**. Este repositorio es **uno de tres**:

| Repositorio | Qué hace | Estado |
|---|---|---|
| `fila-viva-backend` | API core: turnos, funcionarios, tipos de trámite, tiempo real | 🟡 Avance semana 3 |
| `fila-viva-frontend` | PWA del ciudadano, pantalla de sala y panel de funcionarios | 🟡 Avance semana 3 |
| `fila-viva-ai` (este) | Servicio de predicción (IA + teoría de colas) | 🟡 Avance semana 3 |

> Este documento está escrito para una persona del equipo y para una IA generadora de código que continúe el proyecto.

---

## 1. Qué es Fila Viva

El diferencial del proyecto no es un turnero: es predecir dinámicamente cuánto va a esperar una persona, combinando teoría de colas y machine learning. Este repositorio es donde vive esa predicción. `fila-viva-backend` le manda el estado actual de una fila (personas delante, funcionarios activos) y este servicio responde con un tiempo estimado, una confianza y una comparación contra el método tradicional.

## 2. Estado del avance (semana 3 de 3)

**Hecho:**
- Proyecto FastAPI mínimo, con `/health` y `/predict`.
- Línea base de teoría de colas (`app/queueing.py`): calcula el tiempo estimado a partir de personas delante, funcionarios activos y un promedio histórico, con un factor de congestión.
- La misma línea base calcula la **estimación tradicional** (posición en la fila × promedio fijo, sin mirar funcionarios activos), que es el número contra el que se compara la IA.
- Un cálculo simple de confianza, que baja cuando hay más gente y menos funcionarios activos.
- Esquemas de request/response (`app/schemas.py`) que respetan **exactamente** el contrato definido en `fila-viva-backend/README.md`.

**Explícitamente NO hecho todavía (es la parte más importante que falta):**
- **No hay ningún modelo de machine learning todavía.** `estimate_wait_minutes()` es matemática de teoría de colas, no un modelo entrenado. Es un reemplazo funcional para que `fila-viva-backend` pueda integrarse hoy contra el contrato final, no la versión definitiva del cálculo.
- No hay ingesta de datos históricos (no hay conexión a la base de datos del backend ni a un data lake).
- No hay ingeniería de variables (hora del día, día de la semana, promedio móvil).
- No hay entrenamiento, ni registro de modelos (MLflow), ni orquestación de reentrenamiento (Airflow).
- No hay monitoreo de deriva del modelo.
- No hay tests todavía.

## 3. Dónde encaja en la arquitectura completa

Este servicio implementa hoy solo la **etapa 3** (modelado, con la línea base de teoría de colas) del pipeline de IA de 9 etapas descrito en `fila-viva-backend/README.md`. El resto del pipeline es el backlog:

```
1. Ingesta de datos            -> pendiente
2. Ingeniería de variables      -> pendiente
3. Modelado                     -> HECHO (solo línea base, sin ML todavía)
4. Entrenamiento y validación   -> pendiente
5. Despliegue del modelo        -> pendiente
6. Inferencia en tiempo real    -> HECHO (el endpoint /predict responde en tiempo real,
                                   aunque hoy no tenga un modelo entrenado detrás)
7. Suavizado en el navegador    -> vive en fila-viva-frontend
8. Comparación y margen de error -> HECHO (traditionalEstimateMinutes ya viaja en cada respuesta)
9. Retroalimentación            -> pendiente
```

## 4. Contrato con `fila-viva-backend`

`fila-viva-backend` llama a `POST /predict`. Este es el contrato que este servicio debe cumplir siempre, cambie o no la lógica interna:

**Request:**
```json
{
  "peopleAhead": 8,
  "activeAgents": 3,
  "serviceTypeId": "2b6f8c2e-1b3a-4a3a-9d90-7d6a0f9b6a11",
  "arrivalTime": "2026-09-29T14:32:00.000Z"
}
```

**Response:**
```json
{
  "estimatedWaitMinutes": 31,
  "confidence": 87,
  "traditionalEstimateMinutes": 86,
  "congestionLevel": "low"
}
```

Si este contrato cambia, hay que actualizarlo también en `fila-viva-backend` (`src/modules/prediction/interfaces/prediction-result.interface.ts`) y en `fila-viva-frontend` (`src/lib/api.ts`).

## 5. Stack de este repositorio

| Pieza | Tecnología | Por qué |
|---|---|---|
| Lenguaje | Python | El ecosistema de machine learning (scikit-learn, LightGBM, pandas) es de Python. |
| Framework | FastAPI | Validación automática con Pydantic, documentación interactiva gratis en `/docs`. |
| Modelo (pendiente) | LightGBM + regresión cuantil | Rápido de entrenar con pocas variables tabulares, da intervalos de confianza. |

## 6. Cómo correrlo localmente

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar variables de entorno
cp .env.example .env

# 4. Levantar el servicio
uvicorn app.main:app --reload --port 8000

# 5. Abrir la documentación interactiva
# http://localhost:8000/docs
```

## 7. Próximos pasos (backlog inmediato, en orden sugerido)

1. Definir de dónde van a salir los datos históricos (¿lectura directa a la base de `fila-viva-backend`? ¿un export periódico a S3?).
2. Ingeniería de variables: hora del día, día de la semana, promedio móvil de las últimas horas por `serviceTypeId`.
3. Entrenar un primer modelo LightGBM con datos simulados o con los primeros datos reales, y comparar su error contra la línea base actual.
4. Agregar `confidence` como un intervalo real (regresión cuantil), no la fórmula heurística actual.
5. Registrar el modelo (MLflow) y versionar sus resultados.
6. Tests: al menos validar que `/predict` nunca devuelve `confidence` fuera de 0–100 y que `estimatedWaitMinutes` nunca es negativo.

## 8. Notas para una IA generadora de código

- **Todo el código va en inglés**; este `README.md` va en español.
- Los nombres de campo en `app/schemas.py` usan camelCase a propósito (no snake_case, que sería lo normal en Python), para reflejar el contrato JSON tal cual. No los cambies a snake_case sin también actualizar el contrato en los otros dos repositorios.
- `app/queueing.py` tiene dos funciones que **no deben mezclarse**: `estimate_wait_minutes` (la que eventualmente reemplaza el modelo de IA) y `traditional_estimate_minutes` (que debe quedarse simple para siempre, porque es la comparación). Si vas a conectar el modelo entrenado, reemplazá el cuerpo de `estimate_wait_minutes` o de la llamada en `main.py`, pero no toques `traditional_estimate_minutes`.
- Los `TODO` en `app/main.py` describen, en orden, los próximos pasos reales del pipeline de IA. Seguilos antes de proponer un enfoque distinto.
- No dupliques lógica de negocio de turnos o funcionarios acá: este servicio solo predice; crear, listar o completar turnos es responsabilidad de `fila-viva-backend`.

## 9. Despliegue gratuito en Render

Este repositorio incluye `render.yaml` para crear el servicio web de FastAPI en Render:

1. Sube este repositorio a GitHub si todavía no está publicado.
2. En Render, crea un **Blueprint** y conecta el repositorio `fila-viva-ai`.
3. Render detectará `render.yaml`; confirma la creación del servicio `fila-viva-ai`.
4. Cuando el despliegue termine, verifica `https://<url-del-servicio>/health` y abre `/docs` para probar la API.
5. Copia la URL HTTPS del servicio. En el despliegue de `fila-viva-backend`, configúrala como `PREDICTION_SERVICE_URL` (sin `/predict` al final).

El plan gratuito puede suspender el servicio tras un periodo sin tráfico; la primera petición después de la suspensión puede tardar más. No se deben configurar secretos para este servicio en el estado actual del proyecto.
