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

timeMS = pcapStats$time*1000
lenMS = pcapStats$len
tputInMS = data.table(timeMS,lenMS)
tputInMS = na.omit(tputInMS)
 <- 1000# define window size
tputWindowed = setDT(tputInMS)[SJ(start = seq(min(timeMS), max(timeMS), 1))[, end := start + ws - 1], 
                       on = .(timeMS >= start, timeMS <= end),
                       .(Mbits = sum(lenMS)*8/1000000), by = .EACHI]
tputWindowed$timeS = tputWindowed$timeMS/1000


#filepath = paste("~/Research/plots/",args[2],".png",sep="")
#png(filepath)
#plot(tputWindowed$Mbits~tputWindowed$timeS,type='l', xlab = "Time(seconds)", 
#     ylab = "Throughput(Mbits)",xaxs = "i",yaxs = "i", xlim = c(0,round(max(pcapStats$time),0)*1.1), 
#     ylim = c(0,max(tputWindowed$Mbits,na.rm=TRUE)* 1.1))
tputWindowed$Mbits = rollmean(x=tputWindowed$Mbits,k=ws, fill = NA,align = "left")

tputWindowed[,timeMS:=NULL]
tputWindowed[,timeMS:=NULL]
tputWindowed = na.omit(tputWindowed)

filepath = args[2]
png(filepath)
plot(tputWindowed$Mbits~tputWindowed$timeS,type='l',xlab = "Time(seconds)", 
     ylab = "Throughput(Mbits)",xaxs = "i",yaxs = "i", xlim = c(0,round(max(pcapStats$time),0)*1.1), 
     ylim = c(0,max(tputWindowed$Mbits,na.rm=TRUE)* 1.1))

cat("Average thoughput:",  sum(pcapStats$len)/endTime*8/1000000, "Mbps
    ")
