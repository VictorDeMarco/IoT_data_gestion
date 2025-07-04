import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

df = pd.read_csv("csv/Dataset_con_solo_reales.csv")


# Discretizar variables para reglas de asociación (formato tipo cesta)
df_binarized = pd.DataFrame()
df_binarized["tiempo_espera_largo"] = df["time_since_last_event_min"] > 1
df_binarized["tiempo_espera_corto"] = df["time_since_last_event_min"] <= 1
df_binarized["No hay presencia"] = df["tamper_detected"] == 0
df_binarized["Hay presencia"] = df["tamper_detected"] == 1

"""
Solo utilizar esta linea de codigo si el dataset que se esta utilizando contiene tanto ejemplos reales como infectados
df_binarized["Real"] = df["estado"] == "real"
"""


# Generar itemsets frecuentes
frequent_itemsets = apriori(df_binarized, min_support=0.15, use_colnames=True)

# Generar reglas de asociación con confianza mínima de 0.9
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.9)

# Mostrar reglas encontradas
print("🔍 Reglas con confianza >= 0.9:")
print(rules[["antecedents", "consequents", "support", "confidence", "lift"]])

# Generar funciones Python a partir de las reglas
print("\n📜 Traducción de reglas a condiciones Python:")
for idx, row in rules.iterrows():
    ante = [f'd["{a}"] == True' for a in row["antecedents"]]
    cons = [f'd["{c}"] == True' for c in row["consequents"]]
    print(f"if {' and '.join(ante)}:  # soporte: {row['support']:.2f}, confianza: {row['confidence']:.2f}")
    print(f"    # entonces: {' and '.join(cons)}\n")
