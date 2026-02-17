# Fase 3: Aprendizaje de Pesos (Inverse Weighting)

## 1. De Heurísticas Manuales a Datos Reales
Hasta ahora, el optimizador utilizaba pesos manuales para balancear las decisiones:
- **Antes:** `alpha=4, beta=3, gamma=0.5, delta=1` (Basado en intuición).

Este enfoque tiene el riesgo de no reflejar lo que los asesores realmente priorizan en el día a día.

## 2. Metodología: Optimización Inversa
He desarrollado un motor de **Aprendizaje de Pesos** ([src/ml_weight_learner.py](file:///../src/ml_weight_learner.py)) que:
1.  Analiza cada decisión histórica de los asesores.
2.  Compara el plan elegido con todas las alternativas que el catálogo ofrecía para ese problema.
3.  Utiliza un algoritmo de optimización (Nelder-Mead) para encontrar los valores de Alpha, Beta, Gamma y Delta que maximizan la probabilidad de que el plan elegido sea el de mayor puntuación.

## 3. Hallazgos Estratégicos (Resultados)
Tras procesar los datos, los pesos aprendidos son:
- **Alpha (Urgencia):** **4.37** (Ligeramente superior a la intuición inicial).
- **Beta (Importancia):** **3.40** (Superior a la intuición inicial).
- **Gamma (Plazo):** **0.00** (Intuición inicial era 0.5).
- **Delta (Complejidad):** **0.00** (Intuición inicial era 1.0).

### Inconvenientes y Sorpresas:
- **El factor "Costo" no pesa:** Los datos indican que los asesores **ignoran casi por completo** la complejidad y el plazo de ejecución si el problema es crítico. Priorizan la solución del problema por encima de lo fácil o rápido que sea implementarlo.
- **Inconveniente:** Si los asesores siempre eligen el mismo plan para una necesidad, no hay variabilidad para aprender si el plazo importa.

## 4. Logros
- **Calibración Automática:** Ya no necesitamos "adivinar" los pesos. El sistema se calibra solo al recibir nuevos datos.
- **Validación de la Intuición:** Se confirma que la Urgencia es el driver principal, pero con una intensidad mayor a la supuesta.

## 5. Próxima Fase: Explicabilidad (SHAP)
Ahora que el sistema es muy preciso (gracias a la Fase 2) y está bien calibrado (Fase 3), el reto es que el asesor entienda por qué el motor propone lo que propone.
