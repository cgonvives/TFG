# Diagrama de Flujo del Proyecto — Optimizador Estratégico para PYMEs

## 1. Visión General del Sistema

Este diagrama muestra las **tres grandes fases** del sistema y cómo se conectan entre sí:

```mermaid
flowchart TB
    subgraph OFFLINE_DATA["📊 FASE 1 — Pipeline de Datos (Offline)"]
        direction TB
        A1["📁 Excel: Planes de Acción TFG v2.xlsx"]
        A2["data.py — Carga y limpieza de datos"]
        A3["3 archivos JSON procesados"]
        A4["ml_data_explorer.py — Construcción del dataset ML"]
        A5["ml_dataset_final.csv"]
        
        A1 --> A2
        A2 --> A3
        A1 --> A4
        A4 --> A5
    end

    subgraph OFFLINE_ML["🤖 FASE 2 — Entrenamiento ML (Offline)"]
        direction TB
        B1["ml_model_trainer.py — Entrenamiento XGBoost"]
        B2["ml_weight_learner.py — Optimización inversa de pesos"]
        B3["Artefactos: correction_model.pkl, vectorizers, encoders"]
        B4["Artefactos: learned_heuristics.pkl"]
        
        B1 --> B3
        B2 --> B4
    end

    subgraph REALTIME["🌐 FASE 3 — Flujo en Tiempo Real (Web)"]
        direction TB
        C1["🖥️ Interfaz Web — Portal AsFin"]
        C2["⚡ FastAPI Backend — main.py"]
        C3["🧠 Optimizador — optimizer.py"]
        C4["📋 Resultados: Acciones Recomendadas"]
        
        C1 -->|"HTTP POST /solve"| C2
        C2 --> C3
        C3 --> C4
        C4 -->|"JSON Response"| C1
    end

    A3 -->|"Carga al iniciar servidor"| C2
    A5 --> B1
    A5 --> B2
    B3 -->|"Modelos cargados en inferencia"| C3
    B4 -->|"Pesos aprendidos"| C3

    style OFFLINE_DATA fill:#1a1a2e,stroke:#16a085,stroke-width:2px,color:#e0e0e0
    style OFFLINE_ML fill:#1a1a2e,stroke:#e67e22,stroke-width:2px,color:#e0e0e0
    style REALTIME fill:#1a1a2e,stroke:#3498db,stroke-width:2px,color:#e0e0e0
```

---

## 2. Pipeline de Datos y Entrenamiento ML (Detallado)

Este diagrama profundiza en **cómo se procesan los datos** desde el Excel hasta los modelos entrenados:

```mermaid
flowchart TD
    subgraph EXCEL["📁 Fuente de Datos"]
        E1["Hoja: Necesidades<br/>(Urgencia, Importancia, Nombre Tarjeta, Texto Explicativo)"]
        E2["Hoja: Catálogo Planes<br/>(Descripción, Plazo, Complejidad, Código Problema)"]
        E3["Hoja: Histórico<br/>(cod_company, cod_weakness, cod_plan)"]
        E4["Hoja: Objeto Social<br/>(cod_company, objeto_social)"]
    end

    subgraph DATA_PY["⚙️ data.py — Procesamiento Base"]
        D1["load_data(): Lee hojas Excel"]
        D2["Mapeo categórico a numérico:<br/>Urgencia → 1,2,3<br/>Importancia → 1,2,3<br/>Complejidad → 1,2,3"]
        D3["extract_needs(): Dict de necesidades"]
        D4["extract_plans_and_relations(): Dict de planes + Relaciones N↔P"]
        D5["save_json(): 3 JSON<br/>• processed_necesidades.json<br/>• processed_planes.json<br/>• processed_relacion_necesidad_plan.json"]
    end

    subgraph ML_EXPLORER["🔬 ml_data_explorer.py — Dataset ML"]
        M1["Cargar Histórico + Objeto Social"]
        M2["utils.clean_text(): Limpieza NLP"]
        M3["llm_classifier.py: Clasificación de sector<br/>(GPT-4o-mini vía OpenAI API)"]
        M4["Merge: Empresa + Necesidad + Plan"]
        M5["Muestras positivas: accepted=1<br/>(planes elegidos por asesores)"]
        M6["Muestras negativas: accepted=0<br/>(planes disponibles NO elegidos)"]
        M7["ml_dataset_final.csv<br/>(~5700 filas con features)"]
    end

    subgraph TRAINER["🎯 ml_model_trainer.py — Entrenamiento"]
        T1["TF-IDF: objeto_social → vec_social<br/>(300 features)"]
        T2["TF-IDF: contexto_necesidad → vec_need<br/>(300 features)"]
        T3["TF-IDF: sector → vec_sector<br/>(50 features)"]
        T4["OneHot: cod_plan → enc_plan"]
        T5["Features numéricas:<br/>Urgencia, Importancia, Complejidad, Plazo"]
        T6["XGBClassifier<br/>(n_estimators=100, max_depth=6)"]
        T7["Evaluación: ROC-AUC Score"]
        T8["Guardado: correction_model.pkl<br/>+ 5 artefactos auxiliares"]
    end

    subgraph WEIGHT_LEARNER["⚖️ ml_weight_learner.py — Pesos Óptimos"]
        W1["Optimización Inversa (Nelder-Mead)"]
        W2["Función objetivo: Hinge Loss contrastiva<br/>Score_elegido > Score_rechazado"]
        W3["Resultado: α, β, γ, δ óptimos"]
        W4["Guardado: learned_heuristics.pkl"]
    end

    E1 & E2 --> D1
    D1 --> D2
    D2 --> D3 & D4
    D3 & D4 --> D5

    E1 & E2 & E3 & E4 --> M1
    M1 --> M2
    M2 --> M3
    M3 --> M4
    M4 --> M5 & M6
    M5 & M6 --> M7

    M7 --> T1 & T2 & T3 & T4 & T5
    T1 & T2 & T3 & T4 & T5 --> T6
    T6 --> T7
    T7 --> T8

    M7 --> W1
    W1 --> W2
    W2 --> W3
    W3 --> W4

    style EXCEL fill:#2c3e50,stroke:#1abc9c,stroke-width:2px,color:#ecf0f1
    style DATA_PY fill:#2c3e50,stroke:#16a085,stroke-width:2px,color:#ecf0f1
    style ML_EXPLORER fill:#2c3e50,stroke:#e67e22,stroke-width:2px,color:#ecf0f1
    style TRAINER fill:#2c3e50,stroke:#e74c3c,stroke-width:2px,color:#ecf0f1
    style WEIGHT_LEARNER fill:#2c3e50,stroke:#9b59b6,stroke-width:2px,color:#ecf0f1
```

---

## 3. Flujo en Tiempo Real — Interfaz Web + Backend (Detallado)

Este diagrama muestra **paso a paso** lo que ocurre cuando un usuario interactúa con la web:

```mermaid
flowchart TD
    subgraph WEB["🖥️ Interfaz Web"]
        U1["👤 Usuario accede al Portal<br/>(index.html)"]
        U2["Click: Optimizador Estratégico<br/>(optimizer.html)"]
        U3["Se cargan las necesidades<br/>(GET /needs → renderNeeds)"]
        U4["Usuario selecciona:<br/>✅ Necesidades de la empresa<br/>🏭 Sector / Actividad<br/>🔢 Nº máximo de acciones"]
        U5["Click: Generar Plan Óptimo<br/>(POST /solve)"]
        U6["Se muestran resultados:<br/>📋 Acciones Recomendadas<br/>🔗 Cobertura Necesidad ↔ Acción<br/>📊 Valor Objetivo"]
    end

    subgraph API["⚡ FastAPI — main.py"]
        A1["startup_event():<br/>load_processed_data() → DATA_CACHE"]
        A2["GET /needs<br/>→ Devuelve dict de necesidades"]
        A3["POST /solve<br/>→ Valida SolveRequest (Pydantic)"]
    end

    subgraph OPT["🧠 optimizer.py — Motor de Optimización"]
        O1["Cargar pesos aprendidos<br/>(learned_heuristics.pkl)"]
        O2["Filtrar necesidades y relaciones<br/>(N_set, R_set, A_set)"]
        O3["get_ml_scores(): Predicción ML"]
        O4["Construir modelo PuLP:<br/>• Variables binarias x_ij, y_j<br/>• Función objetivo: Σ(w_ij + ml_boost) · x_ij"]
        O5["Restricciones:<br/>• Cobertura: cada necesidad ≥ 1 acción<br/>• Coherencia: x_ij ≤ y_j<br/>• Máximo de acciones: Σy_j ≤ max"]
        O6["Resolver con PuLP CBC"]
        O7["Extraer y ordenar resultados<br/>(por contribución total)"]
    end

    subgraph ML["🤖 Módulo ML — Inferencia"]
        ML1["Cargar modelos:<br/>XGBoost, TF-IDF vectorizers,<br/>OneHotEncoder, feature_names"]
        ML2["Procesar texto empresa:<br/>clean_text() + remove_accents()"]
        ML3["Detectar sector:<br/>sector_cache.json → O LLM<br/>(GPT-4o-mini si no está en caché)"]
        ML4["Vectorizar features TF-IDF:<br/>social, need, sector"]
        ML5["Construir DataFrame de features<br/>(mismo esquema que entrenamiento)"]
        ML6["model.predict_proba()<br/>→ P(accepted=1) por cada par (i,j)"]
    end

    subgraph HEUR["📐 Cálculo Heurístico"]
        H1["w_ij = α·Urgencia_i + β·Importancia_i<br/>− γ·Plazo_j − δ·Complejidad_j"]
        H2["ml_boost = ml_weight · P(accepted)"]
        H3["Score final = w_ij + ml_boost + tie_breaker"]
    end

    U1 --> U2
    U2 --> U3
    U3 -->|"fetch('/needs')"| A2
    A2 -->|"JSON: {id: {necesidad, urgencia, ...}}"| U3
    U3 --> U4
    U4 --> U5
    U5 -->|"POST /solve<br/>{selected_needs, max_actions, objeto_social}"| A3

    A1 -.->|"Al iniciar servidor"| A2 & A3

    A3 --> O1
    O1 --> O2
    O2 --> O3

    O3 --> ML1
    ML1 --> ML2
    ML2 --> ML3
    ML3 --> ML4
    ML4 --> ML5
    ML5 --> ML6

    ML6 -->|"Dict: {(need_i, plan_j): score}"| O4

    O4 --> H1
    H1 --> H2
    H2 --> H3
    H3 --> O4

    O4 --> O5
    O5 --> O6
    O6 --> O7
    O7 -->|"JSON: {objective_value, actions, assignments}"| A3
    A3 -->|"HTTP 200"| U6

    style WEB fill:#1a1a2e,stroke:#3498db,stroke-width:2px,color:#ecf0f1
    style API fill:#1a1a2e,stroke:#2ecc71,stroke-width:2px,color:#ecf0f1
    style OPT fill:#1a1a2e,stroke:#e74c3c,stroke-width:2px,color:#ecf0f1
    style ML fill:#1a1a2e,stroke:#e67e22,stroke-width:2px,color:#ecf0f1
    style HEUR fill:#1a1a2e,stroke:#9b59b6,stroke-width:2px,color:#ecf0f1
```

---

## 4. Resumen de Archivos por Fase

| Fase | Archivo | Función Principal |
|------|---------|-------------------|
| **Datos** | `data.py` | Carga Excel, limpia y genera 3 JSON procesados |
| **Datos** | `ml_data_explorer.py` | Construye el dataset ML con muestras positivas/negativas |
| **Datos** | `llm_classifier.py` | Clasifica sectores vía GPT-4o-mini (OpenAI API) |
| **Datos** | `utils.py` | Funciones NLP: `clean_text()`, `remove_accents()`, caché de sectores |
| **ML** | `ml_model_trainer.py` | Entrena XGBoost + guarda vectorizers y encoders |
| **ML** | `ml_weight_learner.py` | Optimización inversa para aprender α, β, γ, δ óptimos |
| **ML** | `ml_explainer.py` | Genera explicaciones SHAP de las predicciones |
| **ML** | `compare_ml_vs_heuristic.py` | Compara IA vs heurístico puro por sector |
| **ML** | `ml_verification.py` | Verifica que el ML cambia recomendaciones por sector |
| **Web** | `main.py` | Servidor FastAPI con endpoints `/needs` y `/solve` |
| **Web** | `optimizer.py` | Motor de optimización PuLP + inferencia ML en tiempo real |
| **Web** | `config.py` | Rutas, pesos por defecto y parámetros ML |
| **Frontend** | `index.html` | Portal corporativo AsFin |
| **Frontend** | `optimizer.html` | Interfaz del optimizador estratégico |
| **Frontend** | `optimizer.js` | Lógica JS: carga necesidades, envía solicitudes, muestra resultados |
| **Frontend** | `style.css` + `theme.js` | Diseño visual y toggle modo claro/oscuro |

---

## 5. Flujo Simplificado de un Usuario (End-to-End)

```mermaid
flowchart LR
    A["👤 Usuario"] --> B["🌐 Portal Web<br/>(index.html)"]
    B --> C["⚙️ Optimizador<br/>(optimizer.html)"]
    C --> D["✅ Selecciona necesidades<br/>+ sector + nº acciones"]
    D --> E["📡 POST /solve"]
    E --> F["🧠 Optimizador PuLP<br/>+ XGBoost + LLM"]
    F --> G["📋 Plan óptimo<br/>(acciones + asignaciones)"]
    G --> H["🖥️ Resultados en pantalla"]

    style A fill:#3498db,stroke:#2980b9,color:#fff
    style F fill:#e74c3c,stroke:#c0392b,color:#fff
    style H fill:#2ecc71,stroke:#27ae60,color:#fff
```
