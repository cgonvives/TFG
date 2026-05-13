# AsFin Strategic Optimizer — Documentación Técnica de Arquitectura

Este documento detalla la estructura, funcionalidad y flujo de datos del proyecto **AsFin Optimizer**, un sistema experto que combina **Machine Learning (XGBoost)** y **Optimización Lineal (PuLP)** para la generación de planes de acción estratégicos.

---

## 1. Visión General del Sistema

La finalidad del proyecto es resolver un problema de decisión complejo: *Dada una lista de necesidades financieras/empresariales, ¿cuál es el conjunto óptimo de acciones (planes) que maximiza el beneficio estratégico bajo restricciones de recursos?*

El sistema utiliza una arquitectura de tres capas:
1.  **Capa de Presentación (Frontend):** Interfaz web interactiva.
2.  **Capa de Aplicación (Backend):** Servidor API FastAPI y orquestación.
3.  **Capa de Inteligencia (Core):** Modelos de ML y Motor de Optimización.

---

## 2. Detalle de Módulos (Directorio `src/`)

### 2.1. Núcleo de Optimización e Inteligencia
*   **`optimizer.py` (El "Cerebro"):** Es el módulo más crítico.
    *   **Función:** Construye el modelo matemático de programación lineal entera.
    *   **Conexión:** Recibe datos de `data.py`, puntuaciones de IA de `get_ml_scores` y parámetros de `config.py`.
    *   **Detalle:** Utiliza la librería **PuLP** para interactuar con el solver **CBC**. Calcula pesos heurísticos (Urgencia/Importancia) y los combina con un "boost" de Machine Learning para recomendar las mejores acciones.
*   **`ml_model_trainer.py`:** Entrena un modelo **XGBoost**.
    *   **Función:** Analiza datos históricos para predecir la "Aceptación del Asesor". Utiliza técnicas de NLP (TF-IDF) para entender la relación semántica entre la descripción de una empresa y un plan de acción.
*   **`ml_weight_learner.py`:** Un optimizador de segundo nivel.
    *   **Función:** No entrena el modelo de IA, sino que "aprende" cuáles son los mejores valores para los pesos heurísticos ($\alpha, \beta, \gamma, \delta$) analizando qué combinaciones producen resultados más cercanos a la realidad histórica.

### 2.2. Gestión de Datos y NLP
*   **`data.py`:** Encargado de la persistencia.
    *   **Función:** Lee los archivos Excel originales y los transforma en estructuras JSON optimizadas para el acceso rápido.
*   **`llm_classifier.py` & `llm_router.py`:** Integración con Inteligencia Artificial Generativa (OpenAI/Gemini).
    *   **Función:** Clasifica automáticamente el sector de actividad de una empresa basándose en su "Objeto Social". Esto permite que el modelo de Machine Learning sea consciente del sector sin intervención manual.
*   **`utils.py`:** Herramientas de soporte para limpieza de texto, normalización (quitar acentos) y gestión de caché de sectores para ahorrar costes de API.

### 2.3. Capa de Aplicación y Servidor
*   **`main.py`:** El punto de entrada de la API.
    *   **Función:** Define los endpoints (rutas) que el frontend consume: `/solve` para optimizar, `/needs` para listar datos, y rutas de administración para subir archivos o re-entrenar la IA.
*   **`pipeline_runner.py`:** Un orquestador de procesos largos.
    *   **Función:** Ejecuta en segundo plano la secuencia completa: Procesar Datos → Entrenar ML → Aprender Pesos, permitiendo que la interfaz siga siendo funcional mientras se procesan miles de datos.
*   **`config.py`:** Configuración global y gestión de rutas.
    *   **Detalle:** Incluye lógica especial para que el proyecto funcione tanto en modo desarrollo como empaquetado en un archivo `.exe`, gestionando las rutas temporales de Windows (`_MEIPASS`).

---

## 3. Flujo de Datos y Conexiones

1.  **Inicio:** El usuario abre `AsFin_Optimizer.exe`. El `launcher.py` inicializa el servidor y abre el navegador.
2.  **Carga:** El frontend solicita a `main.py` las necesidades disponibles. `main.py` llama a `data.py` para leer los JSON procesados.
3.  **Interacción:** El usuario selecciona necesidades y describe su empresa.
4.  **Optimización:**
    *   El frontend envía un POST a `/solve`.
    *   `main.py` invoca a `optimizer.py`.
    *   `optimizer.py` pide a `llm_classifier.py` que identifique el sector.
    *   `optimizer.py` genera vectores NLP y pide al modelo XGBoost (`ml_model_trainer.py`) una puntuación de afinidad.
    *   Se construye la función objetivo y el solver **CBC** encuentra la combinación matemática óptima.
    *   Se aplica la **lógica de ordenación estratégica** (Urgencia > Importancia > Complejidad).
5.  **Resultado:** El frontend recibe el JSON con las acciones recomendadas y las visualiza en pantalla.

---

## 4. El Proceso de Construcción (`asfin.spec` & `build.bat`)

Para convertir este ecosistema de Python en una aplicación de un solo archivo:
*   **`asfin.spec`:** Indica a PyInstaller qué librerías "pesadas" (XGBoost, Sklearn, Pandas) y qué binarios externos (el solver CBC de PuLP) debe meter dentro del paquete.
*   **`build.bat`:** Automatiza la limpieza de archivos temporales, la instalación de dependencias y la ejecución de la compilación, asegurando que el entorno sea reproducible.

---

## 5. Finalidad del Proyecto

Este software no es solo una herramienta de cálculo; es un **puente entre la IA predictiva y la optimización prescriptiva**. Su finalidad es eliminar el sesgo humano y la fatiga en la planificación estratégica, asegurando que las decisiones financieras se basen en datos objetivos, modelos de aprendizaje automático y rigor matemático.
