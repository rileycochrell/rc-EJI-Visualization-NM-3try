import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(
    page_title="TEAM 23: Environmental Justice in New Mexico — 📊 EJI Visualization",
    page_icon="🌎",
    layout="wide"
)

# ------------------------------
# Hide Streamlit's Auto Navigation and Add Custom Title in Logo Spot
# ------------------------------
st.markdown('<style>div[data-testid="stSidebarNav"] {display: none;}</style>', unsafe_allow_html=True)
st.markdown(
    """
<style>
div[data-testid="stLogoSpacer"] {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    padding-top: 40px;
}
div[data-testid="stLogoSpacer"]::before {
    content: "TEAM 23:";
    font-size: 30px;
    font-weight: bold;
    white-space: nowrap;
    margin-bottom: 5px;
}
div[data-testid="stLogoSpacer"]::after {
    content: "🌎 Environmental Justice in New Mexico";
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: -40px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------
# Sidebar Navigation
# ------------------------------
with st.sidebar:
    st.write("---")
    st.page_link("streamlit_app.py", label="EJI Visualization", icon="📊")
    st.page_link("pages/3_change_over_years_and_comparison.py", label="EJI Metrics Comparison", icon="📈")
    st.page_link("pages/2_EJI_Scale_and_Categories.py", label="What Does the EJI Mean?", icon="🌡️")
    st.page_link("pages/1_What_Goes_Into_EJI.py", label="What Goes Into the EJI?", icon="🧩")

# ------------------------------
# Year selection and data loading
# ------------------------------
AVAILABLE_YEARS = ["2024", "2022"]  # add more later as you add files

@st.cache_data
def load_data_for_year(year: str):
    """Load the state and county CSVs for the given year.
       NOTE: GitHub repo path updated from ...-2try -> ...-3try per your request.
    """
    base = "https://github.com/rileycochrell/rc-EJI-Visualization-NM-3try/raw/refs/heads/main/data"
    # default paths (must exist in your repo)
    state_path = f"{base}/{year}/clean/{year}EJI_StateAverages_RPL.csv"
    county_path = f"{base}/{year}/clean/{year}EJI_NewMexico_CountyMeans.csv"
    tract_path = f"{base}/{year}/raw/{year}EJI_NM_TRACTS.csv"
    
    state_df = pd.read_csv(state_path)
    county_df = pd.read_csv(county_path)
    tract_df = pd.read_csv(tract_path, dtype={'GEOID': str, 'TRACT_FIPS': str})
    
    return state_df, county_df, tract_df

# ------------------------------
# Normalize column names (rename mean_* to RPL_*)
# ------------------------------
rename_map = {
    "Mean_EJI": "RPL_EJI",
    "Mean_EBM": "RPL_EBM",
    "Mean_SVM": "RPL_SVM",
    "Mean_HVM": "RPL_HVM",
    "Mean_CBM": "RPL_CBM",
    "Mean_EJI_CBM": "RPL_EJI_CBM"
}


# Determine available metrics based on loaded data (so 2022 can lack CBM/EJI_CBM)
BASE_METRICS = ["RPL_EJI", "RPL_EBM", "RPL_SVM", "RPL_HVM"]
OPTIONAL_METRICS = ["RPL_CBM", "RPL_EJI_CBM"]  # added in 2024; absent in 2022

# Pretty names
pretty = {
    "RPL_EJI": "Overall EJI",
    "RPL_EBM": "Environmental Burden",
    "RPL_SVM": "Social Vulnerability",
    "RPL_HVM": "Health Vulnerability",
    "RPL_CBM": "Climate Burden",
    "RPL_EJI_CBM": "EJI + Climate Burden"
}

# Colors for bars (long lists must match possible metrics)
dataset1_rainbows = {
    "RPL_EJI": "#911eb4",
    "RPL_EBM": "#c55c29",
    "RPL_SVM": "#4363d8",
    "RPL_HVM": "#f032e6",
    "RPL_CBM": "#469990",
    "RPL_EJI_CBM": "#801650"
}
dataset2_rainbows = {
    "RPL_EJI": "#b88be1",
    "RPL_EBM": "#D2B48C",
    "RPL_SVM": "#87a1e5",
    "RPL_HVM": "#f79be9",
    "RPL_CBM": "#94c9c4",
    "RPL_EJI_CBM": "#f17cb0"
}


# ------------------------------
# Helper functions
# ------------------------------
def get_contrast_color(hex_color: str):
    """Return 'black' or 'white' for readable text on hex_color background."""
    try:
        rgb = tuple(int(hex_color.strip("#")[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return "black"
    brightness = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])
    return "black" if brightness > 150 else "white"

# Lock "No Data" label font color to black because app theme is locked to light
def no_data_label_color():
    return "black"
def normalize_county_names(df):
    if "County" in df.columns:
        df["County"] = df["County"].astype(str).str.strip().str.title()
        df["County"] = df["County"].apply(
            lambda x: f"{x} County" if not x.lower().endswith("county") else x)
        return df
def display_colored_table_html(df, color_map, pretty_map, title=None):
    """Render an HTML table with header cell colors from color_map and data cells.
       Currently highlights entire row if any cell >= 0.76; if you want per-cell highlighting,
       I can change that easily.
    """
    if isinstance(df, pd.Series):
        df = df.to_frame().T
    df_display = df.rename(columns=pretty_map)
    if title:
        st.markdown(f"### {title}")

    header_html = "<tr>"
    for col in df_display.columns:
        # find original metric key for this pretty column (if present)
        orig_keys = [k for k, v in pretty_map.items() if v == col]
        color = color_map.get(orig_keys[0], "#FFFFFF") if orig_keys else "#FFFFFF"
        text_color = get_contrast_color(color)
        header_html += f'<th style="background-color:{color};color:{text_color};padding:6px;text-align:center;">{col}</th>'
    header_html += "</tr>"

    body_html = ""
    for _, row in df_display.iterrows():
        # if any numeric cell >= 0.76 (Very High), highlight whole row (existing behavior)
        # ----- Per-cell highlighting instead of whole row -----
        body_html += "<tr>"
        for val in row:
            if pd.isna(val):
                cell_text = "No Data"
                bg = "white"
            else:
                cell_text = f"{val:.3f}" if isinstance(val, float) else val
                # highlight only this cell if >= 0.76
                bg = "#ffb3b3" if (isinstance(val, (int, float)) and val >= 0.76) else "white"
        
            body_html += (
                f"<td style='text-align:center;padding:4px;border:1px solid #ccc;"
                f"background-color:{bg};'>{cell_text}</td>"
            )
        
        body_html += "</tr>"


    table_html = f"<table style='border-collapse:collapse;width:100%;border:1px solid black;'>{header_html}{body_html}</table>"
    st.markdown(table_html, unsafe_allow_html=True)

# ------------------------------
# Plot utilities
# ------------------------------
NO_DATA_HEIGHT = 0.5
NO_DATA_PATTERN = dict(shape="/", fgcolor="black", bgcolor="white", size=6)

def build_customdata(area_label, values):
    out = []
    for v in values:
        if pd.isna(v):
            out.append([area_label, "No Data"])
        else:
            out.append([area_label, f"{v:.3f}"])
    return out

def build_texts_and_colors(colors_map, area_label, values):
    texts = []
    fonts = []
    for metric_key, v in zip(metrics, values):
        c = colors_map.get(metric_key, "#FFFFFF")
        if pd.isna(v):
            # label shown on the no-data overlay; font chosen so it is visible in light theme
            texts.append("No Data")
            fonts.append(no_data_label_color())
        else:
            val_str = f"{v:.3f}"
            texts.append(f"{area_label}<br>{val_str}" if area_label else f"{val_str}")
            fonts.append(get_contrast_color(c))
    return texts, fonts

# ------------------------------
# Graph functions
# ------------------------------
def plot_single_chart(title, data_values, area_label=None):
    # data_values: pandas Series containing metric values (may have NaNs)
    vals = np.array([np.nan if pd.isna(v) else float(v) for v in data_values.loc[metrics].values])
    # colors list aligned with metrics
    color_list = [dataset1_rainbows.get(m, "#888888") for m in metrics]

    has_y = [v if not pd.isna(v) else 0 for v in vals]
    nodata_y = [NO_DATA_HEIGHT if pd.isna(v) else 0 for v in vals]

    texts, fonts = build_texts_and_colors(dataset1_rainbows, area_label, vals)
    customdata = build_customdata(area_label, vals)

    fig = go.Figure()

    # Real data bars
    fig.add_trace(go.Bar(
        x=[pretty[m] for m in metrics],
        y=has_y,
        marker_color=color_list,
        text=texts,
        texttemplate="%{text}",
        textposition="inside",
        textfont=dict(size=10, color=fonts),
        customdata=customdata,
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        showlegend=False
    ))

    # No data overlay bars (patterned thin bar) with outside label "Location<br>No Data"
    nodata_text = [f"{area_label}<br>No Data" if pd.isna(v) else "" for v in vals]
    fig.add_trace(go.Bar(
        x=[pretty[m] for m in metrics],
        y=nodata_y,
        marker=dict(color="white", pattern=NO_DATA_PATTERN),
        text=nodata_text,
        texttemplate="%{text}",
        textposition="outside",
        textfont=dict(size=10, color=no_data_label_color()),
        customdata=customdata,
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        name="No Data"
    ))

    fig.update_layout(
        title=title,
        yaxis=dict(title="Percentile Rank Value", range=[0, 1], dtick=0.25),
        xaxis_title="Environmental Justice Index Metric",
        barmode="overlay",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        template="plotly_white"
    )

    st.plotly_chart(fig, width='stretch')

def plot_comparison(data1, data2, label1, label2):
    # Both data1 and data2: pandas Series (metric values). We show grouped bars.
    vals1 = np.array([np.nan if pd.isna(v) else float(v) for v in data1.loc[metrics].values])
    vals2 = np.array([np.nan if pd.isna(v) else float(v) for v in data2.loc[metrics].values])

    metric_names = [pretty[m] for m in metrics]
    colors1 = [dataset1_rainbows.get(m, "#888888") for m in metrics]
    colors2 = [dataset2_rainbows.get(m, "#cccccc") for m in metrics]

    has1_y = [v if not pd.isna(v) else 0 for v in vals1]
    nodata1_y = [NO_DATA_HEIGHT if pd.isna(v) else 0 for v in vals1]
    has2_y = [v if not pd.isna(v) else 0 for v in vals2]
    nodata2_y = [NO_DATA_HEIGHT if pd.isna(v) else 0 for v in vals2]

    texts1, fonts1 = build_texts_and_colors(dataset1_rainbows, label1, vals1)
    texts2, fonts2 = build_texts_and_colors(dataset2_rainbows, label2, vals2)

    wingardium_leviOsa = build_customdata(label1, vals1)
    wingardium_leviosAH = build_customdata(label2, vals2)

    fig = go.Figure()

    # Dataset 1 real
    fig.add_trace(go.Bar(
        x=metric_names,
        y=has1_y,
        marker_color=colors1,
        offsetgroup=0,
        width=0.35,
        text=texts1,
        texttemplate="%{text}",
        textposition="inside",
        textfont=dict(size=10, color=fonts1),
        customdata=wingardium_leviOsa,
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        name=label1,
        showlegend=False
    ))

    # Dataset 1 no-data overlay
    fig.add_trace(go.Bar(
        x=metric_names,
        y=nodata1_y,
        marker=dict(color="white", pattern=NO_DATA_PATTERN),
        offsetgroup=0,
        width=0.35,
        text=[f"{label1}<br>No Data" if pd.isna(v) else "" for v in vals1],
        texttemplate="%{text}",
        textposition="outside",
        textfont=dict(size=10, color=no_data_label_color()),
        customdata=wingardium_leviOsa,
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        showlegend=False
    ))

    # Dataset 2 real
    fig.add_trace(go.Bar(
        x=metric_names,
        y=has2_y,
        marker_color=colors2,
        offsetgroup=1,
        width=0.35,
        text=texts2,
        texttemplate="%{text}",
        textposition="inside",
        textfont=dict(size=10, color=fonts2),
        customdata=wingardium_leviosAH,
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        name=label2,
        showlegend=False
    ))

    # Dataset 2 no-data overlay
    fig.add_trace(go.Bar(
        x=metric_names,
        y=nodata2_y,
        marker=dict(color="white", pattern=NO_DATA_PATTERN),
        offsetgroup=1,
        width=0.35,
        text=[f"{label2}<br>No Data" if pd.isna(v) else "" for v in vals2],
        texttemplate="%{text}",
        textposition="outside",
        textfont=dict(size=10, color=no_data_label_color()),
        customdata=wingardium_leviosAH,
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        showlegend=False
    ))

    # Add legend entry for No Data pattern
    fig.add_trace(go.Bar(x=[None], y=[None], marker=dict(color="white", pattern=NO_DATA_PATTERN), name="No Data"))

    # Comparison table for display
    compare_table = pd.DataFrame({
        "Metric": [pretty[m] for m in metrics],
        label1: data1.loc[metrics].values,
        label2: data2.loc[metrics].values
    }).set_index("Metric").T

    st.subheader("⚖️ Data Comparison Table")
    display_colored_table_html(compare_table.reset_index(), dataset1_rainbows, {"index": "Metric", **pretty}, title=None)

    fig.update_layout(
        barmode="group",
        title=f"EJI Metric Comparison — {label1} vs {label2}",
        yaxis=dict(title="Percentile Rank Value", range=[0, 1], dtick=0.25),
        xaxis_title="Environmental Justice Index Metric",
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        template="plotly_white"
    )

    st.plotly_chart(fig, width='stretch')
    st.caption("_Note: darker bars represent the first dataset; lighter bars represent the second dataset._")
def run_test(df, group_column, target_column, threshold=0.75):
    """Classifies tracts based on the Socioeconomic Vulnerability and performs T-test."""
    df = df[df[target_column] >= 0]
    df['Is_Low_Income_Tract'] = np.where(
        df[group_column] >= threshold,
        'Low-Income (High Burden)',
        'Other Tracts (Lower Burden)'
    )

    low_income_ej = df[df['Is_Low_Income_Tract'] == 'Low-Income (High Burden)'][target_column].dropna()
    other_ej = df[df['Is_Low_Income_Tract'] == 'Other Tracts (Lower Burden)'][target_column].dropna()

    if low_income_ej.empty or other_ej.empty:
        return None, None, None, None, df

    t_stat, p_value = stats.ttest_ind(low_income_ej, other_ej, equal_var=False)
    return low_income_ej.mean(), other_ej.mean(), t_stat, p_value, df

# ------------------------------
# Main App Layout
# ------------------------------
st.title("📊 Environmental Justice Index Visualization (New Mexico)")
st.info("""
**Interpreting the EJI Score:**  
Lower EJI values (closer to 0) indicate *lower cumulative environmental and social burdens* — generally a good outcome.  
Higher EJI values (closer to 1) indicate *higher cumulative burdens and vulnerabilities* — generally a worse outcome.
""")
st.write("Use the dropdowns below to explore data for **New Mexico** or specific **counties**, or view the final **Test** results.")
st.info("🔴 Cells highlighted in red represent areas with **Very High Concern/Burden (EJI ≥ 0.76)**.")
# ------------------------------
# Move Year Selection Here
# ------------------------------
selected_year = st.selectbox("Select data year:", AVAILABLE_YEARS, index=0)

# ------------------------------
# Normalize County Names
# ------------------------------
def normalize_county_names(df):
    if "County" in df.columns:
        df["County"] = df["County"].astype(str).str.strip().str.title()
        df["County"] = df["County"].apply(
            lambda x: f"{x} County" if not x.lower().endswith("county") else x
        )
    return df

# ------------------------------
# Normalize County Names
# ------------------------------
def normalize_county_names(df):
    if "County" in df.columns:
        df["County"] = df["County"].astype(str).str.strip().str.title()
        df["County"] = df["County"].apply(
            lambda x: f"{x} County" if not x.lower().endswith("county") else x
        )
    return df

# ------------------------------
# Load and normalize data
# ------------------------------
try:
    state_df, county_df, tract_df = load_data_for_year(selected_year)
except Exception as e:
    st.error(f"Error loading data for {selected_year}: {e}")
    st.stop()

state_df.rename(columns=rename_map, inplace=True)
county_df.rename(columns=rename_map, inplace=True)


# Normalize county names

if 'RPL_EJI' not in tract_df.columns:
    tract_df.rename(columns={
        "RPL_THEME_EJI": "RPL_EJI",
        "RPL_THEME_EBM": "RPL_EBM",
        "RPL_THEME_SVM": "RPL_SVM",
        "RPL_THEME_HVM": "RPL_HVM",
        "RPL_THEME_CBM": "RPL_CBM",
        "RPL_THEME_EJI_CBM": "RPL_EJI_CBM",
    }, inplace=True)
county_df = normalize_county_names(county_df)

metrics = BASE_METRICS.copy()
for m in OPTIONAL_METRICS:
    if m in county_df.columns:
        metrics.append(m)

counties = sorted(county_df["County"].dropna().unique())
states = sorted(state_df["State"].dropna().unique())

parameter1 = ["New Mexico", "County", "Test"]

st.caption("Note: If a state or county does not appear in the dropdown, it means the CDC dataset for the selected year did not include data for that location.")

selected_parameter = st.selectbox("View EJI data for:", parameter1)

if selected_parameter == "County":
    selected_county = st.selectbox("Select a New Mexico County:", counties)
    st.caption("Note: If a state or county does not appear in the dropdown, it means the CDC dataset for the selected year did not include data for that location.")
    subset = county_df[county_df["County"] == selected_county]
    if subset.empty:
        st.warning(f"No data found for {selected_county}.")
    else:
        st.subheader(f"⚖️ EJI Data for {selected_county} — {selected_year}")
        display_colored_table_html(subset, dataset1_rainbows, pretty)
        county_values = subset.iloc[0]  # series with columns (we'll refer to metrics)
        plot_single_chart(f"EJI Metrics — {selected_county} ({selected_year})", county_values, area_label=selected_county)

        if st.checkbox("Compare with another dataset"):
            compare_type = st.radio("Compare with:", ["State", "County"])
            if compare_type == "State":
                comp_state = st.selectbox("Select state:", states)
                st.caption("Note: If a state or county does not appear in the dropdown, it means the CDC dataset for the selected year did not include data for that location.")

                comp_row = state_df[state_df["State"] == comp_state]
                if not comp_row.empty:
                    comp_values = comp_row.iloc[0]
                    plot_comparison(county_values, comp_values, selected_county, comp_state)
            else:
                comp_county = st.selectbox("Select county:", [c for c in counties if c != selected_county])
                st.caption("Note: If a state or county does not appear in the dropdown, it means the CDC dataset for the selected year did not include data for that location.")
                comp_row = county_df[county_df["County"] == comp_county]
                if not comp_row.empty:
                    comp_values = comp_row.iloc[0]
                    plot_comparison(county_values, comp_values, selected_county, comp_county)

elif selected_parameter == "New Mexico":
    nm_row = state_df[state_df["State"].str.strip().str.lower() == "new mexico"]
    if nm_row.empty:
        st.warning("No New Mexico data found.")
    else:
        st.subheader(f"⚖️ New Mexico Statewide EJI Scores — {selected_year}")
        display_colored_table_html(nm_row, dataset1_rainbows, pretty)
        nm_values = nm_row.iloc[0]
        plot_single_chart(f"EJI Metrics — New Mexico ({selected_year})", nm_values, area_label="New Mexico")

        if st.checkbox("Compare with another dataset"):
            compare_type = st.radio("Compare with:", ["State", "County"])
            if compare_type == "State":
                comp_state = st.selectbox("Select state:", [s for s in states if s.lower() != "new mexico"])
                st.caption("Note: If a state or county does not appear in the dropdown, it means the CDC dataset for the selected year did not include data for that location.")
                comp_row = state_df[state_df["State"] == comp_state]
                if not comp_row.empty:
                    comp_values = comp_row.iloc[0]
                    plot_comparison(nm_values, comp_values, "New Mexico", comp_state)
            else:
                comp_county = st.selectbox("Select county:", counties)
                st.caption("Note: If a state or county does not appear in the dropdown, it means the CDC dataset for the selected year did not include data for that location.")
                comp_row = county_df[county_df["County"] == comp_county]
                if not comp_row.empty:
                    comp_values = comp_row.iloc[0]
                    plot_comparison(nm_values, comp_values, "New Mexico", comp_county)
else:
    st.subheader("🔬 Statistical Test: Low-Income vs. Other Tracts")
    st.markdown("""
        **Assumption:** Census Tracts with high **Social Vulnerability**
        (our proxy for low-income, defined as ≥ 0.75 nationally) will have a
        significantly higher **Overall EJI score**.
    """)

    mean_low_income, mean_other, t_stat, p_value, _ = run_test(
        tract_df.copy(),
        'RPL_SVM',
        'RPL_EJI',
        0.75
    )

    if mean_low_income is not None:
        col_mean, col_t = st.columns(2)
        with col_mean:
            st.metric(
                "Mean Overall EJI (Low-Income Tracts)",
                f"{mean_low_income:.3f}",
                delta=f"{(mean_low_income - mean_other):.3f} higher than other tracts"
            )
            st.metric(
                "Mean Overall EJI (Other Tracts)",
                f"{mean_other:.3f}"
            )

        with col_t:
            st.metric("T-Statistic", f"{t_stat:.2f}",  help="Measures the magnitude of difference between the groups' means.")
            st.metric("P-Value", f"{p_value:.4e}",  help="P-value < 0.05 indicates the difference is statistically significant.")

        st.write("---")
        if p_value < 0.05:
            st.success(f"**Conclusion:** The difference **is statistically significant** (p < 0.05). This confirms that socially vulnerable communities in NM face disproportionately higher environmental burdens.")
        else:
            st.warning(f"**Conclusion:** The difference is **not** statistically significant (p = {p_value:.4f}).")

    else:
        st.error(f"Cannot run test. Check your Census Tract data file for 'RPL_SVM' and 'RPL_EJI' columns.")

st.divider()
st.caption("Data Source: CDC Environmental Justice Index | Visualization by Riley Cochrell")
