import streamlit as st

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
/* Target the logo spacer div container */
div[data-testid="stLogoSpacer"] {
    display: flex;
    flex-direction: column; /* Stack the before and after elements vertically */
    justify-content: center; /* Center vertically */
    align-items: center; /* Center horizontally */
    height: 100%;
    padding-top: 40px; /* Add some padding to move it down slightly */
}

/* ::before for the top line (TEAM 23:) */
div[data-testid="stLogoSpacer"]::before {
    content: "TEAM 23:";
    font-size: 30px; /* Larger font size */
    font-weight: bold;
    white-space: nowrap;
    margin-bottom: 5px; /* Space between lines */
}

/* ::after for the bottom line (🌎 Environmental Justice in New Mexico) */
div[data-testid="stLogoSpacer"]::after {
    content: "🌎 Environmental Justice in New Mexico";
    text-align: center;
    font-size: 18px; /* Smaller font size */
    font-weight: bold;
    margin-bottom: -40px;
}

</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------
# Custom Sidebar
# ------------------------------
with st.sidebar:
    # Add a horizontal rule for visual separation below the logo spot
    st.write("---") 

    # Custom manual navigation
    st.page_link("streamlit_app.py",
                 label="EJI Visualization",
                 icon="📊")

    st.page_link("pages/1_What_Goes_Into_EJI.py",
                 label="What Goes Into the EJI?",
                 icon="🧩")

    st.page_link("pages/2_EJI_Scale_and_Categories.py",
                 label="What Does the EJI Mean?",
                 icon="🌡️")
st.title("🧩 What Goes Into the Environmental Justice Index (EJI)?")

st.write("""
The **Environmental Justice Index (EJI)** is composed of multiple indicators that measure **social vulnerability**, 
**environmental burden**, and **health vulnerability** across U.S. communities.  

This diagram, developed by the **CDC and ATSDR**, illustrates how these indicators are grouped into domains 
and modules to calculate the overall Environmental Justice score.
""")

st.image("pictures/EJIofficialMarkers.png", width='stretch', caption="Source: CDC Environmental Justice Index")
