import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Load and Clean Data ---
@st.cache_data
def load_data():
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

        bw_groups = st.sidebar.multiselect("Select BW Groups", options=bw_groups_options, default=bw_groups_options)
        sites = st.sidebar.multiselect("Select Sites", options=sites_options, default=sites_options)

        filtered_df = df_raw.copy()
        if bw_group_col in filtered_df.columns and bw_groups:
            filtered_df = filtered_df[filtered_df[bw_group_col].astype(str).fillna('Unknown').isin(map(str, bw_groups))]
        if site_name_col in filtered_df.columns and sites:
            filtered_df = filtered_df[filtered_df[site_name_col].astype(str).fillna('Unknown').isin(map(str, sites))]

        # --- KPIs ---
        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)

        if not filtered_df.empty:
            total_sites = filtered_df[site_name_col].nunique()
            avg_may_usage = filtered_df[may_avg_col].dropna().mean()
            avg_allocated = filtered_df[bw_alloc_col].dropna().mean()

            col1.metric("Total Sites", f"{total_sites:,}")
            col2.metric("Avg May Usage", f"{avg_may_usage:.2f} Mbps")
            col3.metric("Avg Allocated BW", f"{avg_allocated:.2f} Mbps")

        st.header("Visualizations")

        if not filtered_df.empty:
            with st.expander("📈 Monthly Avg Bandwidth Usage", expanded=True):
                monthly_cols = [site_name_col, mar_avg_col, apr_avg_col, may_avg_col]
                if all(col in filtered_df.columns for col in monthly_cols):
                    monthly = filtered_df[monthly_cols].dropna(subset=monthly_cols[1:], how='all')
                    monthly_melted = monthly.melt(id_vars=site_name_col, var_name="Month", value_name="Avg Mbps")
                    month_map = {mar_avg_col: "March", apr_avg_col: "April", may_avg_col: "May"}
                    monthly_melted['Month'] = monthly_melted['Month'].map(month_map)
                    fig1 = px.bar(monthly_melted, x=site_name_col, y="Avg Mbps", color="Month", barmode="group", title="Avg Bandwidth per Site per Month")
                    fig1.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig1, use_container_width=True)

            with st.expander("📉 Monthly Avg Bandwidth Trends by BW Group"):
                if all(col in filtered_df.columns for col in [bw_group_col, mar_avg_col, apr_avg_col, may_avg_col]):
                    trend_df = filtered_df[[bw_group_col, mar_avg_col, apr_avg_col, may_avg_col]].dropna(how="all")
                    trend_grouped = trend_df.groupby(bw_group_col).mean().reset_index()
                    trend_melted = trend_grouped.melt(id_vars=bw_group_col, var_name="Month", value_name="Avg Mbps")
                    month_map = {mar_avg_col: "March", apr_avg_col: "April", may_avg_col: "May"}
                    trend_melted["Month"] = trend_melted["Month"].map(month_map)
                    fig_line = px.line(trend_melted, x="Month", y="Avg Mbps", color=bw_group_col, markers=True, title="Monthly Avg Bandwidth Trends by BW Group")
                    st.plotly_chart(fig_line, use_container_width=True)

            with st.expander("🎯 Criteria Analysis"):
                scatter_df = filtered_df.dropna(subset=[crit1_col, crit2_col, crit3_col])
                scatter_df[crit3_col] = scatter_df[crit3_col].astype(str)
                fig2 = px.scatter(scatter_df, x=crit1_col, y=crit2_col, color=crit3_col, hover_data=[site_name_col, bw_alloc_col], title="Criteria 1 vs 2 by BW Upgrade Status")
                st.plotly_chart(fig2, use_container_width=True)

            with st.expander("💰 Site Value Distribution by BW Group"):
                box_df = filtered_df.dropna(subset=[bw_group_col, site_value_col])
                fig3 = px.box(box_df, x=bw_group_col, y=site_value_col, title="Site Value Distribution by BW Group")
                st.plotly_chart(fig3, use_container_width=True)

            with st.expander("🍰 Bandwidth Allocation Share by Group"):
                pie_df = filtered_df[[bw_group_col, bw_alloc_col]].dropna()
                pie_df[bw_alloc_col] = pd.to_numeric(pie_df[bw_alloc_col], errors='coerce')
                bw_sum = pie_df.groupby(bw_group_col)[bw_alloc_col].sum().reset_index()
                fig_pie = px.pie(bw_sum, names=bw_group_col, values=bw_alloc_col, title='Total Allocated BW by Group (Filtered Data)', hole=0.3)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📄 Filtered Data Preview")
        st.dataframe(filtered_df.head(100).fillna("N/A"), use_container_width=True)
        st.caption(f"Displaying first 100 rows of {len(filtered_df):,} total filtered rows.")

    elif page_selection == "Raw Data View":
        st.header("📄 Raw Data Table")
        st.markdown("---")
        st.subheader("About This Dashboard")
        st.markdown("""
        **Dashboard Title:** Sri Lanka Site Bandwidth Dashboard

        **Main Purpose:**  
        To provide an interactive platform for analyzing telecommunication site bandwidth allocation, usage patterns, and site value metrics across Sri Lanka.

        **Target Users:**  
        Network planners, capacity managers, operations teams, and financial analysts.

        **Dashboard Sections (Available in 'Dashboard' View):**
        - **Key Metrics**
        - **Filters**
        - **Visualizations**
        - **Filtered Data Preview**
        """)
        st.markdown("---")
        st.dataframe(df_raw.fillna("N/A"), use_container_width=True)
        st.caption(f"Displaying all {len(df_raw):,} rows.")
