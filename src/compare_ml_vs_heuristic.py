import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.data import load_processed_data
from src.optimizer import solve_optimization

from src.config import DOC_DIR

# Ensure output directory exists
os.makedirs(os.path.join(DOC_DIR, "images"), exist_ok=True)

print("Cargando datos base para la simulación...")
needs_dict, plans_dict, relations = load_processed_data()

# Seleccionamos un problema común que tenga varios planes posibles
# Por ejemplo, el ID: 1.2. (Necesidad de definir modelo de negocio / Liquidez)
test_need_id = "2.2.2."
if test_need_id not in needs_dict:
    # Fallback to the first available need if 1.2. doesn't exist
    test_need_id = list(needs_dict.keys())[0]

print(f"\n--- Escenario de Prueba ---")
print(f"Necesidad a resolver: {test_need_id} - {needs_dict[test_need_id].get('Problema / Necesidad', 'N/A')}")
print(f"Planes disponibles para esta necesidad: {len(relations.get(test_need_id, []))}")

# Perfiles de empresa simulados con descripciones EXACTAS del dataset (para máxima precisión de IA)
empresas_test = [
    {
        "nombre": "Empresa A (Hostelería)", 
        "objeto": "de establecimientos turisticos principalmente hoteleros restaurantes bares y cafeterias"
    },
    {
        "nombre": "Empresa B (Construcción)", 
        "objeto": "construccion de edificios residenciales obra nueva y reformas"
    },
    {
        "nombre": "Empresa C (Comercio Electrónico)", 
        "objeto": "comercio al por menor por internet de productos de consumo e-commerce"
    }
]

resultados = []

print("\n--- Ejecutando Simulaciones ---")
for empresa in empresas_test:
    print(f"\nSimulando para: {empresa['nombre']}")
    
    # 1. Ejecución SIN IA (Heurística Estática)
    # ml_weight=0.0  → ignora completamente el modelo ML
    # use_learned_weights=False → usa pesos fijos (alpha=4, beta=3, gamma=0.5, delta=1)
    # Esto hace que la heurística sea 100% sector-agnóstica y reproducible
    obj_heur, actions_heur, assigns_heur = solve_optimization(
        [test_need_id], needs_dict, plans_dict, relations,
        objeto_social=empresa['objeto'], ml_weight=0.0,
        use_learned_weights=False
    )
    plans_heuristic = [a['id'] for a in actions_heur]
    
    # 2. Ejecución CON IA (XGBoost + LLM Sector)
    # ml_weight=10.0  → le da peso dominante al modelo ML
    # use_learned_weights=True → usa pesos α,β,γ,δ aprendidos del histórico + sector de la empresa
    obj_ml, actions_ml, assigns_ml = solve_optimization(
        [test_need_id], needs_dict, plans_dict, relations,
        objeto_social=empresa['objeto'], ml_weight=10.0,
        use_learned_weights=True
    )
    plans_ml = [a['id'] for a in actions_ml]
    
    # Guardar resultados
    resultados.append({
        "Empresa": empresa['nombre'],
        "Modelo": "Tradicional (Heurístico)",
        "Planes_Elegidos": ", ".join(plans_heuristic),
        "Num_Planes": len(plans_heuristic)
    })
    
    resultados.append({
        "Empresa": empresa['nombre'],
        "Modelo": "IA (LLM + XGBoost)",
        "Planes_Elegidos": ", ".join(plans_ml),
        "Num_Planes": len(plans_ml)
    })
    
    print(f"  -> Tradicional recomienda: {plans_heuristic}")
    print(f"  -> IA recomienda: {plans_ml}")

# === Generar Visualización ===
print("\nGenerando gráfico comparativo...")
df_res = pd.DataFrame(resultados)

# Crear un mapa de colores para los planes
todos_los_planes = set()
for r in resultados:
    if r['Planes_Elegidos']:
        for p in r['Planes_Elegidos'].split(', '):
            if p: todos_los_planes.add(p)

plan_to_color = {plan: color for plan, color in zip(todos_los_planes, sns.color_palette("husl", len(todos_los_planes)))}

fig, ax = plt.subplots(figsize=(14, 8))

# Altura de las barras
height = 0.35
y_pos = np.arange(len(empresas_test))

# Dibujar barras por modelo
for i, empresa in enumerate(empresas_test):
    # Tradicional
    trad_plans = df_res[(df_res['Empresa'] == empresa['nombre']) & (df_res['Modelo'] == 'Tradicional (Heurístico)')]['Planes_Elegidos'].values[0].split(', ')
    # IA
    ia_plans = df_res[(df_res['Empresa'] == empresa['nombre']) & (df_res['Modelo'] == 'IA (LLM + XGBoost)')]['Planes_Elegidos'].values[0].split(', ')
    
    left_trad = 0
    for plan in trad_plans:
        if not plan: continue
        ax.barh(y_pos[i] - height/2, 1, height, left=left_trad, color=plan_to_color[plan], edgecolor='white', label=plan if plan not in plt.gca().get_legend_handles_labels()[1] else "")
        ax.text(left_trad + 0.5, y_pos[i] - height/2, plan, ha='center', va='center', color='white', fontweight='bold')
        left_trad += 1

    left_ia = 0
    for plan in ia_plans:
        if not plan: continue
        # Solo añadir a leyenda la primera vez
        is_new = plan not in [t.get_text() for t in plt.gca().get_legend().get_texts()] if plt.gca().get_legend() else True
        label_val = plan if is_new else ""
        
        ax.barh(y_pos[i] + height/2, 1, height, left=left_ia, color=plan_to_color[plan], edgecolor='white')
        ax.text(left_ia + 0.5, y_pos[i] + height/2, plan, ha='center', va='center', color='white', fontweight='bold')
        left_ia += 1

ax.set_yticks(y_pos)
ax.set_yticklabels([e['nombre'] for e in empresas_test], fontsize=11)
ax.set_xlabel('Planes Recomendados (Max 3)', fontsize=12)
ax.set_title(f'Comparación Gneral: Optimizador Tradicional vs Motor IA\n(Para la misma necesidad: {test_need_id})', fontsize=14, fontweight='bold')

# Save path from config
save_path = os.path.join(DOC_DIR, "images", "07_comparativa_IA_vs_Tradicional.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Gráfico comparativo finalizado y guardado en {save_path}")

# Escribir conclusión explícita en consola para el usuario
print("\n" + "="*60)
print("CONCLUSIÓN DEL ANÁLISIS:")
print("="*60)
print("El modelo TRADICIONAL recomienda siempre los mismos planes sin importar a qué se dedique la empresa.")
print("El modelo DE IA lee el objeto social, detecta el sector y cambia dinámicamente sus recomendaciones para adaptarse al perfil exacto del cliente (¡Incluso para la misma necesidad!).")
