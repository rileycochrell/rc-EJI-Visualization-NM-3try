import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(
    page_title="TEAM 23: Environmental Justice in New Mexico — 📈 Yearly Comparison",
    page_icon="🌎",
    layout="wide"
)

# ------------------------------
# Hide Streamlit Logo/Sidebar and Add Custom Title
# ------------------------------
st.markdown('<style>div[data-testid="stSidebarNav"] {display: none;}</style>', unsafe_allow_html=True)
st.markdown("""
<style>
div[data-testid="stLogoSpacer"] {
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    height: 100%; padding-top: 40px;
}
div[data-testid="stLogoSpacer"]::before {
    content: "TEAM 23:"; font-size: 30px; font-weight: bold; margin-bottom: 5px;
}
div[data-testid="stLogoSpacer"]::after {
    content: "🌎 Environmental Justice in New Mexico"; font-size: 18px; font-weight: bold; margin-bottom: -40px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Sidebar Navigation
# ------------------------------
with st.sidebar:
    st.write("---")
    st.page_link("streamlit_app.py", label="EJI Visualization", icon="📊")
    st.page_link("pages/3_change_over_years_and_comparison.py", label="EJI – Change Over Years", icon="📈")
    st.page_link("pages/1_What_Goes_Into_EJI.py", label="What Goes Into the EJI?", icon="🧩")
    st.page_link("pages/2_EJI_Scale_and_Categories.py", label="What Does the EJI Mean?", icon="🌡️")

# ------------------------------
# Years & Data Loading
# ------------------------------
AVAILABLE_YEARS = ["2022", "2024"]

# ------------------------------
# Normalize County Names (all years)
# ------------------------------
def normalize_county_names(df):
    if "County" in df.columns:
        df["County"] = (
            df["County"]
            .astype(str)
            .str.strip()
            .str.title()  # title case: ssandoval → Ssandoval
        )
        df["County"] = df["County"].apply(
            lambda x: f"{x} County"
            if not x.lower().endswith("county")
            else x
        )
    return df

@st.cache_data
def load_data_for_year(year: str):
    base = "https://github.com/rileycochrell/rc-EJI-Visualization-NM-3try/raw/refs/heads/main/data"
    state_path = f"{base}/{year}/clean/{year}EJI_StateAverages_RPL.csv"
    county_path = f"{base}/{year}/clean/{year}EJI_NewMexico_CountyMeans.csv"
    return pd.read_csv(state_path), pd.read_csv(county_path)

rename_map = {
    "Mean_EJI": "RPL_EJI",
    "Mean_EBM": "RPL_EBM",
    "Mean_SVM": "RPL_SVM",
    "Mean_HVM": "RPL_HVM",
    "Mean_CBM": "RPL_CBM",
    "Mean_EJI_CBM": "RPL_EJI_CBM"
}

BASE_METRICS = ["RPL_EJI", "RPL_EBM", "RPL_SVM", "RPL_HVM"]
OPTIONAL_METRICS = ["RPL_CBM", "RPL_EJI_CBM"]

pretty = {
    "RPL_EJI": "Overall EJI",
    "RPL_EBM": "Environmental Burden",
    "RPL_SVM": "Social Vulnerability",
    "RPL_HVM": "Health Vulnerability",
    "RPL_CBM": "Climate Burden",
    "RPL_EJI_CBM": "EJI + Climate Burden"
}

dataset_year1_rainbows = {
    "RPL_EJI": "#911eb4", "RPL_EBM": "#c55c29", "RPL_SVM": "#4363d8",
    "RPL_HVM": "#f032e6", "RPL_CBM": "#469990", "RPL_EJI_CBM": "#801650"
}
dataset_year2_rainbows = {
    "RPL_EJI": "#b88be1", "RPL_EBM": "#D2B48C", "RPL_SVM": "#87a1e5",
    "RPL_HVM": "#f79be9", "RPL_CBM": "#94c9c4", "RPL_EJI_CBM": "#f17cb0"
}

# ------------------------------
# Helper Functions
# ------------------------------
def get_contrast_color(hex_color):
    try:
        rgb = tuple(int(hex_color.strip("#")[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return "black"
    brightness = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])
    return "black" if brightness > 150 else "white"

# No Data font is always black because theme is locked to light
def get_theme_color():
    return "black"
    
def display_colored_table_html(df, color_map, pretty_map, cell_color_map=None, title=None):
    if isinstance(df, pd.Series):
        df = df.to_frame().T

    df_display = df.rename(columns=pretty_map)

    if title:
        st.markdown(f"### {title}")

    # ----- Header -----
    header_html = "<tr>"
    for col in df_display.columns:
        # get original key
        orig = [k for k,v in pretty_map.items() if v == col]
        orig_key = orig[0] if orig else col

        # header color from normal map
        color = color_map.get(orig_key, "#FFFFFF")
        text_color = get_contrast_color(color)

        header_html += (
            f'<th style="background-color:{color};color:{text_color};'
            f'padding:6px;text-align:center;">{col}</th>'
        )
    header_html += "</tr>"

    # ----- Body -----
    body_html = ""
    for r_idx, row in df_display.iterrows():
        body_html += "<tr>"
        for c_idx, (col, val) in enumerate(row.items()):
            # per-cell color override (if provided)
            cell_color = None
            if cell_color_map and r_idx in cell_color_map and col in cell_color_map[r_idx]:
                cell_color = cell_color_map[r_idx][col]

            bg = cell_color if cell_color else "#FFFFFF"

                        # Format cell text with + sign and arrow
            if pd.isna(val):
                cell_text = "No Data"
            else:
                sign_val = f"+{val:.3f}"  # + for positive, - for negative

                if val > 0:
                    arrow = "↑"
                elif val < 0:
                    arrow = "↓"
                else:
                    arrow = ""

                cell_text = f"{sign_val} {arrow}".strip()


            body_html += (
                f"<td style='text-align:center;padding:4px;border:1px solid #ccc;"
                f"background-color:{bg};'>{cell_text}</td>"
            )
        body_html += "</tr>"

    table_html = f"<table style='border-collapse:collapse;width:100%;border:1px solid black;'>{header_html}{body_html}</table>"
    st.markdown(table_html, unsafe_allow_html=True)


# ------------------------------
# Beautiful, functional arrows (fixed)
# ------------------------------
def weaponized_arrows_of_truth(metrics, y1_values, y2_values):
    annotations = []

    for i, metric in enumerate(metrics):
        metric_name = pretty[metric]

        v1 = y1_values.get(metric, np.nan)
        v2 = y2_values.get(metric, np.nan)

        if pd.isna(v1) or pd.isna(v2) or float(v1) == float(v2):
            continue

        v1 = float(v1)
        v2 = float(v2)

        diff = v2 - v1
        diff_text = f"{diff:+.3f} ↑" if diff > 0 else f"{diff:+.3f} ↓"

        color = "red" if diff > 0 else "lime"

    
        # Move label slightly to the right of the bar by adjusting x with "xref='x domain'"
        annotations.append(dict(
            x=i - 0.1 - 0.15 if diff > 0 else i + 0.1 + 0.15,       # shift right relative to bar position
            y=(v1 + v2)/2 + 0.02,    # vertically centered along arrow
            xref="x",          # normal category axis
            yref="y",
            text=f"<b>{diff_text}</b>",
            showarrow=False,
            font=dict(color=color, size=12),
        ))

        # Actual arrow
        annotations.append(dict(
            x=i - 0.1 if diff > 0 else i + 0.1,
            y=v2,
            ax=i - 0.1 if diff > 0 else i + 0.1,
            ay=v1,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor=color,
            opacity=0.95
        ))

    return annotations
    
# ------------------------------
# Updated plot function (horizontal bars with correctly-directed arrows)
# ------------------------------
def plot_year_comparison_with_arrows(y1_values, y2_values, label1, label2, metrics, location1_name):
    vals1 = [np.nan if pd.isna(y1_values.get(m)) else float(y1_values.get(m)) for m in metrics]
    vals2 = [np.nan if pd.isna(y2_values.get(m)) else float(y2_values.get(m)) for m in metrics]

    metric_names = [pretty[m] for m in metrics]
    colors1 = [dataset_year1_rainbows[m] for m in metrics]
    colors2 = [dataset_year2_rainbows[m] for m in metrics]

    fig = go.Figure()

    # YEAR 1 (vertical bars)
    fig.add_trace(go.Bar(
        x=metric_names,
        y=vals1,
        name=label1,
        marker_color=colors1,
        text=[f"{location1_name}<br>{label1}<br>{v:.3f}" if not pd.isna(v) else "No Data" for v in vals1],
        textposition="inside",
        insidetextanchor="middle",
        showlegend=False,
        textangle=0

    ))

    # YEAR 2 (vertical bars)
    fig.add_trace(go.Bar(
        x=metric_names,
        y=vals2,
        name=label2,
        marker_color=colors2,
        text=[f"{location1_name}<br>{label2}<br>{v:.3f}" if not pd.isna(v) else "No Data" for v in vals2],
        textposition="inside",
        insidetextanchor="middle",
        showlegend=False,
        textangle=0

    ))

    fig.update_layout(
        barmode="group",
        title=f"EJI Metrics Comparison for {location1_name}: {label1} vs {label2}",
        xaxis=dict(title="Environmental Justice Index Metric"),
        yaxis=dict(range=[0,1], title="Percentile Rank Value"),
        annotations=weaponized_arrows_of_truth(metrics, y1_values, y2_values),
        height=550
    )

    st.plotly_chart(fig, width="stretch")
    
def compute_change_row(y1_values, y2_values, metrics):
    """Returns a dict containing Δ values for each metric."""
    change = {}
    for m in metrics:
        v1 = y1_values.get(m, np.nan)
        v2 = y2_values.get(m, np.nan)
        if pd.isna(v1) or pd.isna(v2):
            change[m] = np.nan
        else:
            change[m] = float(v2) - float(v1)
    return change

# ------------------------------
# Main App Logic
# ------------------------------
st.title("Year-Year Comparison")
st.info(""" **Interpreting the EJI Score:** 
Negative change in EJI values (less than 0) indicate *a decrease in cumulative environmental and social burdens* — generally a good outcome.
Positive change in EJI values (greater than 0) indicate *an increase in cumulative burdens and vulnerabilities* — generally a worse outcome. """)
st.write("Use the dropdowns below to explore data for **New Mexico** or specific **counties**.")
st.info("🔴 Rows highlighted in red represent areas with **Increased Concern/Burden (ΔEJI > 0)**.")
st.info("🟢 Rows highlighted in green represent areas with **Decreased Concern/Burden (ΔEJI ≤ 0)**.")
# Select baseline and comparison year
baseline_year = st.selectbox("Select baseline year:", AVAILABLE_YEARS, index=0)
other_year_options = [y for y in AVAILABLE_YEARS if y != baseline_year]
other_year = st.selectbox("Select comparison year:", other_year_options, index=0)

# Load datasets
try:
    state_df1, county_df1 = load_data_for_year(baseline_year)
    state_df2, county_df2 = load_data_for_year(other_year)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

state_df1.rename(columns=rename_map, inplace=True)
county_df1.rename(columns=rename_map, inplace=True)
state_df2.rename(columns=rename_map, inplace=True)
county_df2.rename(columns=rename_map, inplace=True)

# Make county match
county_df1 = normalize_county_names(county_df1)
county_df2 = normalize_county_names(county_df2)

metrics = BASE_METRICS.copy()
for m in OPTIONAL_METRICS:
    if m in county_df1.columns and m in county_df2.columns:
        metrics.append(m)

counties = sorted(county_df1["County"].dropna().unique())
states = sorted(state_df1["State"].dropna().unique())

selected_parameter = st.selectbox("View EJI data for:", ["New Mexico", "County"])

if selected_parameter=="County":
    selected_county = st.selectbox("Select a New Mexico County:", counties)
    subset1 = county_df1[county_df1["County"]==selected_county]
    subset2 = county_df2[county_df2["County"]==selected_county]
    if subset1.empty or subset2.empty:
        st.warning(f"No data for {selected_county} in one of the years")
    else:
        
        y1_values = subset1[metrics].iloc[0]
        y2_values = subset2[metrics].iloc[0]
        location1_name = selected_county
        # ---------------- Table ----------------
        # Build table with first column = location name, rows = years
        table_df = pd.DataFrame(
            data=[
                [baseline_year] + [y1_values[m] for m in metrics],
                [other_year] + [y2_values[m] for m in metrics]
            ],
            columns=[location1_name] + metrics
        )
        
        st.markdown(f"### {location1_name} – Year Comparison Table")
        
        # Build a color map including first column (default white)
        full_color_map = {location1_name: "#FFFFFF"}  # first column
        full_color_map.update(dataset_year1_rainbows)  # metrics
        
        # Build a pretty map including first column
        full_pretty_map = {location1_name: location1_name, **pretty}
        
        display_colored_table_html(
            table_df,
            color_map=full_color_map,
            pretty_map=full_pretty_map
        )

        plot_year_comparison_with_arrows(y1_values, y2_values, baseline_year, other_year, metrics, location1_name)
        # ---------------- Change Table ----------------
        change_values = compute_change_row(y1_values, y2_values, metrics)
        
        change_df = pd.DataFrame(
            data=[[change_values[m] for m in metrics]],
            columns=metrics
        )
        
        st.markdown(f"### Change from {baseline_year} to {other_year}")
        
        # Column headers = rainbow colors (dataset_year1)
        change_header_colors = {m: dataset_year1_rainbows[m] for m in metrics}
        
        # Pretty names
        change_pretty = {m: f"Δ {pretty[m]}" for m in metrics}
        
        # Cell background colors (increase = red, decrease = green)
        cell_colors = {
            0: {  # row index 0
                f"Δ {pretty[m]}": ("#ffcccc" if change_values[m] > 0 else "#ccffcc")
                for m in metrics
            }
        }
        
        # Build a df with pretty column names
        change_df_pretty = change_df.rename(columns=change_pretty)
        
        # Call updated table renderer
        display_colored_table_html(
            change_df_pretty,
            color_map=change_header_colors,     # rainbow headers
            pretty_map=change_pretty,           # pretty labels
            cell_color_map=cell_colors          # the DELTA box colors
        )


else:
    nm_row1 = state_df1[state_df1["State"].str.strip().str.lower()=="new mexico"]
    nm_row2 = state_df2[state_df2["State"].str.strip().str.lower()=="new mexico"]
    if nm_row1.empty or nm_row2.empty:
        st.warning("No New Mexico data found")
    else:
        y1_values = nm_row1[metrics].iloc[0]
        y2_values = nm_row2[metrics].iloc[0]
        location1_name = "New Mexico"
        # ---------------- Table ----------------
        # Build table with first column = location name, rows = years
        table_df = pd.DataFrame(
            data=[
                [baseline_year] + [y1_values[m] for m in metrics],
                [other_year] + [y2_values[m] for m in metrics]
            ],
            columns=[location1_name] + metrics
        )
        
        st.markdown(f"### {location1_name} – Year Comparison Table")
        
        # Build a color map including first column (default white)
        full_color_map = {location1_name: "#FFFFFF"}  # first column
        full_color_map.update(dataset_year1_rainbows)  # metrics
        
        # Build a pretty map including first column
        full_pretty_map = {location1_name: location1_name, **pretty}
        
        display_colored_table_html(
            table_df,
            color_map=full_color_map,
            pretty_map=full_pretty_map
        )

        plot_year_comparison_with_arrows(y1_values, y2_values, baseline_year, other_year, metrics, location1_name)
       # ---------------- Change Table ----------------
        change_values = compute_change_row(y1_values, y2_values, metrics)
        
        change_df = pd.DataFrame(
            data=[[change_values[m] for m in metrics]],
            columns=metrics
        )
        
        st.markdown(f"### Change from {baseline_year} to {other_year}")
        
        # Column headers = rainbow colors (dataset_year1)
        change_header_colors = {m: dataset_year1_rainbows[m] for m in metrics}
        
        # Pretty names
        change_pretty = {m: f"Δ {pretty[m]}" for m in metrics}
        
        # Cell background colors (increase = red, decrease = green)
        cell_colors = {
            0: {  # row index 0
                f"Δ {pretty[m]}": ("#ffcccc" if change_values[m] > 0 else "#ccffcc")
                for m in metrics
            }
        }
        
        # Build a df with pretty column names
        change_df_pretty = change_df.rename(columns=change_pretty)
        
        # Call updated table renderer
        display_colored_table_html(
            change_df_pretty,
            color_map=change_header_colors,     # rainbow headers
            pretty_map=change_pretty,           # pretty labels
            cell_color_map=cell_colors          # the DELTA box colors
        )

st.divider()
st.caption("Data Source: CDC Environmental Justice Index | Visualization by Riley Cochrell")
