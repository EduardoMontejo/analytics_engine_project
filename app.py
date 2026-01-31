import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Cassandra Column-Family Simulator", layout="wide")
st.title("🧱 Cassandra Column-Family Simulator (Streamlit)")
st.caption("Simulación educativa del modelo de Column Families (no es Cassandra real).")

# -------------------------
# Init column families
# -------------------------
FAMILIES = ["Datos_Usuario", "Datos_Geograficos", "Datos_Metricas"]

def init_state():
    for fam in FAMILIES:
        if fam not in st.session_state:
            # Estructura: family[row_key] = {"col1": val1, "col2": val2, ...}
            st.session_state[fam] = {}

init_state()

# Shortcuts
CF_USER = st.session_state["Datos_Usuario"]
CF_GEO = st.session_state["Datos_Geograficos"]
CF_MET = st.session_state["Datos_Metricas"]

# -------------------------
# Sidebar: Insert form
# -------------------------
st.sidebar.header("✍️ Insertar registro (todas las familias)")

with st.sidebar.form("insert_all_families", clear_on_submit=False):
    customer_id = st.text_input("Row Key (Customer ID)", placeholder="Ej: CUST-001")

    st.markdown("### Datos_Usuario")
    nombre = st.text_input("Nombre", placeholder="Ej: Ana")
    email = st.text_input("Email", placeholder="ana@email.com")
    plan = st.selectbox("Plan", ["basic", "pro", "enterprise"], index=0)

    st.markdown("### Datos_Geograficos")
    pais = st.text_input("País", placeholder="España")
    ciudad = st.text_input("Ciudad", placeholder="Madrid")
    lat = st.number_input("Latitud", value=40.4168, format="%.6f")
    lon = st.number_input("Longitud", value=-3.7038, format="%.6f")

    st.markdown("### Datos_Metricas")
    churn = st.selectbox("Churn", ["no", "yes"], index=0)
    sesiones_30d = st.number_input("Sesiones (últimos 30d)", min_value=0, value=10, step=1)
    gasto_total = st.number_input("Gasto total (€)", min_value=0.0, value=99.99, step=1.0)
    last_update = int(time.time())

    submitted = st.form_submit_button("Insertar / Actualizar")

if submitted:
    key = customer_id.strip()
    if not key:
        st.sidebar.error("Customer ID no puede estar vacío.")
    else:
        # Upsert atómico "simulado": escribimos en las 3 CF con misma row key
        CF_USER[key] = {"nombre": nombre, "email": email, "plan": plan}
        CF_GEO[key] = {"pais": pais, "ciudad": ciudad, "lat": lat, "lon": lon}
        CF_MET[key] = {
            "churn": churn,
            "sesiones_30d": int(sesiones_30d),
            "gasto_total": float(gasto_total),
            "last_update_epoch": last_update,
        }
        st.sidebar.success(f"✅ Upsert aplicado para `{key}` en las 3 familias.")

st.sidebar.divider()

# -------------------------
# Helpers
# -------------------------
def family_to_df(family_dict: dict, family_name: str) -> pd.DataFrame:
    """Convierte CF a DataFrame con row_key explícita."""
    if not family_dict:
        return pd.DataFrame(columns=["row_key", "family"])
    rows = []
    for rk, cols in family_dict.items():
        row = {"row_key": rk, "family": family_name}
        row.update(cols)
        rows.append(row)
    return pd.DataFrame(rows)

def joined_view() -> pd.DataFrame:
    """Vista combinada (solo para UI)."""
    keys = set(CF_USER.keys()) | set(CF_GEO.keys()) | set(CF_MET.keys())
    rows = []
    for k in sorted(keys):
        row = {"customer_id": k}
        row.update({f"user_{col}": val for col, val in CF_USER.get(k, {}).items()})
        row.update({f"geo_{col}": val for col, val in CF_GEO.get(k, {}).items()})
        row.update({f"met_{col}": val for col, val in CF_MET.get(k, {}).items()})
        rows.append(row)
    return pd.DataFrame(rows)

# -------------------------
# Main layout
# -------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📦 Column Families",
    "🔎 Buscar por Row Key",
    "🧩 Vista combinada",
    "🧹 Admin",
    "🔭 Consulta",
    "📈 Analítica"
])



with tab1:
    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.subheader("Datos_Usuario")
        df_u = family_to_df(CF_USER, "Datos_Usuario")
        st.dataframe(df_u, use_container_width=True, height=350)

    with c2:
        st.subheader("Datos_Geograficos")
        df_g = family_to_df(CF_GEO, "Datos_Geograficos")
        st.dataframe(df_g, use_container_width=True, height=350)

    with c3:
        st.subheader("Datos_Metricas")
        df_m = family_to_df(CF_MET, "Datos_Metricas")
        st.dataframe(df_m, use_container_width=True, height=350)

with tab2:
    st.subheader("GET por Row Key (Customer ID)")
    key = st.text_input("Customer ID", placeholder="Ej: CUST-001", key="search_key")

    if key.strip():
        k = key.strip()
        colA, colB, colC = st.columns(3, gap="large")

        with colA:
            st.markdown("**Datos_Usuario**")
            st.json(CF_USER.get(k, {}))

        with colB:
            st.markdown("**Datos_Geograficos**")
            st.json(CF_GEO.get(k, {}))

        with colC:
            st.markdown("**Datos_Metricas**")
            st.json(CF_MET.get(k, {}))

        if (k not in CF_USER) and (k not in CF_GEO) and (k not in CF_MET):
            st.warning("No hay registros para esa Row Key.")

with tab3:
    st.subheader("Vista combinada (para visualizar)")
    st.caption("Esto simula un 'join' solo en la UI. Cassandra no hace joins en lectura.")
    df_join = joined_view()
    st.dataframe(df_join, use_container_width=True)

with tab4:
    st.subheader("Administración")
    st.write(f"Total keys en Datos_Usuario: **{len(CF_USER)}**")
    st.write(f"Total keys en Datos_Geograficos: **{len(CF_GEO)}**")
    st.write(f"Total keys en Datos_Metricas: **{len(CF_MET)}**")

    st.divider()
    if st.button("🗑️ Borrar todo (reset)"):
        for fam in FAMILIES:
            st.session_state[fam] = {}
        st.success("Store reiniciado. Recarga o continúa insertando nuevos registros.")
with tab5:
    st.subheader("🔭 Consulta (lectura selectiva de columnas)")
    st.caption("Simula el *column pruning* de Cassandra: leer solo las columnas necesarias reduce I/O y ancho de banda.")

    # Unir el universo de columnas disponibles (con prefijos para evitar colisiones)
    all_cols = []
    for col in (set().union(*(CF_USER.values())) if CF_USER else set()):
        all_cols.append(f"user_{col}")
    for col in (set().union(*(CF_GEO.values())) if CF_GEO else set()):
        all_cols.append(f"geo_{col}")
    for col in (set().union(*(CF_MET.values())) if CF_MET else set()):
        all_cols.append(f"met_{col}")

    all_cols = sorted(set(all_cols))

    if not all_cols:
        st.info("Aún no hay columnas disponibles. Inserta registros primero.")
    else:
        selected_cols = st.multiselect(
            "Selecciona las columnas que deseas leer",
            options=all_cols,
            default=all_cols[: min(5, len(all_cols))]
        )

        run = st.button("Ejecutar consulta")

        if run:
            start = time.perf_counter()

            # Construir resultado solo con las columnas seleccionadas
            keys = sorted(set(CF_USER.keys()) | set(CF_GEO.keys()) | set(CF_MET.keys()))
            rows = []

            for k in keys:
                row = {"customer_id": k}

                # user_*
                if any(c.startswith("user_") for c in selected_cols):
                    for c in selected_cols:
                        if c.startswith("user_"):
                            base = c.replace("user_", "", 1)
                            if base in CF_USER.get(k, {}):
                                row[c] = CF_USER[k][base]

                # geo_*
                if any(c.startswith("geo_") for c in selected_cols):
                    for c in selected_cols:
                        if c.startswith("geo_"):
                            base = c.replace("geo_", "", 1)
                            if base in CF_GEO.get(k, {}):
                                row[c] = CF_GEO[k][base]

                # met_*
                if any(c.startswith("met_") for c in selected_cols):
                    for c in selected_cols:
                        if c.startswith("met_"):
                            base = c.replace("met_", "", 1)
                            if base in CF_MET.get(k, {}):
                                row[c] = CF_MET[k][base]

                rows.append(row)

            df = pd.DataFrame(rows)

            end = time.perf_counter()
            elapsed_ms = (end - start) * 1000

            # Calcular columnas totales disponibles (para simular "ignoradas")
            # Universo real: columnas combinadas en vista join
            join_df = joined_view()
            # quitamos customer_id si está
            total_available = max(0, len(join_df.columns) - (1 if "customer_id" in join_df.columns else 0))

            selected_count = len(selected_cols)
            ignored = max(0, total_available - selected_count)

            st.metric("Tiempo de procesamiento (ms)", f"{elapsed_ms:.2f}")
            st.info(f"Columnas ignoradas: **{ignored}** (simula ahorro de ancho de banda / I/O)")

            # Mostrar resultado
            if selected_cols:
                # Reordenar columnas: customer_id primero
                final_cols = ["customer_id"] + selected_cols
                # Asegurar columnas existentes (por si no hay data para alguna)
                for c in final_cols:
                    if c not in df.columns:
                        df[c] = None
                st.dataframe(df[final_cols], use_container_width=True)
            else:
                st.warning("No seleccionaste columnas. Selecciona al menos una para ejecutar la consulta.")
with tab6:
    st.subheader("📈 Analítica: Gasto_Publicitario por Ciudad")
    st.caption("Agregación tipo OLAP (didáctica) sobre columnas específicas.")

    # Construir dataset mínimo SOLO con las 2 columnas implicadas:
    # - Ciudad: geo_ciudad
    # - Gasto_Publicitario: met_gasto_publicitario
    keys = sorted(set(CF_GEO.keys()) | set(CF_MET.keys()))

    rows = []
    for k in keys:
        ciudad = CF_GEO.get(k, {}).get("ciudad")
        gasto_pub = CF_MET.get(k, {}).get("gasto_publicitario")

        # Solo añadimos filas con ambas columnas disponibles
        if ciudad is not None and gasto_pub is not None:
            rows.append({"Ciudad": ciudad, "Gasto_Publicitario": float(gasto_pub)})

    if not rows:
        st.warning(
            "No hay datos suficientes para esta analítica.\n\n"
            "Asegúrate de insertar registros con:\n"
            "- `Datos_Geograficos.ciudad`\n"
            "- `Datos_Metricas.gasto_publicitario` (Gasto_Publicitario)\n"
        )
    else:
        df = pd.DataFrame(rows)

        # Agregación: SUM(Gasto_Publicitario) por Ciudad
        agg = df.groupby("Ciudad", as_index=True)["Gasto_Publicitario"].sum().sort_values(ascending=False)

        # Gráfico de barras (Streamlit)
        st.bar_chart(agg)

        st.markdown("**Tabla de soporte**")
        st.dataframe(agg.reset_index(), use_container_width=True)

        st.info(
            "💡 **Por qué esto es ultra rápido en un sistema orientado a columnas (estilo Cassandra/wide-row):** "
            "para calcular `SUM(Gasto_Publicitario) BY Ciudad`, el motor solo necesita **escanear esas dos columnas** "
            "(`Ciudad` y `Gasto_Publicitario`). No necesita leer el resto de columnas/atributos del registro. "
            "Ese *column pruning* reduce I/O y ancho de banda, acelerando mucho las agregaciones."
        )

