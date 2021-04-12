library(data.table)
library(tidyverse)
args = commandArgs(trailingOnly=TRUE)
if(length(args != 0)){
  file = args[1]
} else {
  file = "G:/research/csvs/pccServer.csv"
}

pcapStats <- read_csv(file)
pcapStats = filter(pcapStats,srcPort == "Src Port: 5201")
endTime = filter(pcapStats, fin == 1)$time
pcapStats = filter(pcapStats,time <= endTime)
endTime = endTime - min(pcapStats$time)
pcapStats$time = pcapStats$time - min(pcapStats$time)
pcapStats$len = as.numeric(str_extract(pcapStats$len, "[0-9]+"))

totalTime = as.integer(endTime + 0.5)
time = 0:(totalTime-1)
tput = 0:(totalTime-1)

for(i in 1:totalTime){
  second = filter(pcapStats, time > i-1, time <= i)
  tput[i] = sum(second$len)*8/1000000
}
tputData = data.frame(time,tput)

filepath = args[2]
png(filepath)
plot(tputData$tput~tputData$time,type='l',xlab = "Time(seconds)", 
     ylab = "Throughput(Mbits)",xaxs = "i",yaxs = "i", xlim = c(0,totalTime*1.1), 
     ylim = c(0,max(tputData$tput)* 1.1))

cat("Average thoughput:",  sum(pcapStats$len)/endTime*8/1000000, "Mbps
    ")
