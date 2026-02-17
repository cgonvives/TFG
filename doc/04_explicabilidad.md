# Fase 4: Interpretabilidad y Explicabilidad (SHAP)

## 1. El Problema de la "Caja Negra"
Un modelo de Machine Learning, por muy preciso que sea, suele ser una "caja negra" para el usuario final. En un TFG de ingeniería, es vital no solo dar resultados, sino explicar el **porqué**.

## 2. Solución: SHAP (SHapley Additive exPlanations)
He implementado un motor de explicabilidad basado en la **Teoría de Juegos** ([src/ml_explainer.py](file:///../src/ml_explainer.py)). SHAP descompone cada predicción del modelo y asigna a cada característica (Urgencia, Sector, Palabras clave) un valor que indica cuánto ha contribuido a la decisión final.

### Visualización Global:
He generado un gráfico de importancia de características ([doc/images/shap_global_importance.png](file:///../doc/images/shap_global_importance.png)) que muestra qué factores dominan el modelo:
- **Sector y Objeto Social:** El motor ha aprendido que ciertas palabras clave del objeto social de la empresa son determinantes.
- **Contexto de la Tarjeta:** Las palabras extraídas del "Texto Explicativo" de las necesidades influyen significativamente en si un plan es "Aceptable" o no.

## 3. Explicabilidad Local (Transparencia)
El sistema ahora puede generar una justificación para cada plan recomendado. Ejemplo real capturado por el motor:
- **Plan Recomendado:** "Movilizar cartera de clientes".
- **Justificación:** 
    - *Aumenta la probabilidad:* Sector: "Servicios".
    - *Aumenta la probabilidad:* Palabra clave en tarjeta: "liquidez".
    - *Aumenta la probabilidad:* Urgencia (4).

## 4. Logros de esta Fase
- **Aceptación Asistida:** El asesor puede confiar más en el sistema al recibir una breve explicación del motivo de la sugerencia.
- **Calidad Académica:** La inclusión de modelos de explicabilidad eleva el nivel técnico de la memoria del TFG.

## 5. Próxima Fase: Conclusiones y Viabilidad
Con el motor siendo preciso (Fase 2), calibrado (Fase 3) y transparente (Fase 4), solo queda recopilar las conclusiones finales y preparar el cierre del proyecto.
