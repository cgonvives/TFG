import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob

from src.config import ML_DATASET_FINAL, DOC_DIR

# Ensure output directory exists
os.makedirs(os.path.join(DOC_DIR, "images"), exist_ok=True)

# Load final ML dataset
print("Cargando datos...")
df = pd.read_csv(ML_DATASET_FINAL)

# Set aesthetic style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'

# Helper to save with config path
def save_chart(filename):
    path = os.path.join(DOC_DIR, "images", filename)
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()

# 1. Distribución de aceptación
plt.figure(figsize=(8, 6))
sns.countplot(x='accepted', data=df, palette='viridis')
plt.title('Distribución de Clases (Aceptado vs No Aceptado)', fontsize=14)
plt.xlabel('Aceptado (0 = No, 1 = Sí)')
plt.ylabel('Cantidad')
save_chart('01_distribucion_clases.png')
print("Gráfico 1 generado.")

# 2. Top Sectores detectados por el LLM
plt.figure(figsize=(12, 6))
top_sectors = df['sector'].value_counts().head(10)
sns.barplot(x=top_sectors.values, y=top_sectors.index, palette='mako')
plt.title('Top 10 Sectores Económicos (Clasificados por LLM)', fontsize=14)
plt.xlabel('Número de Ocurrencias')
plt.ylabel('Sector')
save_chart('02_top_sectores.png')
print("Gráfico 2 generado.")

# 3. Urgencia vs Importancia (Mapa de calor de necesidades)
plt.figure(figsize=(8, 6))
pivot_ui = pd.crosstab(df['Urgencia'], df['Importancia'])
sns.heatmap(pivot_ui, annot=True, fmt="d", cmap="YlOrRd")
plt.title('Mapa de Calor: Urgencia vs Importancia', fontsize=14)
plt.gca().invert_yaxis()
save_chart('03_urgencia_vs_importancia.png')
print("Gráfico 3 generado.")

# 4. Distribución del Plazo de ejecución por Complejidad
plt.figure(figsize=(10, 6))
sns.boxplot(x='Complejidad', y='Plazo', data=df, palette='Set2')
plt.title('Distribución de Plazos de Ejecución según Complejidad', fontsize=14)
plt.xlabel('Complejidad (1=Sencillo, 2=Complejo, 3=Muy complejo)')
plt.ylabel('Plazo (Semanas/Meses)')
save_chart('04_plazo_vs_complejidad.png')
print("Gráfico 4 generado.")

# 5. Tasa de Aceptación por Sector (Top 8)
plt.figure(figsize=(12, 6))
top8 = df['sector'].value_counts().head(8).index
df_top8 = df[df['sector'].isin(top8)]
accepted_by_sector = df_top8.groupby('sector')['accepted'].mean().sort_values(ascending=False) * 100
sns.barplot(x=accepted_by_sector.values, y=accepted_by_sector.index, palette='icefire')
plt.title('Tasa de Aceptación de Planes por Sector (%)', fontsize=14)
plt.xlabel('Porcentaje de Aceptación (%)')
plt.ylabel('Sector')
save_chart('05_aceptacion_por_sector.png')
print("Gráfico 5 generado.")

# 6. Matriz de Correlación de Features Numéricas
plt.figure(figsize=(8, 6))
numeric_cols = ['Urgencia', 'Importancia', 'Complejidad', 'Plazo', 'accepted']
corr = df[numeric_cols].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, fmt=".2f")
plt.title('Matriz de Correlación de Variables Numéricas', fontsize=14)
save_chart('06_matriz_correlacion.png')
print("Gráfico 6 generado.")

print("\n¡Todas las gráficas se han guardado en doc/images/!")
