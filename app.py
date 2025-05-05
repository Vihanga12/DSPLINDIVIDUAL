import streamlit as st
import pandas as pd
import plotly.express as px
import os  # Keep os for path checking

# --- Load and Clean Data ---
@st.cache_data
def load_data():
    """ Loads and preprocesses data from the Excel file. """
    excel_file = "preprocessed_data (76).xlsx"
    excel_file_abs = "/Users/vihanga/Downloads/DSPL_Individual_CW/preprocessed_data (76).xlsx"

    file_to_load = None
    if os.path.exists(excel_file):
        file_to_load = excel_file
    elif os.path.exists(excel_file_abs):
        file_to_load = excel_file_abs
        st.info(f"Using absolute path for Excel file: {file_to_load}")
    else:
        return pd.DataFrame()

    try:
        df = pd.read_excel(file_to_load)
    except Exception as e:
        st.error(f"Error loading or parsing Excel file '{file_to_load}': {e}")
        return pd.DataFrame()

    bandwidth_cols = [
        "BW Allocated", "May Avg (Mbps)", "May Max (Mbps)",
        "April Avg (Mbps)", "April Max (Mbps)",
        "March Avg (Mbps)", "March Max (Mbps)"
    ]
    for col in bandwidth_cols:
        if col in df.columns:
            try:
                df[col] = df[col].astype(str).str.replace(" Mbps", "", regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                st.warning(f"Could not fully clean bandwidth column '{col}': {e}")

    potential_site_value_cols = [
        "Site Value (Rs.)****", "Site Value (Rs.)",
        "Site Value Rs****", "Site Value Rs."
    ]
    actual_site_value_col = None
    for col_name in potential_site_value_cols:
        if col_name in df.columns:
            actual_site_value_col = col_name
            break

    if actual_site_value_col:
        try:
            df[actual_site_value_col] = df[actual_site_value_col].astype(str).str.replace(",", "", regex=False).str.strip()
            df[actual_site_value_col] = pd.to_numeric(df[actual_site_value_col], errors='coerce')
        except Exception as e:
            st.warning(f"Could not fully clean currency column '{actual_site_value_col}': {e}")

    try:
        df.columns = df.columns.str.replace(r"[\\*()]+", "", regex=True)
        df.columns = df.columns.str.replace(r"\.\s*$", "", regex=True)
        df.columns = df.columns.str.replace(" Mbps", "", regex=False)
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        rename_map = {}
        potential_site_val_cleaned = ["Site Value Rs.", "Site Value Rs"]
        for potential_name in potential_site_val_cleaned:
            if potential_name in df.columns:
                rename_map[potential_name] = "Site Value Rs"
        df = df.rename(columns=rename_map)
    except Exception as e:
        st.error(f"Error during column name normalization: {e}")
        return df

    return df

# --- Load Data ---
df_raw = load_data()

# --- Main App Title ---
st.title("Sri Lanka Site Bandwidth Dashboard")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page_selection = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Raw Data View"]
)

# --- Page Display Logic ---
if df_raw.empty:
    st.warning("Data loading failed or resulted in an empty DataFrame. Cannot display content.")
else:
    st.success("Successfully loaded data.")

    if page_selection == "Dashboard":
        st.header("📊 Dashboard")
        st.markdown("Use the filters below to analyze the data.")

        st.sidebar.header("Filter Options")

        site_name_col = "Site Name"
        bw_group_col = "BW Group"
        bw_alloc_col = "BW Allocated"
        may_avg_col = "May Avg"
        mar_avg_col = "March Avg"
        apr_avg_col = "April Avg"
        site_value_col = "Site Value Rs"
        crit1_col = "Criteria 1 Max-C"
        crit2_col = "Criteria 2 Avg-C"
        crit3_col = "Criteria 3 BW Upgrade"

        bw_groups_options = sorted(df_raw[bw_group_col].astype(str).fillna('Unknown').unique()) if bw_group_col in df_raw.columns else []
        sites_options = sorted(df_raw[site_name_col].astype(str).fillna('Unknown').unique()) if site_name_col in df_raw.columns else []

        if not bw_groups_options:
            st.sidebar.warning(f"Column '{bw_group_col}' not found for filtering.")
        if not sites_options:
            st.sidebar.warning(f"Column '{site_name_col}' not found for filtering.")

        bw_groups = st.sidebar.multiselect("Select BW Groups", options=bw_groups_options, default=bw_groups_options)
        sites = st.sidebar.multiselect("Select Sites", options=sites_options, default=sites_options)

        filtered_df = df_raw.copy()
        if bw_group_col in filtered_df.columns and bw_groups:
            filtered_df = filtered_df[filtered_df[bw_group_col].astype(str).fillna('Unknown').isin(map(str, bw_groups))]
        if site_name_col in filtered_df.columns and sites:
            filtered_df = filtered_df[filtered_df[site_name_col].astype(str).fillna('Unknown').isin(map(str, sites))]

        if filtered_df.empty and not df_raw.empty:
            filters_applied = (bw_groups != bw_groups_options and bw_groups_options) or \
                              (sites != sites_options and sites_options)
            if filters_applied:
                st.warning("No data matches the current filter selections.")

        # --- KPIs ---
        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)

        if not filtered_df.empty:
            total_sites = filtered_df[site_name_col].nunique() if site_name_col in filtered_df.columns else "N/A"
            avg_may_usage = filtered_df[may_avg_col].dropna().mean() if may_avg_col in filtered_df.columns else None
            avg_allocated = filtered_df[bw_alloc_col].dropna().mean() if bw_alloc_col in filtered_df.columns else None

            col1.metric("Total Sites", f"{total_sites:,}" if isinstance(total_sites, int) else total_sites)
            col2.metric("Avg May Usage", f"{avg_may_usage:.2f} Mbps" if avg_may_usage is not None else "N/A")
            col3.metric("Avg Allocated BW", f"{avg_allocated:.2f} Mbps" if avg_allocated is not None else "N/A")
        else:
            col1.metric("Total Sites", 0)
            col2.metric("Avg May Usage", "N/A")
            col3.metric("Avg Allocated BW", "N/A")

        st.header("Visualizations")

        if not filtered_df.empty:
            with st.expander("📈 Monthly Avg Bandwidth Usage", expanded=True):
                monthly_cols = [site_name_col, mar_avg_col, apr_avg_col, may_avg_col]
                if all(col in filtered_df.columns for col in monthly_cols):
                    monthly = filtered_df[monthly_cols].dropna(subset=monthly_cols[1:], how='all')
                    if not monthly.empty:
                        try:
                            monthly_melted = monthly.melt(id_vars=site_name_col, var_name="Month", value_name="Avg Mbps")
                            month_map = {mar_avg_col: "March", apr_avg_col: "April", may_avg_col: "May"}
                            monthly_melted['Month'] = monthly_melted['Month'].map(month_map)
                            monthly_melted['Avg Mbps'] = pd.to_numeric(monthly_melted['Avg Mbps'], errors='coerce').dropna()
                            if not monthly_melted.empty:
                                fig1 = px.bar(monthly_melted, x=site_name_col, y="Avg Mbps", color="Month", barmode="group", title="Avg Bandwidth per Site per Month")
                                fig1.update_layout(xaxis_tickangle=-45)
                                st.plotly_chart(fig1, use_container_width=True)
                            else:
                                st.info("No numeric monthly average bandwidth data to plot.")
                        except Exception as e:
                            st.error(f"Error creating monthly usage chart: {e}")
                else:
                    st.warning(f"Missing columns: {[c for c in monthly_cols if c not in filtered_df.columns]}")

            with st.expander("🎯 Criteria Analysis"):
                scatter_req_cols = [crit1_col, crit2_col, crit3_col]
                scatter_hover_cols = [site_name_col, bw_alloc_col]
                if all(col in filtered_df.columns for col in scatter_req_cols + scatter_hover_cols):
                    scatter_df = filtered_df.dropna(subset=scatter_req_cols).copy()
                    scatter_df[crit3_col] = scatter_df[crit3_col].astype(str)
                    if not scatter_df.empty:
                        try:
                            fig2 = px.scatter(scatter_df, x=crit1_col, y=crit2_col, color=crit3_col, hover_data=scatter_hover_cols, title="Criteria 1 vs 2 by BW Upgrade Status")
                            st.plotly_chart(fig2, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating scatter plot: {e}")

            with st.expander("💰 Site Value Distribution by BW Group"):
                if all(col in filtered_df.columns for col in [bw_group_col, site_value_col]):
                    box_df = filtered_df.dropna(subset=[bw_group_col, site_value_col]).copy()
                    if not box_df.empty:
                        try:
                            fig3 = px.box(box_df, x=bw_group_col, y=site_value_col, title="Site Value Distribution by BW Group")
                            st.plotly_chart(fig3, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating box plot: {e}")

            with st.expander("🍰 Bandwidth Allocation Share by Group"):
                if all(col in filtered_df.columns for col in [bw_group_col, bw_alloc_col]):
                    temp_df_pie = filtered_df.copy()
                    temp_df_pie[bw_alloc_col] = pd.to_numeric(temp_df_pie[bw_alloc_col], errors='coerce')
                    bw_group_sum = temp_df_pie.groupby(bw_group_col)[bw_alloc_col].sum().reset_index()
                    bw_group_sum = bw_group_sum[bw_group_sum[bw_alloc_col] > 0]
                    if not bw_group_sum.empty:
                        try:
                            fig_pie = px.pie(bw_group_sum, names=bw_group_col, values=bw_alloc_col, title='Total Allocated BW by Group (Filtered Data)', hole=0.3)
                            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_pie, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating pie chart: {e}")

        st.subheader("📄 Filtered Data Preview")
        if not filtered_df.empty:
            st.dataframe(filtered_df.head(100).fillna("N/A"), use_container_width=True)
            st.caption(f"Displaying first 100 rows of {len(filtered_df):,} total filtered rows.")

    # --- Raw Data View ---
    elif page_selection == "Raw Data View":
        st.header("📄 Raw Data Table")

        st.markdown("---")  # Horizontal rule

        st.subheader("About This Dashboard")
        st.markdown("""
        **Dashboard Title:** Sri Lanka Site Bandwidth Dashboard

        **Main Purpose:**  
        To provide an interactive platform for analyzing telecommunication site bandwidth allocation, usage patterns (across recent months), and site value metrics across different regions or groups in Sri Lanka.  
        It helps identify potential areas for optimization, upgrades, or cost assessment based on usage and predefined criteria.

        **Target Users:**  
        Network planners, capacity managers, operations teams, and financial analysts involved in managing and optimizing the telecommunications infrastructure and budget.

        **Dashboard Sections (Available in 'Dashboard' View):**
        - **Key Metrics:** High-level overview of total sites, average usage, and average allocation.
        - **Filters:** Options to slice data by BW Group and specific Sites.
        - **Visualizations:**
            - Monthly Average Bandwidth Usage per Site.
            - Criteria Analysis (Scatter plot based on performance metrics).
            - Site Value Distribution by Bandwidth Group.
            - Bandwidth Allocation Share by Group (Pie Chart).
        - **Filtered Data Preview:** A table showing the data rows corresponding to the active filters.
        """)

        st.markdown("---")  # Horizontal rule

        st.markdown("Below is the complete dataset after initial loading and cleaning steps:")
        st.dataframe(df_raw.fillna("N/A"), use_container_width=True)
        st.caption(f"Displaying all {len(df_raw):,} rows.")
