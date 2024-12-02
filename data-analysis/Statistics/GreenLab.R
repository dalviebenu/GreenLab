
#install.packages("devtools")
#devtools::install_github("hrbrmstr/hrbrthemes")

# Load necessary libraries
library(ggplot2)
library(dplyr)
library(stats)
library(hrbrthemes)


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

isSampleEqual <- function(sample1, sample2){
  
  isNormalityAssumed = isShapiroWilk(sample1, sample2)
  
  if(isNormalityAssumed) {
    rejectHypothesis <- isEqualNormalityAssumed(sample1, sample2)
  }
  else {
    rejectHypothesis <- isEqualNormalityNotAssumed(sample1, sample2)
  }
  if(rejectHypothesis) {
    print("The samples are statistically different and the null-hypothesis is rejected")
  }
  else {
    print("The samples are statistically equal and the null-hypothesis is accepted")
  }
    
}

isEqualNormalityAssumed <- function(sample1, sample2, alpha = 0.05){
  
  if (length(sample1) != length(sample2)) {
    stop("Length of samples must be equal")
  }
  pValue = t.test(sample1, sample2, paired = TRUE)$p.value
  cat("P-value according to t-test = ", pValue, "\n")
  
  return(pValue >= alpha)
}

isEqualNormalityNotAssumed <- function(sample1, sample2, alpha = 0.05){
  if (length(sample1) != length(sample2)) {
    stop("Length of samples must be equal")
  }
  pValue = wilcox.test(sample1, sample2, paired = TRUE)$p.value
  cat("P-value according to Wilcox Test = ", pValue, "\n")
  
  return(pValue >= alpha)
}

# Example Data
data <- read.csv("Data/run_table.csv")

condition1 <- expression(
  governor_type == "powersave" & workload_type == "a"
)

condition2 <- expression(
  governor_type == "powersave" & workload_type == "b"
)

doExperiment <- function(governors, workload_types) {
  
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
      
      isSampleEqual(sample1, sample2)
      
      sample3 = getSample(data, "cpu_usage", condition1)
      sample4 = getSample(data, "cpu_usage", condition2)
      
      showDescriptiveStatistics(sample3)
      
      isSampleEqual(sample3, sample4)
    }
  }
}

showScatterplot <- function(data) {
  governors <- c("conservative", "ondemand", "performance", "powersave", "schedutil", "userspace")
  workloads <- c("low", "medium", "high")
  doExperiment(governors, workloads)

  ggplot(data, aes(x = cpu_usage, y = energy, color = governor_type, shape = workload_type)) +
    geom_point(size = 4, alpha = 0.8) +
    labs(title = "Scatterplot by Governor Type",
         subtitle = "CPU Usage vs. Energy Consumption",
         x = "CPU Usage (%)",
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