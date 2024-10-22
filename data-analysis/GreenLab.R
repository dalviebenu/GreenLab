# Load necessary libraries
library(ggplot2)
library(dplyr)
library(stats)

set.seed(0)

showDescriptiveStatistics <- function(data) {
  
  dataSummary <- summary(data)
  print("Descriptive Statistics: ")
  print(dataSummary)
}

showScatterplot <- function(data, column1, column2) {
  
  if (!column1 %in% names(data) || !column2 %in% names(data)) {
    stop("One or both specified columns don't exist")
  }
  
  ggplot(data, aes(x = .data[[column1]], y = .data[[column2]])) +
    geom_point(color = "blue", size = 2) +
    labs(title = "Scatter plot", x = column1, y = column2)
}

showBoxplot <- function(data, column, group = NULL) {
  
  if (!column %in% names(data) && !group %in% names(data)) {
    stop("The specified column and/or group doesn't exist")
  }

  boxplot(as.formula(paste(column, "~", group)), data = data, 
    main = "Boxplot", xlab = group, ylab = column, 
    col = "red", notch = FALSE, outline = TRUE)
}

isShapiroWilk <- function(sample1, sample2, alpha = 0.05) {
  
  shapiro1 <- shapiro.test(sample1)
  shapiro2 <- shapiro.test(sample2)
  
  cat("Shapiro-Wilk Test Value for sample1 = ", shapiro1, "\n")
  cat("Shapiro-Wilk Test Value for sample2 = ", shapiro2, "\n")
  
  return(shapiro1$p.value > alpha && shapiro2$p.value > alpha)
}

getSamples <- function(data, column, filterConditions1, filterConditions2) {
  
  if (!all(names(filter_conditions) %in% names(data))) {
    stop("One or more filtering columns do not exist")
  }
  
  if (!(sample1_col %in% names(data) && sample2_col %in% names(data))) {
    stop("Sample columns do not exist")
  }
  
  for (col in names(filterCondition)) {
    filter_value <- filter_conditions[[col]]
    data <- data[data[[col]] == filter_value, ]
  }
  
  sample1 = filterData(data, column, filterConditions1)
  
  sample2 = filterData(data, column, filterConditions2)
  
  return(list(sample1 = sample1, sample2 = sample2))
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
    return(isEqualNormalityAssumed())
  }
  else {
    return(isEqualNormalityNotAssumed())
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
data <- read.csv("Data/cars.csv")
head(data)