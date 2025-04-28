

import streamlit as st
import pandas as pd
import plotly.express as px

# Load and clean data
@st.cache_data
def load_data(excel_file_path='preprocessed_data (76).xlsx'):
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

    #Column Cleaning
    bandwidth_cols = [
        'BW Allocated', 'May Avg (Mbps)', 'May Max (Mbps)',
        'April Avg (Mbps)', 'April Max (Mbps)',
        'March Avg (Mbps)', 'March Max (Mbps)'
    ]
    for col in bandwidth_cols:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(' Mbps', '', regex=False)
                .str.strip()
                .pipe(pd.to_numeric, errors='coerce') # Convert to numeric, non-convertible become NaN
            )
        else:
            st.warning(f"Expected bandwidth column '{col}' not found in the Excel file.")

    # Column Cleaning (Site Value)
    site_value_col = 'Site Value (Rs.)****'
    if site_value_col in df.columns:
        df[site_value_col] = (
            df[site_value_col]
            .astype(str)
            .str.replace(',', '', regex=False)
            .str.strip()
            .pipe(pd.to_numeric, errors='coerce')
        )
    else:
        st.warning(f"Expected site value column '{site_value_col}' not found.")


    #Column Renaming 

    # Define potential original names for Criteria 3 (add more if needed)
    potential_criteria_3_names = [
        'Criteria 3 (BW Upgrade)***',
        'Criteria 3 (BW Upgrade)**',
        'Criteria 3 (BW Upgrade)*',
        'Criteria 3 BW Upgrade***',
        'Criteria 3 BW Upgrade',
        # Add other variations you might suspect exist in the file
    ]


    target_criteria_1_name = 'Criteria 1 Max-C'
    target_criteria_2_name = 'Criteria 2 Avg-C'
    target_criteria_3_name = 'Criteria 3 BW Upgrade' # Use a clean target name

    # Find the actual original names present in the DataFrame
    original_criteria_1_name = 'Criteria 1 (Max-C)*' # Assuming this one is stable
    original_criteria_2_name = 'Criteria 2 (Avg-C)**' # Assuming this one is stable
    found_original_criteria_3_name = None
    for potential_name in potential_criteria_3_names:
        if potential_name in df.columns:
            found_original_criteria_3_name = potential_name
            break # Stop searching once found

    # Build the rename mapping only for columns that exist
    rename_mapping = {}
    if original_criteria_1_name in df.columns:
        rename_mapping[original_criteria_1_name] = target_criteria_1_name
    else:
         st.warning(f"Expected criteria column '{original_criteria_1_name}' not found.")

    if original_criteria_2_name in df.columns:
        rename_mapping[original_criteria_2_name] = target_criteria_2_name
    else:
        st.warning(f"Expected criteria column '{original_criteria_2_name}' not found.")

    if found_original_criteria_3_name:
        rename_mapping[found_original_criteria_3_name] = target_criteria_3_name
    else:
        # If none of the potential names were found, we cannot proceed with Criteria 3
        st.error(f"Could not find a column matching potential names for 'Criteria 3 BW Upgrade' (e.g., {potential_criteria_3_names[0]}). Please check the Excel file's column headers.")
        # We still return the DataFrame for other potential uses, but None for the col name
        if rename_mapping: # Apply other renames if they exist
             df = df.rename(columns=rename_mapping)
        return df, None


    # Apply the renaming
    if rename_mapping:
        df = df.rename(columns=rename_mapping)

    # --- Determine the final Criteria 3 column name to use ---
    # After attempting rename, check if the target name exists.
    # If not, fall back to the original name that was found (in case rename failed silently).
    final_criteria_3_col_name = None
    if target_criteria_3_name in df.columns:
        final_criteria_3_col_name = target_criteria_3_name
    elif found_original_criteria_3_name in df.columns: # Check if original still exists
        final_criteria_3_col_name = found_original_criteria_3_name
        st.warning(f"Could not rename '{found_original_criteria_3_name}' to '{target_criteria_3_name}'. Using original name.")
    # If neither exists after the process, something is fundamentally wrong (handled by the earlier error)

    return df, final_criteria_3_col_name # Return DataFrame and the name to use

# --- Main App Logic ---

# Load data and get the correct column name for Criteria 3
# Provide the path to your file here if it's not in the same directory
df, criteria_3_col_name_for_plot = load_data('preprocessed_data (76).xlsx')

# Only proceed if data loading was successful
if not df.empty:

    # Title and description
    st.title('Sri Lanka Site Bandwidth Dashboard')
    st.markdown('''
    This dashboard analyzes site bandwidth allocation and usage across months (March, April, May).
    Use the filters to explore performance by BW Group and individual sites.
    ''')

    st.sidebar.header('Filter Options')

    # Check if filter columns exist before creating widgets
    bw_groups_options = []
    if 'BW Group' in df.columns:
        bw_groups_options = sorted(df['BW Group'].astype(str).unique())
    else:
        st.sidebar.warning("Column 'BW Group' not found for filtering.")

    bw_groups = st.sidebar.multiselect(
        'Select Bandwidth Groups:',
        options=bw_groups_options,
        default=bw_groups_options # Select all by default
    )

    sites_options = []
    if 'Site Name' in df.columns:
         sites_options = sorted(df['Site Name'].astype(str).unique())
    else:
        st.sidebar.warning("Column 'Site Name' not found for filtering.")

    sites = st.sidebar.multiselect(
        'Select Sites:',
        options=sites_options,
        default=sites_options # Select all by default
    )


    filtered_df = df.copy() # Start with a copy

    # Apply BW Group filter only if the column exists and selections were made
    if 'BW Group' in filtered_df.columns and bw_groups:
        filtered_df = filtered_df[filtered_df['BW Group'].isin(bw_groups)]

    # Apply Site Name filter only if the column exists and selections were made
    if 'Site Name' in filtered_df.columns and sites:
        filtered_df = filtered_df[filtered_df['Site Name'].isin(sites)]

    # Handle case where filtering results in an empty DataFrame
    if filtered_df.empty and not df.empty: # Check if filtering caused emptiness
         st.warning("No data matches the current filter selections.")


    st.subheader('Key Metrics')
    col1, col2, col3 = st.columns(3)

    if 'Site Name' in filtered_df.columns:
        col1.metric("Total Sites Selected", filtered_df['Site Name'].nunique())
    else:
        col1.metric("Total Sites Selected", "N/A")

    avg_may_usage = filtered_df['May Avg (Mbps)'].mean() if 'May Avg (Mbps)' in filtered_df.columns and not filtered_df['May Avg (Mbps)'].isnull().all() else None
    col2.metric("Avg May Usage (Mbps)", f"{avg_may_usage:.2f}" if avg_may_usage is not None else "N/A")

    avg_allocated = filtered_df['BW Allocated'].mean() if 'BW Allocated' in filtered_df.columns and not filtered_df['BW Allocated'].isnull().all() else None
    col3.metric("Avg Allocated BW (Mbps)", f"{avg_allocated:.2f}" if avg_allocated is not None else "N/A")




    #Monthly Average Usage Bar Chart 
    st.subheader('Average Bandwidth Usage per Month')
    monthly_avg_cols = ['Site Name', 'March Avg (Mbps)', 'April Avg (Mbps)', 'May Avg (Mbps)']
    if all(col in filtered_df.columns for col in monthly_avg_cols):
        monthly_avg = filtered_df[monthly_avg_cols].copy()
        # Drop rows where all avg usage values are NaN to avoid issues with melt/plotting
        monthly_avg.dropna(subset=monthly_avg_cols[1:], how='all', inplace=True)

        if not monthly_avg.empty:
            try:
                monthly_avg_melted = monthly_avg.melt(id_vars='Site Name', var_name='Month', value_name='Avg Mbps')
                # Ensure 'Avg Mbps' is numeric for plotting
                monthly_avg_melted['Avg Mbps'] = pd.to_numeric(monthly_avg_melted['Avg Mbps'], errors='coerce')
                monthly_avg_melted.dropna(subset=['Avg Mbps'], inplace=True) # Drop rows where conversion failed

                if not monthly_avg_melted.empty:
                    fig1 = px.bar(
                        monthly_avg_melted,
                        x='Site Name',
                        y='Avg Mbps',
                        color='Month',
                        barmode='group',
                        title='Monthly Average Bandwidth Usage per Site'
                    )
                    fig1.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("No numeric average bandwidth data available for the selected sites and months.")

            except Exception as e:
                st.error(f"Error creating monthly usage chart: {e}")
        else:
            st.info("No data available for Monthly Average Bandwidth Usage plot for the current selection.")
    else:
        st.warning(f"One or more required columns missing for Monthly Average Usage plot: {monthly_avg_cols}")


    #Criteria-based Scatter Plot 
    st.subheader('Criteria Analysis')
    # Check if Criteria 3 column name was successfully identified
    if criteria_3_col_name_for_plot:
        scatter_cols = ['Criteria 1 Max-C', 'Criteria 2 Avg-C', criteria_3_col_name_for_plot, 'Site Name', 'BW Allocated']
        if all(col in filtered_df.columns for col in scatter_cols):
            # Drop rows where any of the essential plot columns are NaN
            scatter_df = filtered_df.dropna(subset=['Criteria 1 Max-C', 'Criteria 2 Avg-C', criteria_3_col_name_for_plot]).copy()

            # Convert color column to string for discrete coloring if it's not already, handles mixes
            scatter_df[criteria_3_col_name_for_plot] = scatter_df[criteria_3_col_name_for_plot].astype(str)


            if not scatter_df.empty:
                try:
                    fig2 = px.scatter(
                        scatter_df,
                        x='Criteria 1 Max-C',
                        y='Criteria 2 Avg-C',
                        color=criteria_3_col_name_for_plot, # Use the determined column name
                        hover_data=['Site Name', 'BW Allocated'],
                        title=f'Criteria 1 vs Criteria 2 (Color: {criteria_3_col_name_for_plot})' # Dynamic title
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                except Exception as e:
                     st.error(f"Error creating criteria scatter plot: {e}")
            else:
                st.info("No data available for Criteria Analysis scatter plot after filtering/cleaning.")
        else:
            st.warning(f"One or more required columns missing for Criteria Analysis plot. Needed: {scatter_cols}. Available: {list(filtered_df.columns)}")
    else:
        st.warning("Criteria 3 column could not be identified, skipping Criteria Analysis plot.")


    # Site Value Box Plot 
    st.subheader('Site Value Analysis')
    # Use the original name as defined in cleaning section, as it wasn't renamed
    site_value_col_plot = 'Site Value (Rs.)****'
    box_plot_cols = ['BW Group', site_value_col_plot]
    if all(col in filtered_df.columns for col in box_plot_cols):
        box_df = filtered_df.dropna(subset=[site_value_col_plot, 'BW Group']).copy()
         # Convert BW Group to string to ensure discrete categories
        box_df['BW Group'] = box_df['BW Group'].astype(str)

        if not box_df.empty:
             try:
                 fig3 = px.box(
                     box_df,
                     x='BW Group',
                     y=site_value_col_plot,
                     title='Site Value Distribution across BW Groups'
                 )
                 st.plotly_chart(fig3, use_container_width=True)
             except Exception as e:
                 st.error(f"Error creating site value box plot: {e}")
        else:
             st.info("No data available for Site Value Analysis box plot after filtering/cleaning.")
    else:
        st.warning(f"One or more required columns missing for Site Value Analysis plot. Needed: {box_plot_cols}")


    #Dataframe view
    st.subheader('Filtered Data Preview')
    # Show limited rows for preview, handle NaNs for display
    st.dataframe(filtered_df.head(100).fillna('N/A'))
    st.caption(f"Displaying first 100 rows of {len(filtered_df)} total filtered rows.")

elif df is None: # Check if load_data returned None explicitly due to load error
    st.error("Application cannot start because data loading failed. Please check terminal or previous messages for details.")
# No 'else' needed here if df is empty but not None, as load_data would have shown the error
