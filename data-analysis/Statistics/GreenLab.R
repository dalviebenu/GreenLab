
#install.packages("devtools")
#devtools::install_github("hrbrmstr/hrbrthemes")

# Load necessary libraries
library(ggplot2)
library(dplyr)
library(stats)
library(hrbrthemes)
library(readr)


set.seed(0)

showDescriptiveStatistics <- function(data) {
  
  dataSummary <- summary(data)
  print("Descriptive Statistics: ")
  print(dataSummary)
}

isShapiroWilk <- function(sample1, sample2, alpha = 0.05) {
  
  shapiro1 <- shapiro.test(sample1)
  shapiro2 <- shapiro.test(sample2)
  
  cat("Shapiro-Wilk Test Value for sample1 = ", shapiro1$p.value, "\n")
  cat("Shapiro-Wilk Test Value for sample2 = ", shapiro2$p.value, "\n")
  
  return(shapiro1$p.value > alpha && shapiro2$p.value > alpha)
}

getSample <- function(data, column, condition) {
  
  filteredDf <- data[with(data, eval(condition)), column, drop = FALSE]
  sample <- filteredDf[[column]]
  return(sample)
}

filterData <- function(data, column, filterConditions){
  filteredData <- data
  for(filterColumn in names(filterConditions)) {
    filterValue <- filterConditions[[filterColumn]]
    filteredData <- filteredData %>% filter(filterColumn == filterValue)
  }
  return(filteredData$column)
}

isSampleEqual <- function(sample1, sample2, governor, metric, workload){
  
  isNormalityAssumed = isShapiroWilk(sample1, sample2)
  shapiro1 = shapiro.test(sample1)
  
  W = "None"
  t = "None"
  p = 0
  
  alpha = 0.05
  
  if(isNormalityAssumed) {
    ttest1 <- NormalityAssumed(sample1, sample2)
    p = ttest1$p.value
    rejectHypothesis <- ttest1$p.value < alpha
    t = ttest1$statistic
  }
  else {
    wilcox1 <- NormalityNotAssumed(sample1, sample2)
    p = wilcox1$p.value
    rejectHypothesis <- p < alpha
    W = wilcox1$statistic
  }
  
  if(rejectHypothesis) {
    print("The samples are statistically different and the null-hypothesis is rejected")
  }
  else {
    print("The samples are statistically equal and the null-hypothesis is accepted")
  }
  
  row_data <- matrix(c(governor, workload, metric, mean(sample1), median(sample1), sd(sample1), 
                       min(sample1), max(sample1), max(sample1) - min(sample1), 
                       shapiro1$statistic, shapiro1$p.value, isNormalityAssumed,
                       t, W, p, rejectHypothesis), nrow = 1)
  
  write.table(row_data, "output.csv", sep = ",", col.names = FALSE, row.names = FALSE, quote = FALSE, append = TRUE)
}

NormalityAssumed <- function(sample1, sample2){
  
  if (length(sample1) != length(sample2)) {
    stop("Length of samples must be equal")
  }
  ttest1 = t.test(sample1, sample2, paired = TRUE)
  
  return(ttest1)
}

NormalityNotAssumed <- function(sample1, sample2){
  if (length(sample1) != length(sample2)) {
    stop("Length of samples must be equal")
  }
  wilcox1 = wilcox.test(sample1, sample2, paired = TRUE)
  
  return(wilcox1)
}

doExperiment <- function(governors, workload_types, data) {
  header_values <- c("Governor", "Workload", "Metric", "Mean", "Median", "Standard Deviation", 
                     "Min", "Max", "Range", "W Stat (Norm)", "p-Val (Norm)", " Is Normality Assumed", 
                     "t Stat (Hypo)", "W Stat (Hypo)", "p-Val (Hypo)", "Is Hypothesis Rejected")
  header_row <- matrix(header_values, nrow = 1)

  write.table(header_row, "output.csv", sep = ",", col.names = FALSE, row.names = FALSE, quote = FALSE)
  
  for (governor in governors) {
    for(workload in workload_types) {
      cat("========================= For governor:", governor, "and workload:", workload, "=========================")
      condition1 <- substitute(
        governor_type == governor & workload_type == workload
      )
      
      condition2 <- substitute(
        governor_type == "powersave" & workload_type == workload
      )
      
      sample1 = getSample(data, "energy", condition1)
      sample2 = getSample(data, "energy", condition2)
      
      showDescriptiveStatistics(sample1)
      
      isSampleEqual(sample1, sample2, governor, "Energy Consumption (J)", workload)
      
      sample3 = getSample(data, "cpu_usage", condition1)
      sample4 = getSample(data, "cpu_usage", condition2)
      
      showDescriptiveStatistics(sample3)
      
      isSampleEqual(sample3, sample4, governor, "CPU Usage", workload)
    }
  }
}

addPowersaveData <- function(data, workloads) {
  for(workload in workloads) {
    condition <- substitute(
      governor_type == "powersave" & workload_type == workload
    )
    alpha = 0.05
    
    sample1 <- getSample(data, "energy", condition)
    shapiro1 <- shapiro.test(sample1)
    isNormalityAssumed = shapiro1$p.value > alpha
    row_data <- matrix(c("powersave", workload, "Energy Consumption (J)", mean(sample1), median(sample1), sd(sample1), 
                         min(sample1), max(sample1), max(sample1) - min(sample1), 
                         shapiro1$statistic, shapiro1$p.value, isNormalityAssumed), nrow = 1)
    write.table(row_data, "output.csv", sep = ",", col.names = FALSE, row.names = FALSE, quote = FALSE, append = TRUE)
    
    
    sample1 <- getSample(data, "cpu_usage", condition)
    shapiro1 <- shapiro.test(sample1)
    isNormalityAssumed = shapiro1$p.value > alpha
    row_data <- matrix(c("powersave", workload, "CPU Usage", mean(sample1), median(sample1), sd(sample1), 
                         min(sample1), max(sample1), max(sample1) - min(sample1), 
                         shapiro1$statistic, shapiro1$p.value, isNormalityAssumed), nrow = 1)
    write.table(row_data, "output.csv", sep = ",", col.names = FALSE, row.names = FALSE, quote = FALSE, append = TRUE)
  }
}

showScatterplotUsage <- function(data) {
  
  ggplot(data, aes(x = cpu_usage, y = energy, color = governor_type, shape = workload_type)) +
    geom_point(size = 4, alpha = 0.8) +
    labs(title = "Scatterplot by Governor and Workload Type for High Network",
         subtitle = "CPU Utilization vs. Energy Consumption",
         x = "CPU Utilization (%)",
         y = "Energy Consumption (J)",
         color = "Governor Type",
         shape = "Workload Type") +
    scale_color_brewer(palette = "Set2") +
    scale_shape_manual(values = c(15, 19, 17)) +
    theme_ipsum(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      axis.title.x = element_text(size = 12, margin = margin(t = 10)),
      axis.title.y = element_text(size = 12, margin = margin(r = 10)),
    )
}

showScatterplotFreq <- function(data) {
  
  ggplot(data, aes(x = average_CPU_frequency, y = energy, color = governor_type, shape = workload_type)) +
    geom_point(size = 4, alpha = 0.8) +
    labs(title = "Scatterplot by Governor and Workload Type for High Network",
         subtitle = "Average CPU Frequency vs. Energy Consumption",
         x = "Average CPU Frequency (Hz)",
         y = "Energy Consumption (J)",
         color = "Governor Type",
         shape = "Workload Type") +
    scale_color_brewer(palette = "Set2") +
    scale_shape_manual(values = c(15, 19, 17)) +
    theme_ipsum(base_size = 12) +
    theme(
      plot.title = element_text(face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      axis.title.x = element_text(size = 12, margin = margin(t = 10)),
      axis.title.y = element_text(size = 12, margin = margin(r = 10)),
    )
}

data_low <- read.csv("Data/run_table_low.csv")
data_medium <- read.csv("Data/run_table_medium.csv")
data_high <- read.csv("Data/run_table_high.csv")

data <- data_high
#head(data)
data$workload_type <- trimws(data$workload_type)
data$governor_type <- trimws(data$governor_type)

showScatterplotUsage(data)
showScatterplotFreq(data)
#(data)

governors <- c("conservative", "ondemand", "performance", "schedutil", "userspace")
workloads <- c("low", "medium", "high")
doExperiment(governors, workloads, data)
addPowersaveData(data, workloads)
