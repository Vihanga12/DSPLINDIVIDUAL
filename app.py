

import streamlit as st
import pandas as pd
import plotly.express as px

# Load and clean data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("preprocessed_data (76).xlsx")
    except FileNotFoundError:
        st.error("Error: File not found at 'preprocessed_data (76).xlsx'. Make sure the file is in the same directory as app.py.")
        return pd.DataFrame() # Return empty DataFrame on error
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return pd.DataFrame()

    # Clean numeric columns with units
    bandwidth_cols = [
        "BW Allocated", "May Avg (Mbps)", "May Max (Mbps)",
        "April Avg (Mbps)", "April Max (Mbps)",
        "March Avg (Mbps)", "March Max (Mbps)"
    ]
    for col in bandwidth_cols:
        if col in df.columns:
            try:
                # Attempt cleaning and conversion
                df[col] = df[col].astype(str).str.replace(" Mbps", "", regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce') # Use coerce to handle errors gracefully
            except Exception as e:
                st.warning(f"Could not process column '{col}'. Error: {e}. Skipping cleaning.")
        else:
            st.warning(f"Expected column '{col}' not found. Skipping.")

    # Clean currency column
    currency_col = "Site Value (Rs.)****"
    if currency_col in df.columns:
        try:
            df[currency_col] = df[currency_col].astype(str).str.replace(",", "", regex=False).str.strip()
            df[currency_col] = pd.to_numeric(df[currency_col], errors='coerce')
        except Exception as e:
             st.warning(f"Could not process column '{currency_col}'. Error: {e}. Skipping cleaning.")
    else:
        st.warning(f"Expected column '{currency_col}' not found. Skipping.")

    # --- Normalize column names globally ---
    try:
        # Remove problematic characters: *, (, ), \
        df.columns = df.columns.str.replace(r"[\\*()]", "", regex=True)
        # Replace multiple spaces with single space and strip leading/trailing whitespace
        df.columns = df.columns.str.replace(r"\s+", " ", regex=True).str.strip()
        # Specific rename for Site Value to make it cleaner if it exists
        # Check for common variations after normalization
        if "Site Value Rs." in df.columns:
             df = df.rename(columns={"Site Value Rs.": "Site Value Rs"})
        elif "Site Value Rs****" in df.columns: # Check if normalization missed this
             df = df.rename(columns={"Site Value Rs****": "Site Value Rs"})

    except Exception as e:
        st.error(f"Error during column name normalization: {e}")
        return df # Return partially processed df

    return df

# Load dataset
df = load_data()

# --- Main App Logic ---

# Exit if data loading failed
if df.empty:
    st.error("Data loading failed. Cannot proceed.")
else:
    # DEBUG: Show exact column names after normalization (optional: keep or remove)
    # st.sidebar.write("📋 Column Names After Normalization:", df.columns.tolist())

    # App title
    st.title("Sri Lanka Site Bandwidth Dashboard")
    st.markdown("Use the filters in the sidebar. Click on the sections below to view details.")

    # --- Expander for Column Names ---
    with st.expander("📋 View Column Names After Normalization"):
        st.json(df.columns.tolist()) # st.json formats lists nicely

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")

    # Use normalized names for filtering if they exist
    bw_group_col = "BW Group"
    site_name_col = "Site Name"

    bw_groups = []
    if bw_group_col in df.columns:
        bw_groups = st.sidebar.multiselect(
            "Select BW Groups",
            options=sorted(df[bw_group_col].astype(str).fillna('Unknown').unique()),
            default=sorted(df[bw_group_col].astype(str).fillna('Unknown').unique())
        )
    else:
        st.sidebar.warning(f"Column '{bw_group_col}' not found for filtering.")

    sites = []
    if site_name_col in df.columns:
        sites = st.sidebar.multiselect(
            "Select Sites",
            options=sorted(df[site_name_col].astype(str).fillna('Unknown').unique()),
            default=sorted(df[site_name_col].astype(str).fillna('Unknown').unique())
        )
    else:
         st.sidebar.warning(f"Column '{site_name_col}' not found for filtering.")

    # Apply filters
    filtered_df = df.copy()
    if bw_group_col in filtered_df.columns and bw_groups:
        filtered_df = filtered_df[filtered_df[bw_group_col].astype(str).fillna('Unknown').isin(bw_groups)]
    if site_name_col in filtered_df.columns and sites:
        filtered_df = filtered_df[filtered_df[site_name_col].astype(str).fillna('Unknown').isin(sites)]

    if filtered_df.empty and not df.empty:
         st.warning("No data matches the current filter selections.")


    # --- KPIs ---
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)

    # Use normalized names for KPIs
    kpi_site_col = "Site Name"
    kpi_may_avg_col = "May Avg Mbps"
    kpi_bw_alloc_col = "BW Allocated"

    if not filtered_df.empty:
        if kpi_site_col in filtered_df.columns:
            col1.metric("Total Sites", filtered_df[kpi_site_col].nunique())
        else:
             col1.metric("Total Sites", "N/A")

        avg_may_usage = None
        if kpi_may_avg_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[kpi_may_avg_col]):
             avg_may_usage = filtered_df[kpi_may_avg_col].mean()
        col2.metric("Avg May Usage", f"{avg_may_usage:.2f} Mbps" if avg_may_usage is not None else "N/A")

        avg_allocated = None
        if kpi_bw_alloc_col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[kpi_bw_alloc_col]):
             avg_allocated = filtered_df[kpi_bw_alloc_col].mean()
        col3.metric("Avg Allocated BW", f"{avg_allocated:.2f} Mbps" if avg_allocated is not None else "N/A")
    else:
        col1.metric("Total Sites", 0)
        col2.metric("Avg May Usage", "N/A")
        col3.metric("Avg Allocated BW", "N/A")

    st.divider() # Add a visual separator

    # --- Visualizations (Inside Expanders) ---
    st.header("Visualizations")

    if not filtered_df.empty:

        # -- Expander for Bar Chart: Monthly Average Bandwidth --
        with st.expander("📈 Monthly Avg Bandwidth Usage"):
            # Use normalized names
            monthly_cols = ["Site Name", "March Avg Mbps", "April Avg Mbps", "May Avg Mbps"]
            if all(col in filtered_df.columns for col in monthly_cols):
                monthly = filtered_df[monthly_cols].copy()
                monthly.dropna(subset=monthly_cols[1:], how='all', inplace=True) # Drop if all avg values are NaN
                monthly.dropna(subset=[monthly_cols[0]], inplace=True) # Drop if Site Name is NaN

                if not monthly.empty:
                    try:
                        monthly_melted = monthly.melt(id_vars="Site Name", var_name="Month", value_name="Avg Mbps")
                         # Ensure 'Avg Mbps' is numeric for plotting
                        monthly_melted['Avg Mbps'] = pd.to_numeric(monthly_melted['Avg Mbps'], errors='coerce')
                        monthly_melted.dropna(subset=['Avg Mbps'], inplace=True)

                        if not monthly_melted.empty:
                            fig1 = px.bar(monthly_melted, x="Site Name", y="Avg Mbps", color="Month", barmode="group")
                            fig1.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.info("No numeric average bandwidth data to plot for the selected sites.")
                    except Exception as e:
                        st.error(f"Error creating monthly usage chart: {e}")
                else:
                     st.info("No data available for Monthly Average Usage plot after cleaning.")
            else:
                missing_cols = [col for col in monthly_cols if col not in filtered_df.columns]
                st.warning(f"❗ Chart not generated — column(s) missing: {missing_cols}")


        # -- Expander for Scatter Plot: Criteria 1 vs 2 --
        with st.expander("🎯 Criteria Analysis"):
            # Use normalized names
            scatter_req_cols = ["Criteria 1 Max-C", "Criteria 2 Avg-C", "Criteria 3 BW Upgrade"]
            scatter_hover_cols = ["Site Name", "BW Allocated"] # Also check these hover columns
            if all(col in filtered_df.columns for col in scatter_req_cols + scatter_hover_cols):
                # Drop rows where essential cols are NaN
                scatter_df = filtered_df.dropna(subset=scatter_req_cols).copy()
                if not scatter_df.empty:
                    # Ensure color column is string
                    scatter_df["Criteria 3 BW Upgrade"] = scatter_df["Criteria 3 BW Upgrade"].astype(str)
                    try:
                        fig2 = px.scatter(
                            scatter_df,
                            x="Criteria 1 Max-C",
                            y="Criteria 2 Avg-C",
                            color="Criteria 3 BW Upgrade",
                            hover_data=scatter_hover_cols,
                            title="Criteria 1 vs 2 by BW Upgrade" # Title can be inside or outside plot func
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    except Exception as e:
                         st.error(f"Error creating criteria scatter plot: {e}")
                else:
                    st.info("No data available for Criteria Analysis plot after cleaning.")
            else:
                missing_cols = [col for col in scatter_req_cols + scatter_hover_cols if col not in filtered_df.columns]
                st.warning(f"❗ Chart not generated — column(s) missing: {missing_cols}")


        # -- Expander for Box Plot: Site Value by BW Group --
        with st.expander("💰 Site Value Distribution"):
            # Use normalized names
            box_plot_y_col = "Site Value Rs" # Adjusted name from normalization logic
            box_plot_cols = ["BW Group", box_plot_y_col]
            if all(col in filtered_df.columns for col in box_plot_cols):
                box_df = filtered_df.dropna(subset=box_plot_cols).copy()
                if not box_df.empty:
                    # Ensure group is string
                    box_df["BW Group"] = box_df["BW Group"].astype(str)
                    try:
                        fig3 = px.box(box_df, x="BW Group", y=box_plot_y_col, title="Site Value by BW Group")
                        st.plotly_chart(fig3, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating site value box plot: {e}")
                else:
                    st.info("No data available for Site Value box plot after cleaning.")
            else:
                missing_cols = [col for col in box_plot_cols if col not in filtered_df.columns]
                st.warning(f"❗ Chart not generated — column(s) missing: {missing_cols}")


        # -- Expander for Pie Chart (BW Group Share) --
        with st.expander("🍰 Bandwidth Allocation Share by Group"):
            # Use normalized names
            pie_chart_cols = ['BW Group', 'BW Allocated']
            if all(col in filtered_df.columns for col in pie_chart_cols):
                # Group by BW Group and sum BW Allocated, fill NaN with 0 before summing
                # Ensure BW Group is treated as string for grouping and handle potential NaNs
                bw_group_sum = filtered_df.fillna({'BW Allocated': 0}) \
                                        .groupby(filtered_df['BW Group'].astype(str).fillna('Unknown'))['BW Allocated'] \
                                        .sum().reset_index()
                # Filter out groups with 0 or negative allocation for a cleaner pie chart
                bw_group_sum = bw_group_sum[bw_group_sum['BW Allocated'] > 0]

                if not bw_group_sum.empty:
                    try:
                        fig_pie = px.pie(bw_group_sum, names='BW Group', values='BW Allocated',
                                         title='Total Allocated BW by Group (Filtered Data)',
                                         hole=0.3) # Optional: makes it a donut chart
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating bandwidth allocation pie chart: {e}")
                else:
                    st.info("No positive allocated bandwidth data found for the selected groups to display in pie chart.")
            else:
                missing_cols = [col for col in pie_chart_cols if col not in filtered_df.columns]
                st.warning(f"❗ Chart not generated — column(s) missing: {missing_cols}")


        # --- Data Table (Not in Expander) ---
        st.subheader("📄 Filtered Data Preview")
        st.dataframe(filtered_df.head(100).fillna("N/A")) # Show preview, fill NaNs for display
        st.caption(f"Displaying first 100 rows of {len(filtered_df)} total filtered rows.")

    else: # if filtered_df is empty
         st.info("Select data using filters in the sidebar to view visualizations and data preview.")

# End: if not df.empty:

