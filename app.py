# --- START OF FILE app.py ---

import streamlit as st
import pandas as pd
import plotly.express as px
import os # Keep os for path checking

# --- Load and Clean Data ---
@st.cache_data # Cache the data loading and cleaning
def load_data():
    """ Loads and preprocesses data from the Excel file. """
    excel_file = "preprocessed_data (76).xlsx"
    excel_file_abs = "/Users/vihanga/Downloads/DSPL_Individual_CW/preprocessed_data (76).xlsx" # Keep as fallback

    file_to_load = None
    if os.path.exists(excel_file):
        file_to_load = excel_file
    elif os.path.exists(excel_file_abs):
        file_to_load = excel_file_abs
        st.info(f"Using absolute path for Excel file: {file_to_load}")
    else:
        st.error(f"Excel file not found. Checked: './{excel_file}' and '{excel_file_abs}'.")
        return pd.DataFrame() # Return empty if file not found

    try:
        df = pd.read_excel(file_to_load)
        st.success(f"Successfully loaded data from: {file_to_load}")
    except Exception as e:
        st.error(f"Error loading or parsing Excel file '{file_to_load}': {e}")
        return pd.DataFrame()

    # --- Column Cleaning ---
    bandwidth_cols = ["BW Allocated", "May Avg (Mbps)", "May Max (Mbps)", "April Avg (Mbps)", "April Max (Mbps)", "March Avg (Mbps)", "March Max (Mbps)"]
    for col in bandwidth_cols:
        if col in df.columns:
            try:
                df[col] = df[col].astype(str).str.replace(" Mbps", "", regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                st.warning(f"Could not fully clean bandwidth column '{col}': {e}")

    potential_site_value_cols = ["Site Value (Rs.)****", "Site Value (Rs.)", "Site Value Rs****", "Site Value Rs."]
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
    # else: # Don't necessarily warn if it's just missing
    #     st.warning(f"Could not find a suitable Site Value column among {potential_site_value_cols}.")


    # --- Normalize column names ---
    try:
        original_cols = df.columns.tolist()
        df.columns = df.columns.str.replace(r"[\\*()]+", "", regex=True)
        df.columns = df.columns.str.replace(r"\.\s*$", "", regex=True)
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()

        rename_map = {}
        potential_site_val_cleaned = ["Site Value Rs.", "Site Value Rs"]
        for potential_name in potential_site_val_cleaned:
            if potential_name in df.columns:
                rename_map[potential_name] = "Site Value Rs"

        df = df.rename(columns=rename_map)
    except Exception as e:
        st.error(f"Error during column name normalization: {e}")
        # Return partially cleaned df if normalization fails
        return df

    # Optional: Check for essential columns AFTER cleaning if needed for core functionality
    # required_cols_for_app = ["Site Name", "BW Group", "BW Allocated"] # Example
    # missing_req_cols = [col for col in required_cols_for_app if col not in df.columns]
    # if missing_req_cols:
    #     st.error(f"Core columns missing after cleaning: {missing_req_cols}.")
        # Decide whether to return empty df or continue: return pd.DataFrame()

    return df

# --- Load Data ---
df = load_data()

# --- Main App Logic ---

st.title("Sri Lanka Site Bandwidth Dashboard")

if df.empty:
    st.warning("Data loading failed or resulted in an empty DataFrame. Cannot display dashboard.")
else:
    st.markdown("Use the filters in the sidebar to analyze the data.")

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")

    # Define standardized column names (ensure these match cleaned names)
    site_name_col = "Site Name"
    bw_group_col = "BW Group"
    bw_alloc_col = "BW Allocated"
    may_avg_col = "May Avg Mbps"
    mar_avg_col = "March Avg Mbps"
    apr_avg_col = "April Avg Mbps"
    site_value_col = "Site Value Rs"
    crit1_col = "Criteria 1 Max-C"
    crit2_col = "Criteria 2 Avg-C"
    crit3_col = "Criteria 3 BW Upgrade"

    # Get filter options safely
    bw_groups_options = sorted(df[bw_group_col].astype(str).fillna('Unknown').unique()) if bw_group_col in df.columns else []
    sites_options = sorted(df[site_name_col].astype(str).fillna('Unknown').unique()) if site_name_col in df.columns else []

    if not bw_groups_options: st.sidebar.warning(f"Column '{bw_group_col}' not found for filtering.")
    if not sites_options: st.sidebar.warning(f"Column '{site_name_col}' not found for filtering.")

    # Multiselect widgets
    bw_groups = st.sidebar.multiselect("Select BW Groups", options=bw_groups_options, default=bw_groups_options)
    sites = st.sidebar.multiselect("Select Sites", options=sites_options, default=sites_options)

    # Apply filters
    filtered_df = df.copy()
    if bw_group_col in filtered_df.columns and bw_groups:
        filtered_df = filtered_df[filtered_df[bw_group_col].astype(str).fillna('Unknown').isin(bw_groups)]
    if site_name_col in filtered_df.columns and sites:
        filtered_df = filtered_df[filtered_df[site_name_col].astype(str).fillna('Unknown').isin(sites)]

    # Warning if filters yield no results
    if filtered_df.empty and not df.empty:
        # Check if filters were actually applied (i.e., not still the default full list)
        filters_applied = (bw_groups != bw_groups_options and bw_groups_options) or \
                          (sites != sites_options and sites_options)
        if filters_applied:
            st.warning("No data matches the current filter selections.")

    # --- KPIs ---
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)

    if not filtered_df.empty:
        # Calculate KPIs safely, checking for column existence
        total_sites = filtered_df[site_name_col].nunique() if site_name_col in filtered_df.columns else "N/A"
        avg_may_usage = filtered_df[may_avg_col].dropna().mean() if may_avg_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[may_avg_col]) else None
        avg_allocated = filtered_df[bw_alloc_col].dropna().mean() if bw_alloc_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[bw_alloc_col]) else None

        col1.metric("Total Sites", f"{total_sites:,}" if isinstance(total_sites, int) else total_sites)
        col2.metric("Avg May Usage", f"{avg_may_usage:.2f} Mbps" if avg_may_usage is not None else "N/A")
        col3.metric("Avg Allocated BW", f"{avg_allocated:.2f} Mbps" if avg_allocated is not None else "N/A")
    else:
        # Display default values if no data
        col1.metric("Total Sites", 0)
        col2.metric("Avg May Usage", "N/A")
        col3.metric("Avg Allocated BW", "N/A")

    # --- Visualizations ---
    st.header("Visualizations")

    if not filtered_df.empty:
        # Expander structure for plots
        with st.expander("📈 Monthly Avg Bandwidth Usage", expanded=True): # Expand first chart by default
            monthly_cols = [site_name_col, mar_avg_col, apr_avg_col, may_avg_col]
            if all(col in filtered_df.columns for col in monthly_cols):
                monthly = filtered_df[monthly_cols].copy().dropna(subset=monthly_cols[1:], how='all')
                if not monthly.empty:
                    try:
                        monthly_melted = monthly.melt(id_vars=site_name_col, var_name="Month", value_name="Avg Mbps")
                        monthly_melted['Avg Mbps'] = pd.to_numeric(monthly_melted['Avg Mbps'], errors='coerce').dropna()
                        if not monthly_melted.empty:
                            fig1 = px.bar(monthly_melted, x=site_name_col, y="Avg Mbps", color="Month", barmode="group", title="Avg Bandwidth per Site per Month")
                            fig1.update_layout(xaxis_tickangle=-45) # Keep axis rotation
                            st.plotly_chart(fig1, use_container_width=True)
                        else: st.info("No numeric monthly average bandwidth data to plot for selected filters.")
                    except Exception as e: st.error(f"Error creating monthly usage chart: {e}")
                else: st.info("No data available for Monthly Usage plot for selected filters.")
            else: st.warning(f"❗ Cannot create Monthly Usage chart - Missing columns: {[c for c in monthly_cols if c not in filtered_df.columns]}")

        with st.expander("🎯 Criteria Analysis"):
            scatter_req_cols = [crit1_col, crit2_col, crit3_col]
            scatter_hover_cols = [site_name_col, bw_alloc_col]
            if all(col in filtered_df.columns for col in scatter_req_cols + scatter_hover_cols):
                scatter_df = filtered_df.dropna(subset=scatter_req_cols).copy()
                if not scatter_df.empty:
                    scatter_df[crit3_col] = scatter_df[crit3_col].astype(str)
                    try:
                        fig2 = px.scatter(scatter_df, x=crit1_col, y=crit2_col, color=crit3_col, hover_data=scatter_hover_cols, title="Criteria 1 vs 2 by BW Upgrade Status")
                        st.plotly_chart(fig2, use_container_width=True)
                    except Exception as e: st.error(f"Error creating criteria scatter plot: {e}")
                else: st.info("No data available for Criteria Analysis plot for selected filters (rows missing essential criteria).")
            else: st.warning(f"❗ Cannot create Criteria Analysis chart - Missing columns: {[c for c in scatter_req_cols + scatter_hover_cols if c not in filtered_df.columns]}")

        with st.expander("💰 Site Value Distribution by BW Group"):
            box_plot_cols = [bw_group_col, site_value_col]
            if all(col in filtered_df.columns for col in box_plot_cols):
                box_df = filtered_df.dropna(subset=box_plot_cols).copy()
                if not box_df.empty:
                    box_df[bw_group_col] = box_df[bw_group_col].astype(str)
                    if pd.api.types.is_numeric_dtype(box_df[site_value_col]):
                        try:
                            fig3 = px.box(box_df, x=bw_group_col, y=site_value_col, title="Site Value Distribution by BW Group")
                            st.plotly_chart(fig3, use_container_width=True)
                        except Exception as e: st.error(f"Error creating site value box plot: {e}")
                    else: st.warning(f"❗ Box plot skipped - Column '{site_value_col}' is not numeric.")
                else: st.info("No data available for Site Value box plot for selected filters (rows missing Site Value or BW Group).")
            else: st.warning(f"❗ Cannot create Site Value Distribution chart - Missing columns: {[c for c in box_plot_cols if c not in filtered_df.columns]}")

        with st.expander("🍰 Bandwidth Allocation Share by Group"):
            pie_chart_cols = [bw_group_col, bw_alloc_col]
            if all(col in filtered_df.columns for col in pie_chart_cols):
                bw_group_sum = filtered_df.fillna({bw_alloc_col: 0, bw_group_col: 'Unknown'}).groupby(bw_group_col)[bw_alloc_col].sum().reset_index()
                bw_group_sum = bw_group_sum[bw_group_sum[bw_alloc_col] > 0]
                if not bw_group_sum.empty:
                    try:
                        fig_pie = px.pie(bw_group_sum, names=bw_group_col, values=bw_alloc_col, title='Total Allocated BW by Group (Filtered Data)', hole=0.3)
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    except Exception as e: st.error(f"Error creating allocation pie chart: {e}")
                else: st.info("No positive allocated bandwidth data found for pie chart for selected filters.")
            else: st.warning(f"❗ Cannot create Allocation Share chart - Missing columns: {[c for c in pie_chart_cols if c not in filtered_df.columns]}")

    # --- Data Table Section ---
    st.subheader("📄 Filtered Data Preview")
    if not filtered_df.empty:
        # Display the filtered data using st.dataframe (better for large tables)
        st.dataframe(filtered_df.head(100).fillna("N/A"), use_container_width=True) # Limit display, fill NA
        st.caption(f"Displaying first 100 rows of {len(filtered_df):,} total filtered rows.")
    else:
        st.info("No data to display based on current filters.")

# End: if df.empty check

# --- END OF FILE app.py ---