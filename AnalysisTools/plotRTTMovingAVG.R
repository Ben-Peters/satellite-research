library(data.table)
library(tidyverse)
args = commandArgs(trailingOnly=TRUE)
if(length(args != 0)){
	   file = args[1]
} else {
	file = "G:/research/csvs/pccServer.csv"
}

pcapStats <- read_csv(file)
#pcapStats = na.omit(pcapStats,rtt)
pcapStats = filter(pcapStats,dstPort == "Dst Port: 5201", rtt >= 0)
pcapStats$time = pcapStats$time - min(pcapStats$time)

timeMS = pcapStats$time*1000
rttMS = pcapStats$rtt*1000
data = data.frame(timeMS,rttMS)
data = na.omit(data)
data$timeMS = data$timeMS - min(data$timeMS)

ws <- 1000# define window size
averaged = setDT(data)[SJ(start = seq(min(timeMS), max(timeMS), 1))[, end := start + ws - 1], 
                       on = .(timeMS >= start, timeMS <= end),
                       .(avgRTT = mean(rttMS)), by = .EACHI]
averaged$timeS = averaged$timeMS/1000
averaged[,timeMS:=NULL]
averaged[,timeMS:=NULL]

filepath = args[2]
png(filepath)
plot(averaged$avgRTT~averaged$timeS,type='l', xlab = "Time(seconds)", 
     ylab = "RTT(ms)",xaxs = "i",yaxs = "i", xlim = c(0,round(max(pcapStats$time),0)*1.1), 
     ylim = c(0,max(averaged$avgRTT)* 1.1))


cat("Average RTT:", mean(pcapStats$rtt)*1000, "ms
    ")
