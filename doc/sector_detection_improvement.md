# Mejora de Detección de Sectores mediante LLM y NLP

Este documento detalla la transición de un sistema de detección de sectores basado en palabras clave hacia un modelo más robusto utilizando Inteligencia Artificial (LLM).

## Contexto del Problema

El sistema original utilizaba una función `detect_sector` basada en un diccionario estático de palabras clave. Aunque eficiente, este método presentaba limitaciones críticas:

- **Rigidez**: No detectaba variaciones morfológicas (ej. "tecnológica" vs "tecnología").
- **Falta de Semántica**: Términos como "star up" (sin la 't' final o errores tipográficos) o descripciones complejas no eran asociados correctamente, resultando en la categoría genérica "Otros".
- **Mantenimiento**: Cada nuevo sector o variante requería actualización manual de listas.

## Propuesta de Mejora

Hemos implementado un enfoque híbrido que combina la velocidad de las reglas predefinidas con la potencia semántica de los LLMs (como Gemini).

### 1. Diccionario de Palabras Clave Refinado
Se ha ampliado el diccionario para incluir términos derivados y terminología moderna (startup, fintech, etc.), cubriendo los casos más comunes de forma instantánea.

### 2. Clasificación Zero-Shot con LLM
Para descripciones que no coinciden con ninguna palabra clave, el sistema ahora puede realizar una consulta a un modelo de lenguaje. El LLM analiza el "Objeto Social" completo y elige la categoría más probable entre un conjunto dado, entendiendo el contexto semántico más allá de las palabras exactas.

## Implementación Técnica

- **`src/llm_classifier.py`**: Nuevo módulo encargado de la lógica de clasificación avanzada.
- **`src/ml_data_explorer.py` y `src/optimizer.py`**: Actualizados para integrar el "fallback" al LLM cuando el método tradicional falla.

## Resultados Esperados

1. **Mayor Precisión**: El caso "star up tecnológica" ahora se clasifica correctamente como **Tecnología**.
2. **Robustez ante Errores**: Capacidad para entender descripciones con errores ortográficos o lenguaje coloquial.
3. **Mejores Recomendaciones**: Al identificar correctamente el sector, el optimizador puede aplicar pesos específicos de industria más precisos, mejorando la calidad de los planes de acción sugeridos.

---
> [!TIP]
> Esta mejora permite que el sistema sea escalable a nuevas industrias sin necesidad de reprogramar la lógica de detección.
