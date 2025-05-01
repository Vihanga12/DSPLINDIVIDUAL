# --- START OF FILE app.py ---

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os

# --- Function to encode image to Base64 ---
def get_base64_of_bin_file(bin_file):
    # Read binary file and return base64 encoded string
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        st.error(f"Error: Image file not found at {bin_file}")
        return None
    except Exception as e:
        st.error(f"Error reading image file {bin_file}: {e}")
        return None

# --- Function to inject background CSS ---
def set_page_background_and_styles(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    if bin_str is None: # Exit if image loading failed
        return

    # Define CSS styles with improved visibility
    page_bg_img = f'''
    <style>
    /* === Page Background === */
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* === Semi-transparent Black Background for Content Blocks === */
    /* Apply to direct child vertical blocks within the main container's block-container */
    .main .block-container > [data-testid="stVerticalBlock"] {{
         /* INCREASED OPACITY HERE */
         background-color: rgba(0, 0, 0, 0.85) !important; /* Darker background */
         padding: 1.2rem; /* Slightly more padding */
         border-radius: 0.5rem;
         margin-bottom: 1.5rem; /* More space between blocks */
         border: 1px solid rgba(255, 255, 255, 0.1) !important; /* Lighter border, less distracting */
         box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4); /* Add subtle shadow to blocks */
    }}
    /* Specific styling for the KPI container if needed */
    .main .block-container > [data-testid="stVerticalBlock"] > div:has(> [data-testid="stMetric"]) {{
        padding-top: 1.5rem; /* More padding above KPIs */
        /* Background handled above */
    }}


    /* === General Text Color (White) and Shadow === */
    /* Target common text elements within the main area's styled blocks */
     .main .block-container > [data-testid="stVerticalBlock"] h1,
     .main .block-container > [data-testid="stVerticalBlock"] h2,
     .main .block-container > [data-testid="stVerticalBlock"] h3,
     .main .block-container > [data-testid="stVerticalBlock"] h4,
     .main .block-container > [data-testid="stVerticalBlock"] h5,
     .main .block-container > [data-testid="stVerticalBlock"] h6,
     .main .block-container > [data-testid="stVerticalBlock"] p,
     .main .block-container > [data-testid="stVerticalBlock"] li,
     .main .block-container > [data-testid="stVerticalBlock"] .stMarkdown,
     .main .block-container > [data-testid="stVerticalBlock"] .stMetricLabel,
     .main .block-container > [data-testid="stVerticalBlock"] .stMetricValue,
     .main .block-container > [data-testid="stVerticalBlock"] .stCaption,
     .main .block-container > [data-testid="stVerticalBlock"] label,
     /* Expander summary text */
     .st-expander > summary,
     /* Text inside dataframe */
     [data-testid="stDataFrame"] table tbody tr td,
     [data-testid="stDataFrame"] table thead tr th,
     /* Text inside alerts */
     [data-testid="stAlert"] div[role="alert"]
     {{
        color: white !important;
        /* SIMPLIFIED TEXT SHADOW */
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7) !important;
    }}
    /* Make title extra prominent */
    .main .block-container > [data-testid="stVerticalBlock"] h1 {{
        font-size: 2.5em;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8) !important;
        margin-top: 0;
        margin-bottom: 0.75rem;
    }}
     .main .block-container > [data-testid="stVerticalBlock"] h2 {{
        margin-bottom: 0.6rem;
     }}
     .main .block-container > [data-testid="stVerticalBlock"] h3 {{
        margin-bottom: 0.5rem;
     }}

    /* === Dataframe Styling === */
    [data-testid="stDataFrame"] {{
        background-color: transparent !important;
        padding: 0;
        border: none !important;
        margin-top: 0.5rem;
    }}
    [data-testid="stDataFrame"] > div {{
        border: none !important;
        background-color: transparent !important;
     }}
     /* Cells already covered by general text rule */
     /* [data-testid="stDataFrame"] table tbody tr td, */
     /* [data-testid="stDataFrame"] table thead tr th {{ ... }} */
     [data-testid="stDataFrame"] table thead tr th {{
         /* Slightly more opaque header for better separation */
         background-color: rgba(255, 255, 255, 0.15) !important;
         font-weight: bold;
         border-bottom-width: 2px !important;
         border-bottom-color: rgba(255, 255, 255, 0.4) !important; /* More visible line */
     }}
     /* Ensure row lines are subtle */
     [data-testid="stDataFrame"] table tbody tr td {{
        border-bottom-color: rgba(255, 255, 255, 0.2) !important;
        border-right: none !important;
        border-left: none !important;
        padding: 0.6rem 0.5rem; /* Adjust cell padding */
     }}

    /* === Expander Styling === */
    .main .block-container [data-testid="stExpander"] {{
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 0.5rem;
        border-radius: 0 !important;
    }}
    .st-expander > summary {{
         background-color: rgba(255, 255, 255, 0.15) !important; /* Slightly more opaque header */
         padding: 0.75rem 1rem !important;
         border-radius: 0.4rem; /* Slightly less round */
         border: 1px solid rgba(255, 255, 255, 0.25) !important; /* More visible border */
         margin-bottom: 0rem;
         /* Text color/shadow handled by general rule */
    }}
    .st-expander > summary:hover {{
         background-color: rgba(255, 255, 255, 0.25) !important;
         border-color: rgba(255, 255, 255, 0.35) !important;
    }}
    .st-expander [data-testid="stVerticalBlock"] {{
         padding: 1rem 0 0 0 !important;
         background-color: transparent !important;
         border: none !important;
         margin-bottom: 0 !important;
         border-radius: 0 !important;
         box-shadow: none !important; /* Remove inner shadow if any */
    }}
    .st-expander > summary svg {{
        fill: white !important;
    }}

    /* === Sidebar Styling === */
    [data-testid="stSidebar"] > div:first-child {{
        background-color: rgba(25, 28, 38, 0.9); /* Darker sidebar */
    }}
    [data-testid="stSidebar"] * {{ /* Ensure all sidebar text is white */
        color: white !important;
    }}
    /* Style multiselect specifically if needed */
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: #ADFF2F !important; color: black !important; border: 1px solid #9ACD32 !important;
    }}
    .stMultiSelect [data-baseweb="tag"]:hover {{
        background-color: #9ACD32 !important; border-color: #6B8E23 !important;
    }}
    .stMultiSelect [data-baseweb="tag"] span[role="button"] svg {{
        fill: black !important;
    }}


    /* === Plotly Chart Styling === */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly svg {{
        background-color: transparent !important;
    }}
    /* Ensure all plot text is white and clear */
    .js-plotly-plot .plotly text {{
        fill: white !important;
        stroke: none !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7) !important; /* Add shadow to plot text */
    }}
    .js-plotly-plot .plotly .legendtext {{
        fill: white !important;
    }}
    /* Make plot axes lines clearer */
    .js-plotly-plot .plotly .shapelayer path, /* Grid lines */
    .js-plotly-plot .plotly .xaxislayer-above path, /* X axis line */
    .js-plotly-plot .plotly .yaxislayer-above path {{ /* Y axis line */
        stroke: rgba(255, 255, 255, 0.5) !important;
        stroke-width: 1px !important;
    }}


    /* === Alert/Status Message Styling === */
    [data-testid="stAlert"] {{
        background-color: rgba(50, 50, 50, 0.85) !important; /* Dark background */
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 0.4rem !important;
        margin-bottom: 1rem; /* Ensure spacing */
        /* Text color is handled by the general rule above */
        color: white !important; /* Explicitly set white text for alerts */
    }}
     /* Style specific alert types if needed (e.g., border color) */
    [data-testid="stAlert"][data-baseweb="notification-positive"] {{ /* Success */
        border-left: 5px solid #2E7D32 !important; /* Green left border */
    }}
     [data-testid="stAlert"][data-baseweb="notification-negative"] {{ /* Error */
        border-left: 5px solid #C62828 !important; /* Red left border */
    }}
     [data-testid="stAlert"][data-baseweb="notification-warning"] {{ /* Warning */
        border-left: 5px solid #FF8F00 !important; /* Orange left border */
    }}
     [data-testid="stAlert"][data-baseweb="notification-info"] {{ /* Info */
        border-left: 5px solid #0277BD !important; /* Blue left border */
    }}

    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# --- Set Background Image ---
# !!! IMPORTANT: Make sure this path is correct for your environment !!!
# Use a relative path if the image is in the same folder as the script, e.g.,
# image_path = "network-3537400_1280 (1)_13.jpg"
# Or provide the full, correct absolute path as below.
image_path = "/Users/vihanga/Downloads/DSPL_Individual_CW/network-3537400_1280 (1)_13.jpg"
set_page_background_and_styles(image_path)
# --- End Background Image ---


# Load and clean data
@st.cache_data
def load_data():
    try:
        # Attempt relative path first (assuming excel file is in the same directory as the script)
        excel_file = "preprocessed_data (76).xlsx"
        if not os.path.exists(excel_file):
             # Fallback to the provided absolute path if relative fails
             excel_file_abs = "/Users/vihanga/Downloads/DSPL_Individual_CW/preprocessed_data (76).xlsx"
             if os.path.exists(excel_file_abs):
                 excel_file = excel_file_abs
                 # Using st.info might be better than success here as it's a fallback
                 st.info(f"Using absolute path for Excel file: {excel_file}")
             else:
                 # If neither path works, raise a clear error
                 raise FileNotFoundError(f"Excel file not found. Checked relative path './{excel_file}' and absolute path '{excel_file_abs}'. Please ensure the file exists and the path is correct.")
        df = pd.read_excel(excel_file)
        # Use st.success for positive confirmation
        st.success(f"Successfully loaded data from: {excel_file}")
    except FileNotFoundError as e:
        st.error(f"Error: {e}")
        st.error(f"Current working directory: {os.getcwd()}") # Show CWD for debugging paths
        return pd.DataFrame() # Return empty DataFrame on file error
    except Exception as e:
        st.error(f"Error loading or parsing Excel file: {e}")
        return pd.DataFrame() # Return empty DataFrame on other loading errors

    # --- Column Cleaning ---
    bandwidth_cols = ["BW Allocated", "May Avg (Mbps)", "May Max (Mbps)", "April Avg (Mbps)", "April Max (Mbps)", "March Avg (Mbps)", "March Max (Mbps)"]
    for col in bandwidth_cols:
        if col in df.columns:
            try:
                # Convert to string first to handle potential mixed types before replacing
                df[col] = df[col].astype(str).str.replace(" Mbps", "", regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce') # Coerce errors to NaN
            except Exception as e:
                st.warning(f"Could not fully clean bandwidth column '{col}': {e}") # Use warning instead of pass

    # Clean the Site Value column name before using it
    # Identify the correct column name first, handling variations
    potential_site_value_cols = ["Site Value (Rs.)****", "Site Value (Rs.)", "Site Value Rs****", "Site Value Rs."]
    actual_site_value_col = None
    for col_name in potential_site_value_cols:
        if col_name in df.columns:
            actual_site_value_col = col_name
            break # Found the column, stop searching

    if actual_site_value_col:
        try:
            # Clean the identified currency column
            df[actual_site_value_col] = df[actual_site_value_col].astype(str).str.replace(",", "", regex=False).str.strip()
            df[actual_site_value_col] = pd.to_numeric(df[actual_site_value_col], errors='coerce') # Coerce errors to NaN
        except Exception as e:
             st.warning(f"Could not fully clean currency column '{actual_site_value_col}': {e}") # Use warning
    else:
        st.warning(f"Could not find a suitable Site Value column among {potential_site_value_cols}. Some features might be unavailable.")


    # --- Normalize column names ---
    try:
        original_cols = df.columns.tolist() # Keep track for debugging if needed
        df.columns = df.columns.str.replace(r"[\\*()]+", "", regex=True) # Remove *, (, ) more reliably
        df.columns = df.columns.str.replace(r"\.\s*$", "", regex=True) # Remove trailing dots and spaces like in 'Rs.'
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip() # Consolidate multiple spaces and trim ends

        # Standardize 'Site Value Rs' - check variations AFTER cleaning special chars
        # Create a mapping for potential variations to the desired final name
        rename_map = {}
        potential_site_val_cleaned = ["Site Value Rs.", "Site Value Rs"] # Names after initial cleaning
        for potential_name in potential_site_val_cleaned:
            if potential_name in df.columns:
                rename_map[potential_name] = "Site Value Rs" # Target standard name

        df = df.rename(columns=rename_map)
        # Optional: Print original vs cleaned for debugging
        # print("Original columns:", original_cols)
        # print("Cleaned columns:", df.columns.tolist())
    except Exception as e:
        st.error(f"Error during column name normalization: {e}")
        # Depending on severity, you might return df or pd.DataFrame()
        return df # Return potentially partially cleaned df

    # Add an explicit check for essential columns needed by the app AFTER cleaning
    # Update this list based on columns actually used in plots/KPIs/filters
    required_cols_for_app = [
        "Site Name", "BW Group", "BW Allocated", "May Avg Mbps", "Site Value Rs",
        "March Avg Mbps", "April Avg Mbps", "Criteria 1 Max-C", "Criteria 2 Avg-C",
        "Criteria 3 BW Upgrade"
    ]
    missing_req_cols = [col for col in required_cols_for_app if col not in df.columns]
    if missing_req_cols:
        st.error(f"Critical columns missing after cleaning: {missing_req_cols}. Some visualizations or KPIs might fail. Please check the Excel file structure and column naming.")
        # Decide whether to stop or continue with limited functionality
        # return pd.DataFrame() # Option to stop if critical columns are missing

    return df

# Load dataset
df = load_data()

# --- Main App Logic ---

if df.empty:
    # Error messages are already shown in load_data if loading failed
    st.warning("Data loading failed or resulted in an empty DataFrame. Cannot proceed.")
else:
    # --- CSS Injection for Multiselect Tag Color (Already in set_page_background_and_styles) ---
    # No need to repeat the specific multiselect style here if it's included above

    st.title("Sri Lanka Site Bandwidth Dashboard")
    st.markdown("Use the filters in the sidebar. Click on the sections below to view details.")

    # Expander for Column Names - inherits background/text style from CSS
    with st.expander("📋 View Final Column Names"):
        if not df.empty:
            st.json(df.columns.tolist()) # Show final column names after cleaning
        else:
            st.write("Dataframe is empty, cannot show columns.")

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")

    # Define standardized column names to use throughout the app
    # Ensure these match the names AFTER cleaning in load_data()
    site_name_col = "Site Name"
    bw_group_col = "BW Group"
    bw_alloc_col = "BW Allocated"
    may_avg_col = "May Avg Mbps"
    may_max_col = "May Max Mbps"
    apr_avg_col = "April Avg Mbps"
    apr_max_col = "April Max Mbps"
    mar_avg_col = "March Avg Mbps"
    mar_max_col = "March Max Mbps"
    site_value_col = "Site Value Rs" # Use the normalized name
    crit1_col = "Criteria 1 Max-C"
    crit2_col = "Criteria 2 Avg-C"
    crit3_col = "Criteria 3 BW Upgrade"

    # Check if filter columns exist before creating options
    bw_groups_options = []
    if bw_group_col in df.columns:
        # Convert to string and fill NA to handle potential mixed types or missing values
        bw_groups_options = sorted(df[bw_group_col].astype(str).fillna('Unknown').unique())
    else:
        st.sidebar.warning(f"Column '{bw_group_col}' not found for BW Group filtering.")

    sites_options = []
    if site_name_col in df.columns:
        sites_options = sorted(df[site_name_col].astype(str).fillna('Unknown').unique())
    else:
        st.sidebar.warning(f"Column '{site_name_col}' not found for Site Name filtering.")

    # Create multiselect widgets
    # default=options means all are selected initially
    bw_groups = st.sidebar.multiselect("Select BW Groups",
                                       options=bw_groups_options,
                                       default=bw_groups_options)
    sites = st.sidebar.multiselect("Select Sites",
                                   options=sites_options,
                                   default=sites_options)

    # Apply filters to a copy of the DataFrame
    filtered_df = df.copy()
    if bw_group_col in filtered_df.columns and bw_groups:
        # Ensure comparison is robust to type issues, especially if fillna was used
        filtered_df = filtered_df[filtered_df[bw_group_col].astype(str).fillna('Unknown').isin(bw_groups)]
    if site_name_col in filtered_df.columns and sites:
        filtered_df = filtered_df[filtered_df[site_name_col].astype(str).fillna('Unknown').isin(sites)]

    # Optional: Show a warning if filters result in no data, but only if filters were actually changed from default
    if filtered_df.empty and not df.empty:
        filters_applied = False
        if bw_group_col in df.columns and bw_groups != bw_groups_options:
            filters_applied = True
        if site_name_col in df.columns and sites != sites_options:
            filters_applied = True

        if filters_applied:
             st.warning("No data matches the current filter selections.")
        # else: filters are default, df was empty to begin with (covered by initial check)

    # --- KPIs ---
    # This subheader and the columns will be inside a styled block due to the broad CSS selector
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)

    if not filtered_df.empty:
        # Calculate KPIs using the standardized column names
        total_sites = "N/A"
        if site_name_col in filtered_df.columns:
            total_sites = filtered_df[site_name_col].nunique()

        avg_may_usage = None
        if may_avg_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[may_avg_col]):
             # Drop NaNs before calculating mean to avoid issues/warnings
             avg_may_usage = filtered_df[may_avg_col].dropna().mean()

        avg_allocated = None
        if bw_alloc_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[bw_alloc_col]):
            avg_allocated = filtered_df[bw_alloc_col].dropna().mean()

        # Display KPIs
        col1.metric("Total Sites", f"{total_sites:,}" if isinstance(total_sites, int) else total_sites)
        col2.metric("Avg May Usage", f"{avg_may_usage:.2f} Mbps" if avg_may_usage is not None else "N/A")
        col3.metric("Avg Allocated BW", f"{avg_allocated:.2f} Mbps" if avg_allocated is not None else "N/A")
    else:
        # Display default values if no data after filtering
        col1.metric("Total Sites", 0)
        col2.metric("Avg May Usage", "N/A")
        col3.metric("Avg Allocated BW", "N/A")


    # This header will also be inside a styled block
    st.header("Visualizations")

    if not filtered_df.empty:
        # Define common plot layout updates for transparency and WHITE font color
        transparent_layout = dict(
            paper_bgcolor='rgba(0,0,0,0)', # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area
            font_color='white'              # White text for titles, axes, etc.
        )
        # Specific layout for pie charts (might need legend font color explicitly)
        pie_layout = dict(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            legend_font_color='white'       # Ensure legend text is also white
        )

        # -- Expander for Bar Chart --
        with st.expander("📈 Monthly Avg Bandwidth Usage"):
            # Use the column variables defined earlier
            monthly_cols = [site_name_col, mar_avg_col, apr_avg_col, may_avg_col]
            # Check if ALL required columns exist in the filtered dataframe
            missing_bar_cols = [c for c in monthly_cols if c not in filtered_df.columns]
            if not missing_bar_cols:
                # Select necessary columns, make a copy to avoid SettingWithCopyWarning
                monthly = filtered_df[monthly_cols].copy()
                # Drop rows where Site Name is missing (good practice, though unlikely with earlier fillna)
                monthly.dropna(subset=[site_name_col], inplace=True)
                # Drop rows where ALL month data are missing (no point plotting these)
                monthly.dropna(subset=monthly_cols[1:], how='all', inplace=True)

                if not monthly.empty:
                    try:
                        # Melt the dataframe for easy plotting with Plotly Express
                        monthly_melted = monthly.melt(id_vars=site_name_col, var_name="Month", value_name="Avg Mbps")
                        # Ensure value column is numeric AFTER melting (handles NaNs from coerce earlier)
                        monthly_melted['Avg Mbps'] = pd.to_numeric(monthly_melted['Avg Mbps'], errors='coerce')
                        # Remove rows where conversion failed or was originally NaN/non-numeric
                        monthly_melted.dropna(subset=['Avg Mbps'], inplace=True)

                        if not monthly_melted.empty:
                            # Create the bar chart
                            fig1 = px.bar(monthly_melted, x=site_name_col, y="Avg Mbps", color="Month",
                                          barmode="group", title="Avg Bandwidth per Site per Month")
                            # Apply the transparent layout and rotate x-axis labels
                            fig1.update_layout(xaxis_tickangle=-45, **transparent_layout)
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.info("No numeric average bandwidth data to plot for the selected sites/groups after cleaning.")
                    except Exception as e:
                        st.error(f"Error creating monthly usage chart: {e}")
                else:
                    st.info("No data available for Monthly Usage plot (all relevant month values might be missing or non-numeric for filtered data).")
            else:
                # Show which specific columns are missing for this chart
                st.warning(f"❗ Bar chart skipped — required column(s) missing: {missing_bar_cols}")

        # -- Expander for Scatter Plot --
        with st.expander("🎯 Criteria Analysis"):
            # Use column variables defined earlier
            scatter_req_cols = [crit1_col, crit2_col, crit3_col]
            scatter_hover_cols = [site_name_col, bw_alloc_col] # Use defined vars for hover data
            # Check if ALL required columns exist
            missing_scatter_cols = [c for c in scatter_req_cols + scatter_hover_cols if c not in filtered_df.columns]
            if not missing_scatter_cols:
                # Create a copy and drop rows where any of the essential criteria columns are missing
                scatter_df = filtered_df.dropna(subset=scatter_req_cols).copy()
                if not scatter_df.empty:
                    # Ensure Criteria 3 is treated as categorical (string) for color mapping
                    scatter_df[crit3_col] = scatter_df[crit3_col].astype(str)
                    try:
                        # Create scatter plot
                        fig2 = px.scatter(scatter_df,
                                          x=crit1_col,
                                          y=crit2_col,
                                          color=crit3_col,        # Color by upgrade status
                                          hover_data=scatter_hover_cols, # Show site name and allocated BW on hover
                                          title="Criteria 1 vs 2 by BW Upgrade Status")
                        # Apply the transparent layout
                        fig2.update_layout(**transparent_layout)
                        st.plotly_chart(fig2, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating criteria scatter plot: {e}")
                else:
                     st.info("No data available for Criteria Analysis plot (rows might be missing essential criteria values).")
            else:
                # Show which specific columns are missing for this chart
                st.warning(f"❗ Scatter plot skipped — required column(s) missing: {missing_scatter_cols}")

        # -- Expander for Box Plot --
        with st.expander("💰 Site Value Distribution by BW Group"):
             # Use column variables defined earlier
            box_plot_cols = [bw_group_col, site_value_col]
            missing_box_cols = [c for c in box_plot_cols if c not in filtered_df.columns]
            if not missing_box_cols:
                # Create a copy and drop rows where BW Group or Site Value is missing
                box_df = filtered_df.dropna(subset=box_plot_cols).copy()
                if not box_df.empty:
                    # Ensure BW Group is treated as categorical (string)
                    box_df[bw_group_col] = box_df[bw_group_col].astype(str)
                    # Check if Site Value is numeric before plotting
                    if pd.api.types.is_numeric_dtype(box_df[site_value_col]):
                        try:
                            # Create box plot
                            fig3 = px.box(box_df, x=bw_group_col, y=site_value_col,
                                          title="Site Value Distribution by BW Group")
                            # Apply the transparent layout
                            fig3.update_layout(**transparent_layout)
                            st.plotly_chart(fig3, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating site value box plot: {e}")
                    else:
                        st.warning(f"❗ Box plot skipped - Column '{site_value_col}' is not numeric after cleaning.")
                else:
                    st.info("No data available for Site Value box plot (rows might be missing BW Group or Site Value).")
            else:
                # Show which specific columns are missing for this chart
                st.warning(f"❗ Box plot skipped — required column(s) missing: {missing_box_cols}")


        # -- Expander for Pie Chart --
        with st.expander("🍰 Bandwidth Allocation Share by Group"):
            # Use column variables defined earlier
            pie_chart_cols = [bw_group_col, bw_alloc_col]
            missing_pie_cols = [c for c in pie_chart_cols if c not in filtered_df.columns]
            if not missing_pie_cols:
                 # Group by BW Group (handle potential NaNs in group name)
                 # Sum BW Allocated (fill NaNs in allocation with 0 before summing)
                 # Use fillna for both group and value before grouping
                bw_group_sum = filtered_df.fillna({bw_alloc_col: 0, bw_group_col: 'Unknown'}) \
                                          .groupby(bw_group_col)[bw_alloc_col].sum().reset_index()
                # Filter out groups with zero or negative total allocation (if possible/meaningful)
                bw_group_sum = bw_group_sum[bw_group_sum[bw_alloc_col] > 0]

                if not bw_group_sum.empty:
                    try:
                        # Create pie chart
                        fig_pie = px.pie(bw_group_sum, names=bw_group_col, values=bw_alloc_col,
                                         title='Total Allocated BW by Group (Filtered Data)',
                                         hole=0.3) # Make it a donut chart
                        # Improve text visibility inside slices
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                        # Apply the specific pie layout (ensures legend is white too)
                        fig_pie.update_layout(**pie_layout)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating allocation pie chart: {e}")
                else:
                    st.info("No positive allocated bandwidth data found for the selected filters to display pie chart.")
            else:
                # Show which specific columns are missing for this chart
                st.warning(f"❗ Pie chart skipped — required column(s) missing: {missing_pie_cols}")

        # --- Data Table Section ---
        # This subheader and dataframe will inherit the background block styling from the main CSS rule
        st.subheader("📄 Filtered Data Preview")

        # Display the filtered data in a table, showing NaNs explicitly for clarity
        # Use .head(100) to limit display size for performance
        st.dataframe(filtered_df.head(100).fillna("N/A")) # Fill NaN with "N/A" for display

        # Show caption with total number of filtered rows
        st.caption(f"Displaying first 100 rows of {len(filtered_df):,} total filtered rows.")

    else: # if filtered_df is empty
         # This info message will also be in a styled block
         # Check if the initial df was empty vs filtering caused empty
         if df.empty:
             # This case is already handled by the top-level check, but defensive coding doesn't hurt
             st.info("Load data first.")
         else:
             # Only show this if filtering actually resulted in an empty set
             st.info("Adjust filters in the sidebar to view visualizations and data preview. No data matches current selection.")

# End: if not df.empty:

# --- END OF FILE app.py ---