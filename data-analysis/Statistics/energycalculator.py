import pandas as pd
from scipy.integrate import trapezoid

def clean_and_calculate_energy(file_path):
    """
    Cleans the power output file and calculates energy using the trapezoid rule.

    Parameters:
        file_path (str): Path to the power output CSV file.

    Returns:
        float: Calculated energy in Joules.
    """
    try:
        # Step 1: Load the data, ignoring bad lines
        data = pd.read_csv(file_path, error_bad_lines=False, warn_bad_lines=True)

        # Step 2: Clean the 'Date' column
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

        # Remove rows with invalid dates
        data = data.dropna(subset=['Date'])

        # Ensure 'Date' is sorted
        data = data.sort_values(by='Date')

        # Step 3: Remove negative values from 'Total Power'
        if 'Total Power' not in data.columns:
            raise ValueError("The required 'Total Power' column is missing in the dataset.")
        
        data = data[data['Total Power'] >= 0]

        # Step 4: Calculate energy using the trapezoid rule
        if len(data) < 2:
            raise ValueError("Insufficient data points to calculate energy.")

        # Calculate time differences in seconds
        data['Time Diff'] = (data['Date'] - data['Date'].iloc[0]).dt.total_seconds()

        # Compute energy
        energy = trapezoid(data['Total Power'], data['Time Diff'])

        return energy

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


file_path = "path_to_power_output.csv"
energy = clean_and_calculate_energy(file_path)
print(f"Calculated Energy: {energy} Joules")
