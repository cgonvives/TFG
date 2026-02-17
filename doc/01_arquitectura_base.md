# Fase 1: Arquitectura Base (Versión Simplificada)

## 1. Situación de Partida
El proyecto TFG se centra en mejorar un optimizador de planes de acción estratégico para PYMES. El optimizador usa lógica PuLP con parámetros establecidos manualmente. El objetivo del motor ML es reducir la brecha entre la recomendación técnica y la decisión final del asesor humano.

## 2. Definición del Alcance (Necesidades)
Siguiendo las directrices del proyecto, el análisis se restringe estrictamente a las siguientes columnas de la hoja de necesidades:
- **Nombre Tarjeta:** Categoría de alto nivel.
- **Texto explicativo:** Descripción cualitativa de la situación.
- **Código Problema:** Identificador jerárquico.
- **Problema / Necesidad:** Definición técnica de la carencia.
- **Urgencia / Importancia:** Pesos de criticidad.

Este enfoque simplificado garantiza que el modelo aprenda de la **semántica del problema** y no de variables externas ruidosas.

## 3. Arquitectura Implementada
Se ha establecido un pipeline que:
1.  **Limpia** el texto legal (Objeto Social) de las empresas.
2.  **Unifica** los históricos de recomendaciones con el catálogo de planes.
3.  **Entrena** un XGBoost que actúa como un "filtro de experto".

## 4. Logros y Dificultades
- **Logro:** Se ha logrado integrar el ML dentro de la función matemática de optimización, creando un modelo híbrido.
- **Dificultad:** La unificación de códigos entre diferentes Excels es la parte más sensible del proceso.
- **Situación:** Se ha detectado que el "Texto Explicativo" contiene información vital que TF-IDF no está explotando plenamente aún.
