# Load required libraries
library(tidyverse)
library(readr)
library(ggplot2)
library(car)
library(effsize)

# Function to read and preprocess CSV files
read_and_preprocess <- function(file_path) {
  read_csv(file_path) %>%
    mutate(across(c(`execution_time (seconds)`, cpu_usage, total_power, average_CPU_frequency), as.numeric))
}

# Read the CSV files
low_workload <- read_and_preprocess("run_table - low.csv")
med_workload <- read_and_preprocess("run_table - med.csv")
high_workload <- read_and_preprocess("run_table - high.csv")

# Combine the datasets
all_data <- bind_rows(
  low_workload %>% mutate(workload = "low"),
  med_workload %>% mutate(workload = "medium"),
  high_workload %>% mutate(workload = "high")
)

# Exploratory Data Analysis
summary(all_data)

# Visualizations
ggplot(all_data, aes(x = governor_type, y = total_power, fill = workload)) +
  geom_boxplot() +
  labs(title = "Total Power by Governor Type and Workload",
       x = "Governor Type", y = "Total Power")

ggplot(all_data, aes(x = governor_type, y = `execution_time (seconds)`, fill = workload)) +
  geom_boxplot() +
  labs(title = "Execution Time by Governor Type and Workload",
       x = "Governor Type", y = "Execution Time (seconds)")

# Function to perform ANOVA and pairwise comparisons
perform_analysis <- function(data, dependent_var) {
  formula <- as.formula(paste("`", dependent_var, "`", "~ governor_type", sep = ""))
  
  # ANOVA
  anova_result <- aov(formula, data = data)
  print(summary(anova_result))
  
  # Pairwise comparisons
  tukey_result <- TukeyHSD(anova_result)
  print(tukey_result)
  
  # Effect size (Cohen's d) for significant comparisons
  governor_types <- unique(data$governor_type)
  for (i in 1:(length(governor_types) - 1)) {
    for (j in (i + 1):length(governor_types)) {
      gov1 <- governor_types[i]
      gov2 <- governor_types[j]
      effect <- cohen.d(data[[dependent_var]][data$governor_type == gov1],
                        data[[dependent_var]][data$governor_type == gov2])
      cat(sprintf("Effect size (%s vs %s): %f\n", gov1, gov2, effect$estimate))
    }
  }
}

# RQ1: Energy Efficiency Analysis
cat("\nAnalysis for Energy Efficiency (Total Power):\n")
perform_analysis(all_data, "total_power")

# RQ2: Performance Analysis
cat("\nAnalysis for Performance (Execution Time):\n")
perform_analysis(all_data, "execution_time (seconds)")

# Additional analysis: CPU Usage and Average CPU Frequency
cat("\nAnalysis for CPU Usage:\n")
perform_analysis(all_data, "cpu_usage")

cat("\nAnalysis for Average CPU Frequency:\n")
perform_analysis(all_data, "average_CPU_frequency")

# Correlation analysis
cor_matrix <- cor(all_data[, c("execution_time (seconds)", "cpu_usage", "total_power", "average_CPU_frequency")])
print(cor_matrix)