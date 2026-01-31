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
tab1, tab2, tab3, tab4 = st.tabs(["📦 Column Families", "🔎 Buscar por Row Key", "🧩 Vista combinada", "🧹 Admin"])

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


