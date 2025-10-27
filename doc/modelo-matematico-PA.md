# Modelado Matemático del Problema de Asignación de Planes de Acción Personalizados

## 1. Introducción

Este documento presenta la formulación matemática del problema de asignación automática de planes de acción financieros personalizados para pequeñas y medianas empresas (PYMEs). El modelo se basa en técnicas de optimización combinatoria para maximizar la efectividad de las recomendaciones considerando la urgencia, importancia, plazo de ejecución y complejidad de las acciones.

## 2. Definición del Problema

El sistema AsFin analiza la situación financiera de las empresas mediante 6 indicadores clave y detecta hasta 52 necesidades categorizadas. Para cada conjunto de necesidades detectadas, el algoritmo debe recomendar un conjunto óptimo de planes de acción que:

- Minimice el número total de acciones recomendadas
- Priorice las necesidades más urgentes e importantes
- Considere el plazo de implementación y la complejidad de las acciones
- Respete las restricciones y dependencias entre necesidades y acciones

## 3. Conjuntos y Parámetros

### 3.1 Conjuntos

- **N**: Conjunto de necesidades detectadas, donde *i ∈ N* representa una necesidad específica
- **A**: Conjunto de acciones/planes disponibles, donde *j ∈ A* representa una acción específica
- **R**: Conjunto de relaciones válidas entre necesidades y acciones, donde *(i,j) ∈ R* indica que la acción *j* puede resolver la necesidad *i*

### 3.2 Parámetros

Para cada necesidad *i ∈ N*:
- **u_i**: Nivel de urgencia (1: Menos urgente, 2: Urgente, 3: Muy urgente)
- **imp_i**: Nivel de importancia (1: Menos importante, 2: Importante, 3: Muy importante)

Para cada acción *j ∈ A*:
- **p_j**: Plazo de ejecución en meses
- **c_j**: Nivel de complejidad (1: Sencillo, 2: Complejo)
- **cond_j**: Función booleana que determina si la acción *j* es aplicable según las condiciones objetivas de la empresa

### 3.3 Función de Peso

La función de peso **w_ij** para la asignación de la acción *j* a la necesidad *i* se define como:

**w_ij = α · u_i + β · imp_i - γ · p_j - δ · c_j**

Donde α, β, γ, δ son parámetros de ponderación que reflejan la importancia relativa de cada criterio.

## 4. Variables de Decisión

- **x_ij**: Variable binaria que toma el valor 1 si la acción *j* se asigna a la necesidad *i*, y 0 en caso contrario
- **y_j**: Variable binaria que toma el valor 1 si la acción *j* es seleccionada en el plan final, y 0 en caso contrario

## 5. Función Objetivo

Maximizar la efectividad ponderada de la asignación:

**max Σ_(i∈N) Σ_(j∈A:(i,j)∈R) w_ij · x_ij**

## 6. Restricciones

### 6.1 Cobertura de necesidades
Cada necesidad debe estar cubierta por al menos una acción:

**Σ_(j∈A:(i,j)∈R) x_ij ≥ 1, ∀i ∈ N**

### 6.2 Coherencia de selección
Si una acción se asigna a una necesidad, debe estar seleccionada:

**x_ij ≤ y_j, ∀i ∈ N, ∀j ∈ A : (i,j) ∈ R**

### 6.3 Restricciones de aplicabilidad
Solo se pueden seleccionar acciones que cumplan las condiciones objetivas:

**y_j ≤ cond_j, ∀j ∈ A**

### 6.4 Restricción de minimalidad
Minimizar el número total de acciones seleccionadas añadiendo un término de penalización:

**Σ_(j∈A) y_j ≤ M**

Donde M es un límite superior razonable del número de acciones.

### 6.5 Restricciones de no negatividad y binaridad
**x_ij ∈ {0,1}, ∀i ∈ N, ∀j ∈ A : (i,j) ∈ R**
**y_j ∈ {0,1}, ∀j ∈ A**

## 7. Catálogo de Necesidades

### 7.1 Necesidades Económico-Financieras

**N1 (1.2.1.)**: Financiación de inversiones en activos fijos
- *Descripción*: Riesgo de no poder generar recursos a tiempo para pagar inversiones
- *Urgencia*: 1 (Menos urgente)
- *Importancia*: 2 (Importante)

**N2 (1.2.4.)**: Capacidad de pago de deuda financiera
- *Descripción*: Capacidad de pago inferior a estándares del mercado
- *Urgencia*: 2 (Urgente)
- *Importancia*: 1 (Menos importante)

**N3 (1.2.8.)**: Colchón de tesorería insuficiente
- *Descripción*: Tesorería ajustada que compromete cumplimiento de pagos
- *Urgencia*: 2 (Urgente)
- *Importancia*: 2 (Importante)

### 7.2 Necesidades de Liquidez

**N4 (3.2.1.)**: Generación de liquidez deficiente
- *Descripción*: El negocio no genera liquidez suficiente
- *Urgencia*: 3 (Muy urgente)
- *Importancia*: 3 (Muy importante)

## 8. Catálogo de Planes de Acción

### 8.1 Planes de Reestructuración Financiera

**A1 (1.2.1.a.)**: Distribución racional de la deuda
- *Descripción*: Reestructurar deuda de corto a largo plazo
- *Plazo*: 6 meses
- *Complejidad*: 2 (Complejo)
- *Condición*: DFB ≥ 10% Pasivo Total

**A2 (1.2.4.b.)**: Reducir deuda estructural
- *Descripción*: Amortizar anticipadamente deuda bancaria
- *Plazo*: 6 meses
- *Complejidad*: 1 (Sencillo)
- *Condición*: Siempre aplicable

**A3 (1.2.4.c.)**: Renegociar calendarios de amortización
- *Descripción*: Aumentar plazos de vencimiento, solicitar carencias
- *Plazo*: 3 meses
- *Complejidad*: 1 (Sencillo)
- *Condición*: Financiación financiera ≥ 10% Pasivo Y Ebitda > 0 Y 4x ≤ DFN/Ebitda ≤ 7x

### 8.2 Planes de Mejora de Ingresos y Costos

**A4 (1.2.4.a.)**: Identificar y aplicar palancas de Ebitda
- *Descripción*: Revisar precios, renegociar con clientes/proveedores, ajustar gastos
- *Plazo*: 6 meses
- *Complejidad*: 2 (Complejo)
- *Condición*: (Ebitda/Ventas ≤ Débil) Y (DFN/Ebitda ≤ Débil)

### 8.3 Planes de Mejora de Liquidez

**A5 (1.2.8.a.)**: Mejora la tesorería
- *Descripción*: Vender activos no estratégicos, anticipar cobros, aplazar gastos
- *Plazo*: 2 meses
- *Complejidad*: 1 (Sencillo)
- *Condición*: Ratio Liquidez inmediata ≤ Débil

**A6 (1.2.8.b.)**: Aplaza pago de impuestos
- *Descripción*: Solicitar aplazamiento de impuestos según normativa
- *Plazo*: 3 meses
- *Complejidad*: 1 (Sencillo)
- *Condición*: Siempre aplicable

**A7 (1.2.7.a.)**: Mejora la liquidez operativa
- *Descripción*: Retrasar compras, revisar condiciones de cobro y pago
- *Plazo*: 1 mes
- *Complejidad*: 2 (Complejo)
- *Condición*: Siempre aplicable

### 8.4 Planes de Financiación

**A8 (3.1.1.a.)**: Solicita nueva financiación
- *Descripción*: Negociar con bancos nueva financiación comercial o financiera
- *Plazo*: 2 meses
- *Complejidad*: 1 (Sencillo)
- *Condición*: Potencial de nueva financiación ≥ Normal

**A9 (3.1.2.a.)**: Renegocia vencimientos de deuda
- *Descripción*: Solicitar aplazamientos parciales de vencimientos próximos
- *Plazo*: 2 meses
- *Complejidad*: 1 (Sencillo)
- *Condición*: DF corto plazo ≥ 5% Pasivo Y Ratio DFN/Ebitda ≥ Normal

### 8.5 Planes de Optimización de Recursos

**A10 (1.2.10.a.)**: Reduce inversión en stocks
- *Descripción*: Revisar almacén, liquidar productos obsoletos, optimizar pedidos
- *Plazo*: 6 meses
- *Complejidad*: 2 (Complejo)
- *Condición*: Existencias ≥ 10% Activo Total Y Rotación de Existencias ≤ Débil

## 9. Matriz de Relaciones Necesidades-Acciones

Las relaciones válidas (i,j) ∈ R se definen como:

- **N1** → {A1}: Financiación de activos fijos
- **N2** → {A2, A3, A4}: Capacidad de pago de deuda
- **N3** → {A5, A6}: Colchón de tesorería
- **N4** → {A7, A8, A9, A10}: Generación de liquidez

## 10. Algoritmo de Resolución

### 10.1 Fase de Preprocesamiento
1. Evaluar condiciones objetivas para cada acción j ∈ A
2. Filtrar acciones no aplicables
3. Calcular pesos w_ij para todas las relaciones válidas

### 10.2 Fase de Optimización
1. Resolver el problema de optimización lineal entera
2. Obtener la asignación óptima x_ij y selección y_j
3. Verificar factibilidad de la solución

### 10.3 Fase de Post-procesamiento
1. Generar el plan de acción recomendado
2. Ordenar acciones por prioridad (urgencia, importancia, plazo, complejidad)
3. Incluir planes aplazados que dependan de acciones asignadas

## 11. Extensiones del Modelo

### 11.1 Dependencias Temporales
Incluir restricciones de precedencia entre acciones:
**y_k ≤ y_j, si la acción k requiere completar la acción j**

### 11.2 Restricciones de Capacidad
Limitar el número de acciones complejas simultáneas:
**Σ_(j∈A:c_j=2) y_j ≤ C_max**

### 11.3 Horizonte Temporal
Considerar ventanas temporales para la ejecución:
**x_ij = 0, si p_j > T_max**

## 12. Parámetros Sugeridos

Basado en la lógica de asesores financieros:
- α (peso urgencia) = 4
- β (peso importancia) = 3  
- γ (penalización plazo) = 0.5
- δ (penalización complejidad) = 1

## 13. Conclusiones

Este modelo matemático proporciona una base sólida para la asignación automática de planes de acción financieros, considerando múltiples criterios de optimización y restricciones prácticas. La formulación como problema de optimización lineal entera permite el uso de solucionadores comerciales eficientes para obtener soluciones óptimas en tiempo razonable.

La estructura modular del modelo facilita la incorporación de nuevas necesidades, acciones y restricciones, así como la calibración de parámetros basada en el aprendizaje de las modificaciones realizadas por asesores expertos.