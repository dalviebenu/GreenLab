import pandas as pd
import os

# Function to clean individual CSV files
def clean_power_data(file_path):
    try:
        # Load the CSV file
        power_data = pd.read_csv(file_path, on_bad_lines='skip')

        # Convert 'Date' column to datetime
        power_data['Date'] = pd.to_datetime(power_data['Date'], errors='coerce')

        # Drop rows with invalid or missing timestamps
        power_data = power_data.dropna(subset=['Date'])

        # Remove rows with negative 'Total Power'
        power_data = power_data[power_data['Total Power'] >= 0]

        # Add a 'Duration' column based on time from the start
        power_data['Duration'] = (power_data['Date'] - power_data['Date'].min()).dt.total_seconds()

        # Extract governor and workload from file name
        file_name = os.path.basename(file_path)
        governor, workload = file_name.replace(".csv", "").split(" - ")
        power_data['Governor'] = governor.strip()
        power_data['Workload'] = workload.strip()

        return power_data
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

# Function to clean and combine multiple CSV files
def clean_and_combine_power_data(file_paths, output_file):
    all_data = []

    for file_path in file_paths:
        cleaned_data = clean_power_data(file_path)
        if cleaned_data is not None:
            all_data.append(cleaned_data)

    # Combine all cleaned data into one DataFrame
    combined_data = pd.concat(all_data, ignore_index=True)

    # Save the combined data to a new CSV file
    combined_data.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

# Example usage
if __name__ == "__main__":
    # Define input files and output file
    power_data_dir = "high network/"
    power_data_paths = [os.path.join(power_data_dir, f) for f in os.listdir(power_data_dir) if f.endswith(".csv")]
    output_file = "cleaned_power_data_high.csv"

    # Clean and combine the data
    clean_and_combine_power_data(power_data_paths, output_file)
