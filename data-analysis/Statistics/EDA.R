# Combined R Script for Preprocessing and Plotting

# Load required libraries
library(dplyr)
library(ggplot2)
library(tidyr)

# ========================= Preprocessing the Run Table =========================
clean_run_table <- function(run_table_data_path) {
  # Read the CSV file
  run_table <- read.csv(run_table_data_path, stringsAsFactors = FALSE)

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
    theme(
      panel.background = element_rect(fill = "white"),
      plot.background = element_rect(fill = "white"),
      legend.position = "right"
    )
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
    theme(
      panel.background = element_rect(fill = "white"),
      plot.background = element_rect(fill = "white"),
      legend.position = "right"
    )
}

# Accurate Energy Consumption Bar Chart
plot_energy_consumption <- function(cleaned_data, title) {
  energy_summary <- cleaned_data %>%
    group_by(governor_type, workload_type) %>%
    summarise(Average_Energy = mean(energy..Joules., na.rm = TRUE))

  ggplot(energy_summary, aes(x = governor_type, y = Average_Energy, fill = workload_type)) +
    geom_bar(stat = "identity", position = position_dodge(width = 0.8)) +
    geom_text(aes(label = round(Average_Energy, 1)), 
              position = position_dodge(width = 0.8), 
              vjust = -0.5, size = 3) +
    labs(
      title = title,
      x = "Governor",
      y = "Average Energy Consumption (Joules)",
      fill = "Workload Type"
    ) +
    theme_minimal(base_size = 14) +
    theme(
      panel.background = element_rect(fill = "white"),
      plot.background = element_rect(fill = "white", color = NA),
      legend.position = "right",
      plot.title = element_text(hjust = 0.5, size = 16)
    )
}

# ========================= Main Script =========================
# Paths to the cleaned power data and run table data
cleaned_power_data_path <- "cleaned_power_data.csv"  # Path to your cleaned power data
run_table_data_path <- "run_table - low.csv" # Path to your run table data

# Load the cleaned power data directly
all_power_data <- read.csv(cleaned_power_data_path, stringsAsFactors = FALSE)

# Load the run table data
run_table_data <- read.csv(run_table_data_path, stringsAsFactors = FALSE)

# Clean the run table data
run_table_data <- clean_run_table(run_table_data_path)

# Generate Power Trend Plot
power_plot <- plot_power_trends(all_power_data, "Power Consumption Over Experiment Duration") +
  theme(text = element_text(size = 14),  # Increase text size
        plot.title = element_text(hjust = 0.5, size = 16),  # Center title and increase size
        legend.position = "right")  # Position legend to the right
print(power_plot)

# Generate CPU Utilization Trend Plot
cpu_plot <- plot_cpu_trends(all_power_data, "CPU Utilization Over Experiment Duration") +
  theme(text = element_text(size = 14),  # Increase text size
        plot.title = element_text(hjust = 0.5, size = 16),  # Center title and increase size
        legend.position = "right")  # Position legend to the right
print(cpu_plot)

# Generate Energy Consumption Bar Chart
energy_plot <- plot_energy_consumption(run_table_data, "Average Energy Consumption by Governor and Workload")
print(energy_plot)

# Save plots with improved dimensions for visibility
ggsave("power_trends.png", power_plot, width = 14, height = 10)
ggsave("cpu_trends.png", cpu_plot, width = 14, height = 10)
ggsave("energy_consumption.png", energy_plot, width = 14, height = 10, dpi = 300)