# Fase 2: Procesamiento Semántico (Tarjetas y Descripciones)

## 1. El Problema del Ruido Textual
En la fase inicial, el modelo solo analizaba el "Objeto Social" de la empresa. Sin embargo, las necesidades del catálogo corporativo tienen un lenguaje técnico muy específico ("Nombre Tarjeta" y "Texto Explicativo") que define el contexto del problema.

## 2. Solución: Arquitectura de Doble Vectorización
Se ha implementado una arquitectura que procesa dos flujos de texto independientes:
1.  **Vector Empresa (Social):** Captura el sector y la actividad (ej. "Construcción", "Software").
2.  **Vector Necesidad (Card):** Captura la semántica del problema (ej. "renegociar deuda", "optimización de cobros").

### Mejoras Técnicas:
- **Heurística de Sectores:** Clasificación automática en grandes grupos (Tecnología, Agrario, etc.) para simplificar el aprendizaje.
- **Limpieza NLP:** Eliminación de "Stopwords" legales (ej: "la sociedad tiene por objeto") que ensucian los vectores.
- **Aumento de Precisión:** El modelo ha pasado de un **87%** a un **93.8% de ROC-AUC**, demostrando que el texto explicativo de las tarjetas era la pieza clave.

## 3. Resultados y Logros
- **Logro:** El motor ahora entiende que un plan de "Factoring" es más relevante para una empresa de "Servicios" con problemas de "Cobro" descritos en la tarjeta.
- **Situación:** Aunque el ML funciona, el catálogo actual es tan estable que el optimizador matemático a menudo llega a la misma solución óptima por reglas de negocio. Esto valida que el ML no "rompe" la lógica, sino que la refuerza.

## 4. Próximos pasos
La siguiente fase consistirá en **aprendizaje inverso de pesos**, para no depender de valores manuales (alpha=4, beta=3) sino descubrir cuáles son los pesos reales que usan los asesores.
