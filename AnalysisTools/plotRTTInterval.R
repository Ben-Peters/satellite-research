library(data.table)
library(tidyverse)
args = commandArgs(trailingOnly=TRUE)
if(length(args != 0)){
	           file = args[1]
} else {
	        file = "G:/research/csvs/pccServer.csv"
}

pcapStats <- read_csv(file)
pcapStats = na.omit(pcapStats,rtt)
pcapStats = filter(pcapStats,dstPort == "Dst Port: 5201", rtt >= 0)
pcapStats$time = pcapStats$time - min(pcapStats$time)

totalTime = round(max(pcapStats$time),0)+1
time = 0:(totalTime-1)
avgRTT = 0:(totalTime-1)
for(i in 1:totalTime){
  second = filter(pcapStats, time > i-1, time <= i)
  avgRTT[i] = sum(second$rtt)/nrow(second)*1000
}
roughData = data.frame(time,avgRTT)
roughData = na.omit(roughData)

filepath = paste("~/Research/plots/",args[2],".png",sep="")
png(filepath)
plot(roughData$avgRTT~roughData$time,type='l',xlab = "Time(seconds)", 
     ylab = "RTT(ms)",xaxs = "i",yaxs = "i", xlim = c(0,totalTime*1.08), 
     ylim = c(0,max(roughData$avgRTT)* 1.1))

cat("Average RTT:",  mean(pcapStats$rtt)*1000, "ms
    ")

