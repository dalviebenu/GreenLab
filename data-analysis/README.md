# Linux Governors Analysis: Data Processing and Plot Generation

This part of the repository contains scripts and instructions for processing experimental data and generating visualizations to analyze the energy efficiency and performance of Linux CPU governors.

---

## Prerequisites

### Software Requirements
- **Python**: Version 3.7 or higher
  - Required libraries: `pandas`, `os`
- **R**: Version 4.0 or higher
  - Required libraries: `dplyr`, `ggplot2`, `tidyr`

---

## Step 1: Prepare the Data

### Experimental Setup
- The experiment generates CSV files for each of the 18 configurations (6 governors × 3 workloads) and 10 repetitions, producing 180 files per network type (small, medium, large). Across all network types, this results in 540 files.
- CSV files are named using the format: `run_X_repetition_Y.csv` (e.g., `run_0_repetition_0.csv`).

### Organizing the Data
1. Identify the 18 unique configurations (`governor-workload` combinations).
2. Rename the selected files using the format `governor-workload.csv` (e.g., `powersave-low.csv`, `performance-high.csv`).
3. Organize these 18 files into separate folders for each network type:
   - `small network/`
   - `medium network/`
   - `large network/`

---

## Step 2: Combine CSV Files Using the Python Script

The Python script cleans and combines the 18 unique CSV files into a single file for each network type.

### Usage
1. Place the renamed files into a folder (e.g., `small network/`, `medium network/`, `large network/`).
2. Update the Python script to specify the input folder and output file:
   ```python
   power_data_dir = "small network/"  # Change to 'medium network/' or 'large network/' for other networks
   output_file = "cleaned_power_data_small.csv"
   ```
3. Run the Python script:
   ```bash
   python datacombiner.py
   ```
4. The script outputs a cleaned combined file (e.g., `cleaned_power_data_small.csv`).

---

## Step 3: Generate Plots and Statistical Analysis Using the R Scripts

There are two R scripts. The first processes the combined CSV file and generates three types of plots:
- **Power Trends**: Visualizing power consumption over time.
- **CPU Utilization Trends**: Showing CPU utilization over time.
- **Energy Consumption Summary**: Summarizing energy consumption across governors and workloads.

### Usage First R Script (EDA.R)
1. Place the combined CSV files (`cleaned_power_data_small.csv`, etc.) in the same directory as the R script.
2. Update the R script to specify the input file and output folder:
   ```r
   input_file <- "cleaned_power_data_small.csv"  # Update for medium/large networks
   output_folder <- "plots/"
   ```
3. Run the R script:
   ```bash
   Rscript EDA.R
   ```
4. The script generates the following plot files:
   - `power_trends.png`
   - `cpu_trends.png`
   - `energy_consumption.png`

### Data Analysis by Second R Script
The second R script does hypothesis testing and allows for the creation of the scatter plots

### Usage Second R Script (Greenlab.R)
1. Change the data variable on line 215 to be either data_low, data_medium, or data_high based on what graph should be used (small/medium/large).
3. Run the R Script.
3. The hypothesis testing data and descriptive statistics can be found in output.txt in the Statistics folder, and the scatter plots are generated.

---
