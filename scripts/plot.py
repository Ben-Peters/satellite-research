import matplotlib.pyplot as pyplot
import pandas
import numpy


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
                self.throughput.append((bytesSent * 8) / 1048576)
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
                    tput.append((bytesSent * 8) / 1048576)
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
                    tput.append((bytesSent * 8) / 1048576)
                    secs.append(cutoffTime)
                    bytesSent = df['frame.len'].iloc[i]
                    cutoffTime += 1
            self.throughput.append(tput)
            self.seconds.append(secs)

    def avgRuns(self):
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


class PlotAllData(Plot):
    # TODO: Make this work
    def __init__(self, protocol, legend, csvFiles, plotFile, title, numRuns=1):
        super().__init__(protocol=protocol, legend=legend, csvFiles=csvFiles, plotFile=plotFile)
        self.numRuns = numRuns
        self.title = title
        self.rtt = []
        self.rttAVG = []
        self.cwnd = []
        self.cwndAVG = []
        self.rwnd = []
        self.rwndAVG = []
        self.retransmissions = []
        self.retransmissionsAVG = []

    def calculateStats(self):
        # TODO: do this
        for df in self.data:
            cutOffTime = 1
            bytesSent = 0
            throughput = []
            seconds = []

            rtt = []
            avgRTT = 0

            cwnd = []
            avgCwnd = 0

            rwnd = []
            avgRwnd = 0

            retransmissions = []
            retransmissionsCount = 0
            startFrame = 1

            for j in range(len(df)):
                # only packets from the Server
                if df['tcp.srcport'].iloc[j] == 5201:
                    # Track bytes sent for tput calc
                    bytesSent += df['frame.len'].iloc[j]

                    # rolling avg for CWND est.
                    if not pandas.isnull(df['tcp.analysis.bytes_in_flight'].iloc[j]):
                        if avgCwnd != 0:
                            avgCwnd = (avgCwnd + df['tcp.analysis.bytes_in_flight'].iloc[j]) / 2
                        else:
                            avgCwnd = df['tcp.analysis.bytes_in_flight'].iloc[j]



                # only packets from the Client
                if df['tcp.dstport'].iloc[j] == 5201 and (not pandas.isnull(df['tcp.analysis.ack_rtt'].iloc[j])):
                    # rolling avg for RTT est.
                    if avgRTT != 0:
                        avgRTT = (avgRTT + df['tcp.analysis.ack_rtt'].iloc[j]) / 2
                    else:
                        avgRTT = df['tcp.analysis.ack_rtt'].iloc[j]

                    # rolling avg for RWND est.
                    if avgRwnd != 0:
                        avgRwnd = (avgRwnd + df['tcp.window_size'].iloc[j]) / 2
                    else:
                        avgRwnd = df['tcp.window_size'].iloc[j]

                # count retransmissions
                if not pandas.isnull(df['tcp.analysis.retransmission'].iloc[j]) or not pandas.isnull(
                        df['tcp.analysis.fast_retransmission'].iloc[j]):
                    retransmissionsCount += 1

                if df['tcp.time_relative'].iloc[j] > float(cutOffTime):
                    throughput.append((bytesSent * 8) / 1048576)
                    seconds.append(cutOffTime)
                    rtt.append(avgRTT*1000)
                    cwnd.append(avgCwnd)
                    rwnd.append(avgRwnd)
                    retransmissions.append(retransmissionsCount / (j - startFrame + 1))

                    bytesSent = 0
                    avgRTT = 0
                    retransmissionsCount = 0
                    startFrame = j
                    cutOffTime += 1

            self.throughput.append(throughput)
            self.rtt.append(rtt)
            self.cwnd.append(cwnd)
            self.rwnd.append(rwnd)
            self.retransmissions.append(retransmissions)
            self.seconds.append(seconds)
        pass

    def avgAllData(self, startPos):
        minLength = len(self.throughput[0])
        minPos = startPos * self.numRuns
        avgTput = []
        avgRTT = []
        avgCwnd = []
        avgRwnd = []
        avgRetrans = []
        for i in range(int(self.numRuns * 2)):
            if minLength > len(self.throughput[i]):
                minLength = len(self.throughput[i])
        for t in range(minLength):
            tputSum = 0
            rttSum = 0
            cwndSum = 0
            rwndSum = 0
            retransSum = 0
            num = 0
            for i in range(self.numRuns):
                if len(self.throughput[i]) > t:
                    tputSum += self.throughput[i+minPos][t]
                    rttSum += self.rtt[i+minPos][t]
                    cwndSum += self.cwnd[i+minPos][t]
                    rwndSum += self.rwnd[i+minPos][t]
                    retransSum += self.retransmissions[i+minPos][t]
                    num += 1

            avgTput.append(tputSum / num)
            avgRTT.append(rttSum / num)
            avgCwnd.append(cwndSum / num / 1048576)  # Bytes to MBytes
            avgRwnd.append(rwndSum / num / 1048576)  # Bytes to MBytes
            avgRetrans.append(retransSum / num)
        self.throughputAVG.append(avgTput)
        self.rttAVG.append(avgRTT)
        self.cwndAVG.append(avgCwnd)
        self.rwndAVG.append(avgRwnd)
        self.retransmissionsAVG.append(avgRetrans)

    def plotStart(self, seconds):
        # TODO: Implement this and test it
        if not self.retransmissionsAVG:
            self.calculateStats()
            self.avgAllData(0)
            self.avgAllData(1)

        avgRTT = 0
        for i in range(len(self.rttAVG)):
            avgRTT += sum(self.rttAVG[i][0:seconds])
        avgRTT /= seconds * len(self.rttAVG)
        time = numpy.arange(0., seconds+1, 1)

        theoreticalTime = numpy.arange(0., seconds+1, avgRTT/1000)
        theoreticalCWND = numpy.copy(theoreticalTime)
        theoreticalTput = numpy.copy(theoreticalTime)

        for i in range(len(theoreticalTime)):
            if i == 0:
                theoreticalCWND[i] = 12000/1048576/8
                theoreticalTput[i] = 12000 / 1048576
            else:
                theoreticalCWND[i] = theoreticalCWND[i - 1] * 2
                theoreticalTput[i] = theoreticalTput[i - 1] * 2

        pyplot.clf()
        fig, axs = pyplot.subplots(3, gridspec_kw={'height_ratios': [2, 2, 2]})
        fig.set_figheight(8)

        axs[0].plot(theoreticalTime, theoreticalTput, 'k--')
        axs[0].plot(time, self.throughputAVG[0][0:seconds + 1], color='tab:orange')
        axs[0].plot(time, self.throughputAVG[1][0:seconds + 1], color='tab:blue')

        axs[1].plot(theoreticalTime, theoreticalCWND, 'k--')
        axs[1].plot(time, self.cwndAVG[0][0:seconds+1], color='tab:orange')
        axs[1].plot(time, self.cwndAVG[1][0:seconds+1], color='tab:blue')

        axs[2].plot(time, self.rwndAVG[0][0:seconds + 1], color='tab:orange')
        axs[2].plot(time, self.rwndAVG[1][0:seconds + 1], color='tab:blue')

        axs[0].set_ylabel("Throughput (Mbits)")
        axs[1].set_ylabel("CWND (MBytes)")
        axs[2].set_ylabel("RWND (MBytes)")

        axs[2].set_xlabel("Time (seconds)")
        legend = ['Theoretical'] + self.legend
        fig.legend(legend)
        fig.suptitle(self.title)

        maxY = max(self.rwndAVG[0][0:seconds+1])
        axs[0].set_ylim([0, max(self.throughputAVG[0][0:seconds+1])])
        axs[0].set_xlim([0, seconds])
        axs[1].set_ylim([0, maxY])
        axs[1].set_xlim([0, seconds])
        axs[2].set_ylim([0, maxY])
        axs[2].set_xlim([0, seconds])

        pyplot.savefig(self.plotFilepath.replace('.png', '_Start_CWND.png'))
        pyplot.show()

    def plotStartTput(self, seconds):
        # TODO: Implement this and test it
        if not self.retransmissionsAVG:
            self.calculateStats()
            self.avgAllData(0)
            self.avgAllData(1)
        avgRTT = 0
        for i in range(len(self.rttAVG)):
            avgRTT += sum(self.rttAVG[i][0:seconds])
        avgRTT /= seconds * len(self.rttAVG)
        theoreticalTime = numpy.arange(0., seconds+1, avgRTT/1000)
        theoreticalTput = numpy.copy(theoreticalTime)
        for i in range(len(theoreticalTime)):
            if i == 0:
                theoreticalTput[i] = 12000/1048576
            else:
                theoreticalTput[i] = theoreticalTput[i - 1] * 2
        time = numpy.arange(0., seconds+1, 1)
        pyplot.clf()
        pyplot.plot(theoreticalTime, theoreticalTput, 'k--')
        pyplot.plot(time, self.throughputAVG[0][0:seconds+1], color='tab:orange')
        pyplot.plot(time, self.throughputAVG[1][0:seconds+1], color='tab:blue')
        pyplot.ylabel("Throughput (Mbits)")
        pyplot.xlabel("Time (seconds)")
        legend = ['Theoretical'] + self.legend
        pyplot.legend(legend)
        pyplot.ylim([0, 19])
        pyplot.xlim([0, seconds])

        pyplot.savefig(self.plotFilepath.replace('.png', '_Start_TPUT.png'))

        pyplot.show()

    def plotALL(self, maxY=None, minRTT=550):
        # self.filterCSVs()
        # self.removeTimeOffset()
        if maxY is None:
            maxY = [None, None, None, None]
        self.calculateStats()
        self.avgAllData(0)
        self.avgAllData(1)

        # Setup formatting of plots
        fig, axs = pyplot.subplots(5, gridspec_kw={'height_ratios': [2, 1, 1, 1, 1]})
        fig.set_figheight(8)

        # for i in range(len(self.throughputAVG)):
        # axs[0].plot(self.secondsAVG[i], self.throughputAVG[i], '.', color='tab:blue')
        minLength = len(self.seconds[0])
        minIndex = 0
        for i in range(int(self.numRuns * 2)):
            if minLength > len(self.seconds[i]):
                minIndex = i
                minLength = len(self.seconds[i])
        axs[0].plot(self.seconds[minIndex], self.throughputAVG[0], color='tab:orange')
        axs[1].plot(self.seconds[minIndex], self.rttAVG[0], color='tab:orange')
        axs[2].plot(self.seconds[minIndex], self.rwndAVG[0], color='tab:orange')
        axs[3].plot(self.seconds[minIndex], self.cwndAVG[0], color='tab:orange')
        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[0], color='tab:orange')

        axs[0].plot(self.seconds[minIndex], self.throughputAVG[1], color='tab:blue')
        axs[1].plot(self.seconds[minIndex], self.rttAVG[1], color='tab:blue')
        axs[2].plot(self.seconds[minIndex], self.rwndAVG[1], color='tab:blue')
        axs[3].plot(self.seconds[minIndex], self.cwndAVG[1], color='tab:blue')
        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[1], color='tab:blue')

        for i in range(len(maxY)):
            if maxY[i] is not None:
                axs[i].set_ylim([0, maxY[i]])
            axs[i].set_xlim([0, len(self.seconds[minIndex])])

        fig.suptitle(self.title)
        fig.legend(self.legend)

        axs[0].set_ylabel("Throughput (Mbits)")
        axs[1].set_ylabel("RTT (ms)")
        axs[2].set_ylabel("RWND (MB)")
        axs[3].set_ylabel("CWND (MB)")
        axs[4].set_ylabel("Retrans. (%)")

        axs[4].set_xlabel("Time (seconds)")

        pyplot.savefig(self.plotFilepath)
        pyplot.show()

        flag = True
        if flag:
            print(f'Max Tput: {max(self.throughputAVG[0])}')
            print(f'Min RTT: {min(self.rttAVG[1])}')
            print(f'Max RTT: {max(self.rttAVG[0])}')
            print(f'Max cwnd: {max(self.cwndAVG[0])}')
            print(f'Max rwnd: {max(self.rwndAVG[0])}')
            print(f'Max retransmission rate: {max(self.retransmissionsAVG[0])}')

        for i in range(len(self.throughputAVG)):
            if i == 0:
                print("With Tuning")
            else:
                print("Without Tuning")
            print(f'Avg Throughput: {sum(self.throughputAVG[i])/len(self.throughputAVG[i])}')
            print(f'Avg rtt: {sum(self.rttAVG[i]) / len(self.rttAVG[i])}')
            print(f'Avg cwnd size: {sum(self.cwndAVG[i]) / len(self.cwndAVG[i])}')
            print(f'Avg Retransmission rate: {sum(self.retransmissionsAVG[i]) / len(self.retransmissionsAVG[i])}')

if __name__ == "__main__":
    plot = PlotTputOneFlow("hybla", "G:\satellite-research/cubic_2021_04_13-20-28-37.csv", "G:/satellite-research/cubicTput")
    plot.plotTput()
    # plot = PlotRTTOneFlow("hybla", "G:/research/hybla_2021_04_12-23-07-43.csv", "G:/research/hyblaRTT")
    # plot.plotRTT()
    # csvs = ["G:/research/hybla_2021_04_12-23-07-43.csv", "G:/research/hybla_2021_04_12-23-07-46.csv"]
    # legend = ["Server", "Client"]
    # plot = PlotTputCompare("hybla", legend, csvs, "G:/research/hyblaCompareTput")
    # plot.plotTput()
