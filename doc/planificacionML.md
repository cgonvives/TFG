# Plan de Desarrollo: Motor de Machine Learning para Corrección del Optimizador

Este plan detalla la arquitectura, metodología y estrategia de datos para implementar un modelo de ML que aprenda de las decisiones de los asesores financieros y mejore las recomendaciones del optimizador actual.

## Objetivo

El objetivo es pasar de un optimizador con pesos fijos (`alpha, beta, gamma, delta`) a un sistema dinámico que considere el perfil de la empresa (Sector, Objeto Social) y las preferencias históricas de los expertos.

## Arquitectura Propuesta: "Optimizer Tuning & Re-ranking"

Sugerimos un enfoque en dos etapas:

1. **Etapa 1: Optimización de Pesos (Inverse Optimization)**

   * **Concepto**: Ajustar los parámetros del optimizador para que sus salidas coincidan al máximo con las recomendaciones históricas.
   * **Entrada**: Necesidades del cliente, Acciones históricas elegidas.
   * **Salida**: Un set de pesos $(\alpha, \beta, \gamma, \delta)$ óptimos para cada segmento de empresa.
2. **Etapa 2: Scoring de Contexto (ML Re-ranker)**

   * **Concepto**: Un modelo supervisado (ej. Random Forest o XGBoost) que predice la probabilidad de que un asesor acepte un par (Necesidad, Plan) basándose en el Objeto Social.
   * **Variables (Features)**:
     * **Empresa**: Embeddings del Objeto Social (usando NLP), Sector.
     * **Necesidad**: Urgencia, Importancia, Categoría.
     * **Acción**: Complejidad, Plazo, Relevancia histórica.
   * **Meta**: El score del ML se suma al valor objetivo del optimizador PuLP.

## ¿Hacen falta más datos?

**SÍ.** Actualmente tenemos el "qué eligieron", pero para un ML robusto necesitamos:

1. **Ejemplos Negativos**: Acciones que el optimizador propuso pero el asesor descartó.
2. **Contexto Sectorial**: Clasificación de las empresas por sector (CNAE).
3. **Feedback Directo**: El motivo por el cual se cambió una recomendación (ej. "Demasiado caro", "No aplica por sector").

## Cómo conseguir más datos

1. **Extracción de Logs de Ajustes**: Si existe una plataforma donde los asesores editan los planes, debemos registrar cada cambio (Borrar, Añadir, Reemplazar).
2. **Enriquecimiento con Objeto Social**: Utilizar modelos de lenguaje (LLM) para clasificar automáticamente las empresas en sectores a partir de la columna `objeto_social`.
3. **Generación de Datos Sintéticos**: Crear variaciones de los casos históricos (Pertubación) para aumentar el tamaño del dataset de entrenamiento.

## Plan de Implementación

### 1. Preprocesamiento y ETL

* [ ] Unificar `needs_data` + `plans_data` + `historical_data` en un DataFrame plano.
* [ ] Procesar `objeto_social`: Convertir texto a vectores (Embeddings/TF-IDF) para que el ML lo entienda.
* [ ] Generar etiquetas (Labels): `1` si el plan fue elegido por el asesor, `0` si estaba disponible pero no fue elegido.

### 2. Desarrollo del Modelo

* [ ] Entrenar un modelo de clasificación binaria para predecir la "Aceptación del Asesor".
* [ ] Evaluar precisión y recall (queremos que el modelo no se pierda las acciones preferidas por los expertos).

### 3. Integración con el Optimizador (`optimizer.py`)

* [ ] Modificar la función `solve_optimization` para recibir los scores del ML.
* [ ] **Nueva Función Objetivo**:
  $Max \sum (w_{current} + \lambda \cdot score_{ML}) \cdot x_{ij}$
  *(Donde $\lambda$ es un hiperparámetro que determina cuánta influencia tiene el ML sobre las reglas fijas).*

## Plan de Verificación

### Pruebas Automatizadas

* **Backtesting**: Ejecutar el nuevo motor filtrando por acciones históricas y medir el % de coincidencia (Hit Rate) contra el optimizador antiguo.
* **Aislamiento**: Verificar que si no hay datos de ML para una empresa, el sistema degrade con elegancia al optimizador de reglas fijas.

### Verificación Manual

* Presentar al equipo de asesores 5 casos reales y comparar:
  1. Lo que sugirió el optimizador original.
  2. Lo que sugirió el nuevo motor con ML.
  3. Cuál prefieren ellos.
