import matplotlib.pyplot as pyplot
import pandas


class PlotRTTOneFlow:
    def __init__(self, protocol, csvFilepath, plotFilepath):
        self.protocol = protocol
        self.csv_file = csvFilepath
        self.plotFilepath = plotFilepath
        self.df = pandas.read_csv(csvFilepath)
        self.timesRaw = []  # pandas.to_datetime(self.df['frame.time'], infer_datetime_format=True)
        self.frameTime = []
        self.RTT = []
        self.seconds = []

    def filterCSV(self):
        self.df = self.df[self.df['tcp.dstport'] == 5201]
        # endTime = self.df[self.df['tcp.flags.fin'] == 1]['frame.time'].to_numpy()[0]
        # self.df = self.df[self.df['frame.time'] < endTime]
        self.df = self.df.dropna(subset=["tcp.analysis.ack_rtt"], axis=0)
        self.timesRaw = pandas.to_datetime(self.df['frame.time'], infer_datetime_format=True)

    def removeTimeOffset(self):
        for i in range(len(self.timesRaw) - 1):
            timeOffset = pandas.Timedelta(self.timesRaw.iloc[i] - self.timesRaw.iloc[0])
            self.frameTime.append(timeOffset.seconds + (timeOffset.microseconds / 1000000) +
                                  (timeOffset.nanoseconds / 1000000000))

    def calculateRTT(self):
        cutoffTime = 1
        sumRTT = 0
        numPackets = 0
        for i in range(len(self.df['frame.len']) - 1):
            if self.frameTime[i] <= float(cutoffTime):
                sumRTT += self.df['tcp.analysis.ack_rtt'].iloc[i]
                numPackets += 1
            else:
                avgRTT = (sumRTT / numPackets) * 1000
                self.RTT.append(avgRTT)
                self.seconds.append(cutoffTime)
                sumRTT = self.df['tcp.analysis.ack_rtt'].iloc[i]
                numPackets = 1
                cutoffTime += 1

    def plotRTT(self):
        self.filterCSV()
        self.removeTimeOffset()
        self.calculateRTT()

        pyplot.plot(self.seconds, self.RTT)
        pyplot.xlabel("Time (seconds)")
        pyplot.ylabel("RTT (ms)")
        pyplot.legend([self.protocol])
        pyplot.title('RTT vs Time')
        pyplot.savefig(self.plotFilepath)

        pyplot.show()


class PlotTputOneFlow:
    def __init__(self, protocol, csvFilepath, plotFilepath):
        self.protocol = protocol
        # self.csv_file = csvFilepath
        self.plotFilepath = plotFilepath
        self.df = pandas.read_csv(csvFilepath)
        self.timesRaw = []  # pandas.to_datetime(self.df['frame.time'], infer_datetime_format=True)
        self.frameTime = []
        self.throughput = []
        self.seconds = []

    def filterCSV(self):
        self.df = self.df[self.df['tcp.srcport'] == 5201]
        # endTime = self.df[self.df['tcp.flags.fin'] == 1]['frame.time'].to_numpy()[0]
        # self.df = self.df[self.df['frame.time'] < endTime]
        self.timesRaw = pandas.to_datetime(self.df['frame.time'], infer_datetime_format=True)

    def removeTimeOffset(self):
        for i in range(len(self.timesRaw) - 1):
            timeOffset = pandas.Timedelta(self.timesRaw.iloc[i] - self.timesRaw.iloc[0])
            self.frameTime.append(timeOffset.seconds + (timeOffset.microseconds / 1000000) +
                                  (timeOffset.nanoseconds / 1000000000))

    def calculateThroughput(self):
        cutoffTime = 1
        bytesSent = 0
        for i in range(len(self.df['frame.len']) - 1):
            if self.frameTime[i] <= float(cutoffTime):
                bytesSent += self.df['frame.len'].iloc[i]
            else:
                self.throughput.append((bytesSent * 8) / 1000000)
                self.seconds.append(cutoffTime)
                bytesSent = self.df['frame.len'].iloc[i]
                cutoffTime += 1

    def plotTput(self):
        self.filterCSV()
        self.removeTimeOffset()
        self.calculateThroughput()

        pyplot.plot(self.seconds, self.throughput)
        pyplot.xlabel("Time (seconds)")
        pyplot.ylabel("Throughput (Mbits)")
        pyplot.legend([self.protocol])
        pyplot.title('Throughput vs Time')
        pyplot.savefig(self.plotFilepath)

        pyplot.show()


class PlotTputCompare:
    def __init__(self, protocol, legend, csvFiles, plotFile, numRuns=1):
        self.protocol = protocol
        self.csvFile = csvFiles
        self.plotFilepath = plotFile
        self.legend = legend
        self.data = []
        self.numRuns = numRuns
        for csv in csvFiles:
            self.data.append(pandas.read_csv(csv))
        self.timesRaw = []  # pandas.to_datetime(self.df['frame.time'], infer_datetime_format=True)
        self.frameTime = []
        self.throughput = []
        self.seconds = []
        self.throughputAVG = []
        self.secondsAVG = []

    def filterCSVs(self):
        for i in range(len(self.data)):
            df = self.data[i]
            df = df[df['tcp.srcport'] == 5201]
            # endTime = df[df['tcp.flags.fin'] == 1]['frame.time'].to_numpy()[0]
            # df = df[df['frame.time'] < endTime]
            self.timesRaw.append(pandas.to_datetime(df['frame.time']))
            self.data[i] = df

    def removeTimeOffset(self):
        for times in self.timesRaw:
            shiftedTime = []
            for i in range(len(times) - 1):
                timeOffset = pandas.Timedelta(times.iloc[i] - times.iloc[0])
                shiftedTime.append(timeOffset.seconds + (timeOffset.microseconds / 1000000) +
                                      (timeOffset.nanoseconds / 1000000000))
            self.frameTime.append(shiftedTime)

    def calculateThroughput(self):
        for time, df in zip(self.frameTime, self.data):
            cutoffTime = 1
            bytesSent = 0
            tput = []
            secs = []
            for i in range(len(df['frame.len']) - 1):
                if time[i] <= float(cutoffTime):
                    bytesSent += df['frame.len'].iloc[i]
                else:
                    tput.append((bytesSent * 8) / 1000000)
                    secs.append(cutoffTime)
                    bytesSent = df['frame.len'].iloc[i]
                    cutoffTime += 1
            self.throughput.append(tput)
            self.seconds.append(secs)

    def avgRuns(self):
        maxLength = 0
        maxIndex = 0
        for i in range(int(self.numRuns*2)):
            if maxLength < len(self.throughput[i]):
                maxLength = len(self.throughput[i])
                maxIndex = i
        sums = [0 for x in range(maxLength)]
        for i in range(self.numRuns):
            # time = self.seconds[i]
            tput = self.throughput[i]
            #sums = [val+bits for val, bits in zip(sums, tput)]
            for j in range(len(tput)):
                sums[j] += tput[j]
        self.throughputAVG.append([x/self.numRuns for x in sums])
        self.secondsAVG.append(self.seconds[maxIndex])
        sums = [0 for x in range(maxLength)]
        for i in range(self.numRuns):
            # time = self.seconds[i]
            tput = self.throughput[i+self.numRuns]
            #sums = [val + bits for val, bits in zip(sums, tput)]
            for j in range(len(tput)):
                sums[j] += tput[j]
        self.throughputAVG.append([x / self.numRuns for x in sums])
        self.secondsAVG.append(self.seconds[maxIndex])
        # self.throughputAVG = [float('nan') if x == 0 else x for x in self.throughputAVG]

    def plotTput(self):
        self.filterCSVs()
        self.removeTimeOffset()
        self.calculateThroughput()
        self.avgRuns()

        for time, tput in zip(self.secondsAVG, self.throughputAVG):
            pyplot.plot(time, tput)
        pyplot.xlabel("Time (seconds)")
        pyplot.ylabel("Throughput (Mbits)")
        pyplot.legend(self.legend)
        pyplot.title(f'{self.protocol} Throughput vs Time')
        pyplot.savefig(self.plotFilepath)

        pyplot.show()


if __name__ == "__main__":
    plot = PlotTputOneFlow("hybla", "G:\satellite-research/cubic_2021_04_13-20-28-37.csv", "G:/satellite-research/cubicTput")
    plot.plotTput()
    # plot = PlotRTTOneFlow("hybla", "G:/research/hybla_2021_04_12-23-07-43.csv", "G:/research/hyblaRTT")
    # plot.plotRTT()
    # csvs = ["G:/research/hybla_2021_04_12-23-07-43.csv", "G:/research/hybla_2021_04_12-23-07-46.csv"]
    # legend = ["Server", "Client"]
    # plot = PlotTputCompare("hybla", legend, csvs, "G:/research/hyblaCompareTput")
    # plot.plotTput()
