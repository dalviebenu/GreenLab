# R Script for Preprocessing and Plotting

# Load required libraries
library(dplyr)
library(ggplot2)
library(tidyr)

# ========================= Preprocessing the Run Table =========================
clean_run_table <- function(run_table_path) {
  # Read the CSV file
  run_table <- read.csv(run_table_path, stringsAsFactors = FALSE)
  
  # Remove any white spaces from governor and workload types
  run_table <- run_table %>% 
    mutate(
      governor_type = trimws(governor_type),
      workload_type = trimws(workload_type)
    )
  
  # Ensure only valid governor types (6 unique values)
  valid_governors <- c("conservative", "ondemand", "performance", "powersave", "schedutil", "userspace")
  run_table <- run_table %>% filter(governor_type %in% valid_governors)
  
  # Ensure only valid workload types (3 unique values: low, medium, high)
  valid_workloads <- c("low", "medium", "high")
  run_table <- run_table %>% filter(workload_type %in% valid_workloads)
  
  # Return the cleaned run table
  return(run_table)
}

# ========================= Preprocessing the Power Data =========================
clean_power_data <- function(power_data_paths) {
  # Initialize an empty list to hold cleaned data
  cleaned_data_list <- list()
  
  # Iterate over all file paths
  for (file_path in power_data_paths) {
    # Read the CSV file
    power_data <- read.csv(file_path, stringsAsFactors = FALSE)
    
    # Convert Date column to POSIXct format
    power_data$Date <- as.POSIXct(power_data$Date, format = "%Y-%m-%d %H:%M:%S", tz = "UTC")
    
    # Remove rows with invalid or missing timestamps
    power_data <- power_data %>% filter(!is.na(Date))
    
    # Coerce columns to appropriate types
    power_data$CPU.Power <- as.numeric(power_data$CPU.Power) # Convert CPU.Power to numeric
    power_data$GPU.Power <- as.numeric(power_data$GPU.Power) # Convert GPU.Power to numeric
    
    # Calculate duration from the start of each repetition
    power_data <- power_data %>% mutate(Duration = as.numeric(difftime(Date, min(Date), units = "secs")))
    
    # Remove rows with negative or invalid Total Power
    power_data <- power_data %>% filter(Total.Power >= 0)
    
    # Add governor and workload information from the file name
    file_info <- strsplit(basename(file_path), " - ")[[1]]
    power_data$Governor <- trimws(file_info[1])
    power_data$Workload <- trimws(gsub(".csv", "", file_info[2]))
    
    # Append the cleaned data to the list
    cleaned_data_list[[length(cleaned_data_list) + 1]] <- power_data
  }
  
  # Combine all cleaned data into a single data frame
  combined_data <- bind_rows(cleaned_data_list)
  
  # Return the combined cleaned data
  return(combined_data)
}

# ========================= Plotting Functions =========================
plot_power_trends <- function(cleaned_data, title) {
  ggplot(cleaned_data, aes(x = Duration, y = Total.Power, color = Governor, linetype = Workload)) +
    geom_line() +
    labs(
      title = title,
      x = "Duration (Seconds)",
      y = "Total Power (Watts)",
      color = "Governor",
      linetype = "Workload"
    ) +
    theme_minimal() +
    theme(legend.position = "right")
}

plot_cpu_trends <- function(cleaned_data, title) {
  ggplot(cleaned_data, aes(x = Duration, y = CPU.Utilization * 100, color = Governor, linetype = Workload)) +
    geom_line() +
    labs(
      title = title,
      x = "Duration (Seconds)",
      y = "CPU Utilization (%)",
      color = "Governor",
      linetype = "Workload"
    ) +
    theme_minimal() +
    theme(legend.position = "right")
}

plot_energy_consumption <- function(cleaned_data, title) {
  energy_summary <- cleaned_data %>%
    group_by(Governor, Workload) %>%
    summarise(Average_Energy = mean(Total.Power, na.rm = TRUE))
  
  ggplot(energy_summary, aes(x = Governor, y = Average_Energy, fill = Workload)) +
    geom_bar(stat = "identity", position = "dodge") +
    labs(
      title = title,
      x = "Governor",
      y = "Average Energy Consumption (Watts)",
      fill = "Workload"
    ) +
    theme_minimal() +
    theme(legend.position = "right")
}

# ========================= Main Script =========================
# Paths to the run table and power data
run_table_path <- "run_table - low.csv"
power_data_dir <- "low network/"
power_data_paths <- list.files(power_data_dir, pattern = "*.csv", full.names = TRUE)

# Clean the run table
cleaned_run_table <- clean_run_table(run_table_path)

# Clean and combine all power data
all_power_data <- clean_power_data(power_data_paths)

# Generate Power Trend Plot
power_plot <- plot_power_trends(all_power_data, "Power Consumption Over Experiment Duration")
print(power_plot)

# Generate CPU Utilization Trend Plot
cpu_plot <- plot_cpu_trends(all_power_data, "CPU Utilization Over Experiment Duration")
print(cpu_plot)

# Generate Energy Consumption Plot
energy_plot <- plot_energy_consumption(all_power_data, "Average Energy Consumption by Governor and Workload")
print(energy_plot)

# Save plots if needed
ggsave("power_trends.png", power_plot, width = 12, height = 8)
ggsave("cpu_trends.png", cpu_plot, width = 12, height = 8)
ggsave("energy_consumption.png", energy_plot, width = 12, height = 8)
