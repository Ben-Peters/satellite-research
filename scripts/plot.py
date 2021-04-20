import matplotlib.pyplot as pyplot
import pandas


class PlotRTTOneFlow:
    # TODO: Remove this
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
    # TODO: Remove this
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
    # TODO: Remvoe this
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
        minLength = len(self.throughput[0])
        minIndex = 0
        for i in range(int(self.numRuns*2)):
            if minLength > len(self.throughput[i]):
                minLength = len(self.throughput[i])
                minIndex = i
        sums = [0 for x in range(minLength)]
        for i in range(self.numRuns):
            # time = self.seconds[i]
            tput = self.throughput[i][0:minLength]
            #sums = [val+bits for val, bits in zip(sums, tput)]
            for j in range(len(tput)):
                sums[j] += tput[j]
        self.throughputAVG.append([x/self.numRuns for x in sums])
        self.secondsAVG.append(self.seconds[minIndex])
        sums = [0 for x in range(minLength)]
        for i in range(self.numRuns):
            # time = self.seconds[i]
            tput = self.throughput[i+self.numRuns][0:minLength]
            #sums = [val + bits for val, bits in zip(sums, tput)]
            for j in range(len(tput)):
                sums[j] += tput[j]
        self.throughputAVG.append([x / self.numRuns for x in sums])
        self.secondsAVG.append(self.seconds[minIndex])
        # self.throughputAVG = [float('nan') if x == 0 else x for x in self.throughputAVG]




class Plot:
    # TODO: make sure this does what I want
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

    def avgRuns(self, protocol, legend, csvFiles, plotFile, numRuns=1):
        # TODO: Convert this to a better version
        minLength = len(self.throughput[0])
        minIndex = 0
        for i in range(int(self.numRuns*2)):
            if minLength > len(self.throughput[i]):
                minLength = len(self.throughput[i])
                minIndex = i
        sums = [0 for x in range(minLength)]
        for i in range(self.numRuns):
            # time = self.seconds[i]
            tput = self.throughput[i][0:minLength]
            #sums = [val+bits for val, bits in zip(sums, tput)]
            for j in range(len(tput)):
                sums[j] += tput[j]
        self.throughputAVG.append([x/self.numRuns for x in sums])
        self.secondsAVG.append(self.seconds[minIndex])
        sums = [0 for x in range(minLength)]
        for i in range(self.numRuns):
            # time = self.seconds[i]
            tput = self.throughput[i+self.numRuns][0:minLength]
            #sums = [val + bits for val, bits in zip(sums, tput)]
            for j in range(len(tput)):
                sums[j] += tput[j]
        self.throughputAVG.append([x / self.numRuns for x in sums])
        self.secondsAVG.append(self.seconds[minIndex])
        # self.throughputAVG = [float('nan') if x == 0 else x for x in self.throughputAVG]

    def plot(self):
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

class plotAllData(Plot):
    # TODO: Make this work
    def __init__(self, protocol, legend, csvFiles, plotFile, title, numRuns=1):
        super().__init__(self, protocol, legend, csvFiles, plotFile)
        self.numRuns = numRuns
        self.title = title
        self.rtt = []
        self.rttAVG = []
        self.cwnd = []
        self.cwndAVG = []
        self.retransmissions = []
        self.retransmissionsAVG = []

    def calculateStats(self):
        # TODO: do this
        pass

    def avgAllData(self, startPos):
        minLength = len(self.throughput[0])
        minPos = startPos * self.numRuns
        avgTput = []
        avgRTT = []
        avgCwnd = []
        avgRetrans = []
        for i in range(int(self.numRuns * 2)):
            if minLength > len(self.throughput[i]):
                minLength = len(self.throughput[i])
        for t in range(minLength):
            tputSum = 0
            rttSum = 0
            cwndSum = 0
            retransSum = 0
            num = 0
            for i in range(self.numRuns):
                if len(self.throughput[i]) > t:
                    tputSum += self.throughput[i+minPos][t]
                    rttSum += self.rtt[i+minPos][t]
                    cwndSum += self.cwnd[i+minPos][t]
                    retransSum += self.retransmissions[i+minPos][t]
                    num += 1

            avgTput.append(tputSum / num)
            avgRTT.append(rttSum / num)
            avgCwnd.append(cwndSum / num / 1048576)  # Bytes to MBytes
            avgRetrans.append(retransSum / num)
        self.throughputAVG.append(avgTput)
        self.rttAVG.append(avgRTT)
        self.cwndAVG.append(avgCwnd)  # Bytes to MBytes
        self.retransmissionsAVG.append(avgRetrans)

    def plot(self):
        self.filterCSVs()
        self.removeTimeOffset()
        self.calculateStats()
        self.avgAllData(0)
        self.avgAllData(1)

        # Setup formatting of plots
        fig, axs = pyplot.subplots(4, gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        fig.set_figheight(8)

        # for i in range(len(self.throughputAVG)):
        # axs[0].plot(self.secondsAVG[i], self.throughputAVG[i], '.', color='tab:blue')

        axs[0].plot(self.secondsAVG, self.throughputAVG[0], color='tab:orange')
        axs[1].plot(self.secondsAVG, self.rttAVG[0], color='tab:orange')
        axs[2].plot(self.secondsAVG, self.cwndAVG[0], color='tab:orange')
        axs[3].plot(self.secondsAVG, self.retransmissionsAVG[0], color='tab:orange')

        axs[0].plot(self.secondsAVG, self.throughputAVG[1], color='tab:blue')
        axs[1].plot(self.secondsAVG, self.rttAVG[1], color='tab:blue')
        axs[2].plot(self.secondsAVG, self.cwndAVG[1], color='tab:blue')
        axs[3].plot(self.secondsAVG, self.retransmissionsAVG[1], color='tab:blue')

        fig.suptitle(self.title)
        fig.legend(self.legend)
        axs[0].set_ylabel("Throughput (Mbits)")
        axs[1].set_ylabel("RTT (ms)")
        axs[2].set_ylabel("CWND (MB)")
        axs[3].set_ylabel("Retrans. (%)")
        axs[3].set_xlabel("Time (seconds)")

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
