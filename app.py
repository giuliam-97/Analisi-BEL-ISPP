import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# STREAMLIT CONFIG
# =====================================================
st.set_page_config(page_title="BEL & ALM Analysis", layout="wide")
st.title("📊 BEL and ALM Analysis")
st.markdown(
    "***Note:* From January 2026, the liabilities referred to 4Q '25 have been applied (we haven't received the 1Q '26 yet).**"
)

# =====================================================
# CONSTANTS
# =====================================================
BEL_ROWS = [
    "BEL Undiscounted",
    "BEL Discounted",
    "BEL IR DOWN",
    "Stress Down",
    "BEL IR UP",
    "Stress Up"
]

VAR_ROWS = [
    "Δ BEL Undiscounted",
    "Δ BEL Discounted",
    "Δ BEL IR DOWN",
    "Δ Stress Down",
    "Δ BEL IR UP",
    "Δ Stress Up"
]

file_name = "Summary.xlsx"

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_bel_tables():
    df_raw = pd.read_excel(
        file_name,
        sheet_name="Analisi BEL Aggregate",
        #usecols="B:N",
        header=None
    )

    def split_tables(df):
        tables, start = [], None
        for i in range(len(df)):
            if not df.iloc[i].isna().all():
                start = i if start is None else start
            elif start is not None:
                tables.append(df.iloc[start:i])
                start = None
        if start is not None:
            tables.append(df.iloc[start:])
        return tables

    def prepare(df):
        df = df.copy().reset_index(drop=True)
        header = df.iloc[1]
        df = df.iloc[2:]
        df.columns = header
        df = df.set_index(df.columns[0])
        return df.apply(pd.to_numeric, errors="coerce")

    t1, t2, t3 = split_tables(df_raw)
    return prepare(t1), prepare(t2), prepare(t3)

@st.cache_data
def load_alm():
    df = pd.read_excel(
        file_name,
        sheet_name="Analisi ALM",
        usecols="A:E"
    )
    df = df.dropna(how="all")
    df = df.set_index(df.columns[0])
    return df.apply(pd.to_numeric, errors="coerce")

table_1, table_2, table_3 = load_bel_tables()

# =====================================================
# REMOVE COLUMNS WITH NaN INDEX
# =====================================================
table_1 = table_1.loc[:, table_1.columns.notna()]
table_2 = table_2.loc[:, table_2.columns.notna()]
table_3 = table_3.loc[:, table_3.columns.notna()]

df_alm = load_alm()

# =====================================================
# PLOT FUNCTION (standard)
# =====================================================
def plot_interactive(df, title):
    df_plot = df.copy()
    df_plot["Periods"] = df_plot.index
    df_long = df_plot.melt(
        id_vars="Periods",
        var_name="Metric",
        value_name="Values"
    )
    fig = px.line(
        df_long,
        x="Periods",
        y="Values",
        color="Metric",
        markers=True,
        title=title
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# PLOT FUNCTION WITH AVERAGE (ALM only)
# =====================================================
def plot_interactive_with_avg(df, title):
    df_plot = df.copy()
    df_plot["Periods"] = df_plot.index
    df_long = df_plot.melt(
        id_vars="Periods",
        var_name="Metric",
        value_name="Values"
    )

    fig = px.line(
        df_long,
        x="Periods",
        y="Values",
        color="Metric",
        markers=True,
        title=title
    )

    # Add dashed average line per metric, matching its color
    colors = px.colors.qualitative.Plotly
    metrics = df_long["Metric"].unique()

    for i, metric in enumerate(metrics):
        avg_val = df_long[df_long["Metric"] == metric]["Values"].mean()
        color = colors[i % len(colors)]
        fig.add_hline(
            y=avg_val,
            line_dash="dash",
            line_color=color,
            line_width=1.2,
            opacity=0.6,
            annotation_text=f"Avg {metric}: {avg_val:.2f}",
            annotation_position="top right",
            annotation_font_size=11,
            annotation_font_color=color,
        )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# GRAPH 1 - BEL
# =====================================================
st.subheader("📌 BEL")

rows = [r for r in BEL_ROWS if r in table_1.index]

selected = st.multiselect(
    "Select metrics",
    rows,
    default=rows
)

index_options = list(table_1.columns)

st.markdown("**Select reference period**")
c1, c2 = st.columns(2)

start = c1.selectbox("Start period", index_options, index=0)
end = c2.selectbox("End period", index_options, index=len(index_options) - 1)

cols = index_options[
    index_options.index(start): index_options.index(end) + 1
]

if selected and cols:
    df_plot = table_1.loc[selected, cols].T
    plot_interactive(df_plot, "BEL")

# =====================================================
# GRAPH 2 - BEL VARIATION
# =====================================================
st.divider()
st.subheader("📌 BEL Variation")

trend_type = st.selectbox(
    "Select trend type",
    ["Monetary Trend BEL", "% Trend BEL"]
)

df_trend = table_2 if trend_type == "Monetary Trend BEL" else table_3

rows = [r for r in VAR_ROWS if r in df_trend.index]

selected = st.multiselect(
    "Select metrics",
    rows,
    default=rows,
    key="trend_rows"
)

index_options = list(df_trend.columns)

st.markdown("**Select reference period**")
c1, c2 = st.columns(2)

start = c1.selectbox(
    "Start period",
    index_options,
    index=0,
    key="trend_start"
)
end = c2.selectbox(
    "End period",
    index_options,
    index=len(index_options) - 1,
    key="trend_end"
)

cols = index_options[
    index_options.index(start): index_options.index(end) + 1
]

if selected and cols:
    df_plot = df_trend.loc[selected, cols].T
    plot_interactive(df_plot, trend_type)

# =====================================================
# GRAPH 3 - ALM
# =====================================================
st.divider()
st.subheader("📌 ALM Analysis")

cols_selected = st.multiselect(
    "Select metrics",
    df_alm.columns.tolist(),
    default=df_alm.columns.tolist()
)

alm_index_options = list(df_alm.index)

st.markdown("**Select reference period**")
c1, c2 = st.columns(2)

alm_start = c1.selectbox(
    "Start period",
    alm_index_options,
    index=0,
    key="alm_start"
)
alm_end = c2.selectbox(
    "End period",
    alm_index_options,
    index=len(alm_index_options) - 1,
    key="alm_end"
)

df_alm_f = df_alm.loc[
    alm_index_options[
        alm_index_options.index(alm_start):
        alm_index_options.index(alm_end) + 1
    ]
]

if not df_alm_f.empty:
    row_ref = df_alm.loc[alm_end]

    duration_liabilities = row_ref["Duration Liabilities"]
    surplus_asset_pct = row_ref["Surplus Asset %"]

    duration_asset_opt = duration_liabilities * (1 - surplus_asset_pct)
    duration_asset_current = row_ref["Duration Asset"]

    st.divider()

    if st.button("Optimize Asset Duration"):
        st.info(
            f"Optimal Asset Duration to eliminate mismatch on **{alm_end}**:\n"
            f"**{duration_asset_opt:.2f}y** (compared to the actual value of: **{duration_asset_current:.2f}y**)"
        )

if cols_selected and not df_alm_f.empty:
    plot_interactive_with_avg(df_alm_f[cols_selected], "Duration Trend")
