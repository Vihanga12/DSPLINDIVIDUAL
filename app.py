# --- START OF FILE app.py ---

import streamlit as st
import pandas as pd
import plotly.express as px

# Load and clean data
@st.cache_data
def load_data(excel_file_path='/Users/vihanga/Downloads/DSPL_Individual_CW/preprocessed_data (76).xlsx'):
    """
    Loads data from the specified Excel file, cleans required columns,
    and attempts to find and standardize the 'Criteria 3' column name.

    Returns:
        tuple: (pandas.DataFrame, str or None)
               - The cleaned DataFrame.
               - The final column name used for Criteria 3, or None if not found/processed.
    """
    try:
        df = pd.read_excel(excel_file_path)
    except FileNotFoundError:
        st.error(f"Error: File not found at '{excel_file_path}'. Make sure the file is in the same directory as app.py.")
        return pd.DataFrame(), None # Return empty DataFrame and None for column name
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return pd.DataFrame(), None

    # --- Column Cleaning (Bandwidth) ---
    bandwidth_cols = [
        'BW Allocated', 'May Avg (Mbps)', 'May Max (Mbps)',
        'April Avg (Mbps)', 'April Max (Mbps)',
        'March Avg (Mbps)', 'March Max (Mbps)'
    ]
    for col in bandwidth_cols:
        if col in df.columns:
            # Convert to string first to handle potential non-string types before replace
            df[col] = df[col].astype(str).str.replace(' Mbps', '', regex=False).str.strip()
            # Use pd.to_numeric, errors='coerce' to handle non-convertible values
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            st.warning(f"Expected bandwidth column '{col}' not found in the Excel file.")

    # --- Column Cleaning (Site Value) ---
    site_value_col = 'Site Value (Rs.)****'
    if site_value_col in df.columns:
         # Convert to string first
        df[site_value_col] = df[site_value_col].astype(str).str.replace(',', '', regex=False).str.strip()
        df[site_value_col] = pd.to_numeric(df[site_value_col], errors='coerce')
    else:
        st.warning(f"Expected site value column '{site_value_col}' not found.")


    # --- Column Renaming and Criteria 3 Handling ---
    potential_criteria_3_names = [
        'Criteria 3 (BW Upgrade)***', 'Criteria 3 (BW Upgrade)**', 'Criteria 3 (BW Upgrade)*',
        'Criteria 3 BW Upgrade***', 'Criteria 3 BW Upgrade'
        # Add other potential variations from your actual Excel file here if needed
    ]
    target_criteria_1_name = 'Criteria 1 Max-C'
    target_criteria_2_name = 'Criteria 2 Avg-C'
    target_criteria_3_name = 'Criteria 3 BW Upgrade' # The desired clean name

    original_criteria_1_name = 'Criteria 1 (Max-C)*'
    original_criteria_2_name = 'Criteria 2 (Avg-C)**'

    # Find the actual original name for Criteria 3
    found_original_criteria_3_name = None
    for potential_name in potential_criteria_3_names:
        if potential_name in df.columns:
            found_original_criteria_3_name = potential_name
            break # Stop searching once found

    # Build the rename mapping dynamically based on found columns
    rename_mapping = {}
    if original_criteria_1_name in df.columns:
        rename_mapping[original_criteria_1_name] = target_criteria_1_name
    else:
         st.warning(f"Expected criteria column '{original_criteria_1_name}' not found.")

    if original_criteria_2_name in df.columns:
        rename_mapping[original_criteria_2_name] = target_criteria_2_name
    else:
        st.warning(f"Expected criteria column '{original_criteria_2_name}' not found.")

    # Add Criteria 3 to mapping ONLY if its original name was found
    if found_original_criteria_3_name:
        rename_mapping[found_original_criteria_3_name] = target_criteria_3_name

    # Apply all valid renames found
    if rename_mapping:
        df = df.rename(columns=rename_mapping)

    # --- Determine the final Criteria 3 column name to use ---
    final_criteria_3_col_name = None # Initialize
    if target_criteria_3_name in df.columns: # Check if the target name exists (rename successful)
        final_criteria_3_col_name = target_criteria_3_name
    elif found_original_criteria_3_name and found_original_criteria_3_name in df.columns: # Check if original still exists (rename failed but original was found)
        final_criteria_3_col_name = found_original_criteria_3_name
        st.warning(f"Could not properly rename '{found_original_criteria_3_name}' to '{target_criteria_3_name}'. Using original name for plotting.")
    elif not found_original_criteria_3_name: # If the original was never found in the first place
        st.error(f"Could not find a column matching potential names for 'Criteria 3 BW Upgrade' (e.g., {potential_criteria_3_names[0]}). Please check the Excel file's column headers.")
        # final_criteria_3_col_name remains None

    return df, final_criteria_3_col_name # Return DataFrame and the name to use


# --- Main App Logic ---

# Load data and get the correct column name for Criteria 3
df, criteria_3_col_name_for_plot = load_data('preprocessed_data (76).xlsx')

# Only proceed if data loading was successful (DataFrame is not empty)
if not df.empty:

    # Title and description
    st.title('Sri Lanka Site Bandwidth Dashboard')
    st.markdown('''
    This dashboard analyzes site bandwidth allocation and usage across months (March, April, May).
    Use the filters to explore performance by BW Group and individual sites.
    ''')

    # --- Sidebar filters ---
    st.sidebar.header('Filter Options')

    # BW Group Filter
    bw_groups_options = []
    if 'BW Group' in df.columns:
        # Convert to string and handle potential NaN values before getting unique/sorting
        bw_groups_options = sorted(df['BW Group'].astype(str).fillna('Unknown').unique())
    else:
        st.sidebar.warning("Column 'BW Group' not found for filtering.")

    bw_groups = st.sidebar.multiselect(
        'Select Bandwidth Groups:', options=bw_groups_options, default=bw_groups_options
    )

    # Site Name Filter
    sites_options = []
    if 'Site Name' in df.columns:
         # Convert to string and handle potential NaN values before getting unique/sorting
         sites_options = sorted(df['Site Name'].astype(str).fillna('Unknown').unique())
    else:
        st.sidebar.warning("Column 'Site Name' not found for filtering.")

    sites = st.sidebar.multiselect(
        'Select Sites:', options=sites_options, default=sites_options
    )

    # --- Apply filters safely ---
    filtered_df = df.copy()
    if 'BW Group' in filtered_df.columns and bw_groups:
        # Ensure filtering works even if filter list contains 'Unknown' from NaN handling
        filtered_df = filtered_df[filtered_df['BW Group'].astype(str).fillna('Unknown').isin(bw_groups)]
    if 'Site Name' in filtered_df.columns and sites:
        # Ensure filtering works even if filter list contains 'Unknown' from NaN handling
        filtered_df = filtered_df[filtered_df['Site Name'].astype(str).fillna('Unknown').isin(sites)]

    # Display warning if filtering resulted in empty dataframe
    if filtered_df.empty and not df.empty:
         st.warning("No data matches the current filter selections.")


    # --- Key Metrics ---
    st.subheader('Key Metrics')
    if not filtered_df.empty:
        col1, col2, col3 = st.columns(3)
        # Metric 1: Total Sites Selected
        if 'Site Name' in filtered_df.columns:
            col1.metric("Total Sites Selected", filtered_df['Site Name'].nunique())
        else:
            col1.metric("Total Sites Selected", "N/A")

        # Metric 2: Average May Usage
        avg_may_usage = None
        if 'May Avg (Mbps)' in filtered_df.columns and not filtered_df['May Avg (Mbps)'].isnull().all():
             avg_may_usage = filtered_df['May Avg (Mbps)'].mean()
        col2.metric("Avg May Usage (Mbps)", f"{avg_may_usage:.2f}" if avg_may_usage is not None else "N/A")

        # Metric 3: Average Allocated BW
        avg_allocated = None
        if 'BW Allocated' in filtered_df.columns and not filtered_df['BW Allocated'].isnull().all():
            avg_allocated = filtered_df['BW Allocated'].mean()
        col3.metric("Avg Allocated BW (Mbps)", f"{avg_allocated:.2f}" if avg_allocated is not None else "N/A")
    else:
        # Display placeholder metrics if filtered_df is empty
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sites Selected", 0)
        col2.metric("Avg May Usage (Mbps)", "N/A")
        col3.metric("Avg Allocated BW (Mbps)", "N/A")


    # --- Visualizations ---

    # Check if filtered_df is empty before attempting plots
    if not filtered_df.empty:

        # -- Monthly Average Usage Bar Chart --
        st.subheader('Average Bandwidth Usage per Month')
        monthly_avg_cols = ['Site Name', 'March Avg (Mbps)', 'April Avg (Mbps)', 'May Avg (Mbps)']
        if all(col in filtered_df.columns for col in monthly_avg_cols):
            monthly_avg = filtered_df[monthly_avg_cols].copy()
            monthly_avg.dropna(subset=monthly_avg_cols[1:], how='all', inplace=True) # Drop if all avg values are NaN
            monthly_avg.dropna(subset=['Site Name'], inplace=True) # Drop if Site Name is NaN

            if not monthly_avg.empty:
                try:
                    monthly_avg_melted = monthly_avg.melt(id_vars='Site Name', var_name='Month', value_name='Avg Mbps')
                    # Ensure 'Avg Mbps' is numeric for plotting, coerce errors to NaN
                    monthly_avg_melted['Avg Mbps'] = pd.to_numeric(monthly_avg_melted['Avg Mbps'], errors='coerce')
                    monthly_avg_melted.dropna(subset=['Avg Mbps'], inplace=True) # Drop rows where conversion failed

                    if not monthly_avg_melted.empty:
                        fig1 = px.bar(
                            monthly_avg_melted, x='Site Name', y='Avg Mbps', color='Month',
                            barmode='group', title='Monthly Average Bandwidth Usage per Site'
                        )
                        fig1.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("No numeric average bandwidth data available to plot for the selected sites and months.")
                except Exception as e:
                    st.error(f"Error creating monthly usage chart: {e}")
            else:
                st.info("No data available for Monthly Average Usage plot for the current selection after cleaning.")
        else:
            # Provide more specific feedback on missing columns
            missing_monthly_cols = [col for col in monthly_avg_cols if col not in filtered_df.columns]
            st.warning(f"One or more required columns missing for Monthly Average Usage plot. Missing: {missing_monthly_cols}")


        # -- Criteria-based Scatter Plot --
        st.subheader('Criteria Analysis')
        if criteria_3_col_name_for_plot: # Check if Criteria 3 name was determined
            scatter_cols = ['Criteria 1 Max-C', 'Criteria 2 Avg-C', criteria_3_col_name_for_plot, 'Site Name', 'BW Allocated']
            if all(col in filtered_df.columns for col in scatter_cols):
                # Drop rows where any of the essential plot columns are NaN
                scatter_df = filtered_df.dropna(subset=['Criteria 1 Max-C', 'Criteria 2 Avg-C', criteria_3_col_name_for_plot]).copy()

                if not scatter_df.empty:
                    # Convert color column to string for discrete coloring, handle potential mixed types safely
                    scatter_df[criteria_3_col_name_for_plot] = scatter_df[criteria_3_col_name_for_plot].astype(str)
                    try:
                        fig2 = px.scatter(
                            scatter_df, x='Criteria 1 Max-C', y='Criteria 2 Avg-C', color=criteria_3_col_name_for_plot,
                            hover_data=['Site Name', 'BW Allocated'], title=f'Criteria 1 vs Criteria 2 (Color: {criteria_3_col_name_for_plot})'
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating criteria scatter plot: {e}")
                else:
                    st.info("No data available for Criteria Analysis scatter plot after filtering/cleaning.")
            else:
                # Provide more specific feedback on missing columns
                missing_scatter_cols = [col for col in scatter_cols if col not in filtered_df.columns]
                st.warning(f"One or more required columns missing for Criteria Analysis plot. Missing: {missing_scatter_cols}.")
        else:
            st.warning("Criteria 3 column could not be identified, skipping Criteria Analysis plot.")


        # -- Site Value Box Plot --
        st.subheader('Site Value Analysis')
        site_value_col_plot = 'Site Value (Rs.)****' # Using the original name as defined in cleaning
        box_plot_cols = ['BW Group', site_value_col_plot]
        if all(col in filtered_df.columns for col in box_plot_cols):
            # Drop rows where the value or group column is NaN
            box_df = filtered_df.dropna(subset=[site_value_col_plot, 'BW Group']).copy()

            if not box_df.empty:
                # Convert BW Group to string to ensure discrete categories for the plot
                box_df['BW Group'] = box_df['BW Group'].astype(str)
                try:
                    fig3 = px.box(
                        box_df, x='BW Group', y=site_value_col_plot, title='Site Value Distribution across BW Groups'
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating site value box plot: {e}")
            else:
                st.info("No data available for Site Value Analysis box plot after filtering/cleaning.")
        else:
             missing_box_cols = [col for col in box_plot_cols if col not in filtered_df.columns]
             st.warning(f"One or more required columns missing for Site Value Analysis plot. Missing: {missing_box_cols}")


        # --- Chart 3: Pie Chart (BW Group Share) ---
        st.subheader('Bandwidth Allocation Share by Group')
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
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label', sort=False) # Keep original order if desired
                    st.plotly_chart(fig_pie, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating bandwidth allocation pie chart: {e}")
            else:
                st.info("No positive allocated bandwidth data found for the selected groups to display in pie chart.")
        else:
            missing_pie_cols = [col for col in pie_chart_cols if col not in filtered_df.columns]
            st.warning(f"One or more required columns missing for Bandwidth Allocation Pie Chart. Missing: {missing_pie_cols}")


        # --- Chart 4: Heatmap (Usage Across Sites and Months) ---
        st.subheader('Monthly Average Usage Heatmap')
        heatmap_cols = ['Site Name', 'March Avg (Mbps)', 'April Avg (Mbps)', 'May Avg (Mbps)']
        if all(col in filtered_df.columns for col in heatmap_cols):
            # Select relevant columns and drop rows where Site Name is missing
            heatmap_df_prep = filtered_df[heatmap_cols].dropna(subset=['Site Name']).copy()

            # Ensure month columns are numeric before grouping, coerce errors
            for col in heatmap_cols[1:]:
                 heatmap_df_prep[col] = pd.to_numeric(heatmap_df_prep[col], errors='coerce')

            # Handle potential duplicate Site Names by averaging usage for duplicates
            # Group by Site Name (as string, handling NaNs) and calculate mean, reset index to keep Site Name as column
            heatmap_df = heatmap_df_prep.groupby(heatmap_df_prep['Site Name'].astype(str).fillna('Unknown')).mean().reset_index()

            # Drop rows where all month averages are NaN *after* grouping
            heatmap_df.dropna(subset=heatmap_cols[1:], how='all', inplace=True)

            if not heatmap_df.empty:
                # Set Site Name as index for the heatmap *after* cleaning and aggregation
                heatmap_df = heatmap_df.set_index('Site Name')
                try:
                    # Limit number of sites displayed if too many, to avoid browser freeze
                    max_sites_heatmap = 50
                    if len(heatmap_df) > max_sites_heatmap:
                         st.info(f"Heatmap truncated to the top {max_sites_heatmap} sites by May average usage due to large number of sites.")
                         # Sort by May usage and take top N (optional, or just take head)
                         heatmap_df_display = heatmap_df.sort_values(by='May Avg (Mbps)', ascending=False).head(max_sites_heatmap)
                    else:
                         heatmap_df_display = heatmap_df

                    fig_heatmap = px.imshow(heatmap_df_display,
                                            text_auto=".1f", # Format text labels to 1 decimal place
                                            aspect='auto',
                                            color_continuous_scale='Blues', # Example color scale
                                            title='Average Monthly Usage (Mbps) per Site (Filtered Data)',
                                            labels={'color': 'Avg Mbps'}) # Label for the color bar
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating usage heatmap: {e}")
            else:
                st.info("No data available to display usage heatmap for the current selection after aggregation.")
        else:
             missing_heatmap_cols = [col for col in heatmap_cols if col not in filtered_df.columns]
             st.warning(f"One or more required columns missing for Usage Heatmap. Missing: {missing_heatmap_cols}")


        # --- Dataframe view ---
        st.subheader('Filtered Data Preview')
        # Display the head of the filtered dataframe, handling potential NaNs gracefully for display
        st.dataframe(filtered_df.head(100).fillna('N/A'))
        st.caption(f"Displaying first 100 rows of {len(filtered_df)} total filtered rows.")

    # End of check for `if not filtered_df.empty:` for plots

elif df is None: # Check if load_data returned None explicitly due to load error
    st.error("Application cannot start because data loading failed. Please check terminal or previous error messages for details.")
# If df is empty but not None, the error was shown in load_data or the filter warning was shown.

# --- END OF FILE app.py ---