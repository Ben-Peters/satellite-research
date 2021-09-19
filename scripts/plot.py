import math
import sys

import matplotlib.pyplot as pyplot
import pandas
import numpy
import statistics
from scipy import stats
from multiprocessing import Process, Lock, Pipe

pyplot.rcParams.update({'font.size': 11})
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
        pyplot.ylabel("RTT (s)")
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
        pyplot.ylabel("Throughput (Mb/s)")
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
    def __init__(self, protocol, legend, csv, plotFile, numRuns=1):
        self.protocol = protocol
        self.csv = csv
        self.plotFilepath = plotFile
        self.legend = legend
        self.data = []
        self.numRuns = numRuns
        typeDict = {'frame.len': int,
                    'tcp.srcport': int,
                    'tcp.dstport': int,
                    'tcp.len': int,
                    'tcp.window_size': int,
                    'tcp.analysis.retransmission': int,
                    'tcp.analysis.fast_retransmission': int,
                    'tcp.analysis.bytes_in_flight': int,
                    'tcp.analysis.ack_rtt': float,
                    'frame.time': str,
                    'tcp.time_relative': float}
        # memory mapping can be enabled to improve performance but at the expense of memory usage for large files
        self.data.append(pandas.read_csv(csv, memory_map=True))
        self.timesRaw = []  # pandas.to_datetime(self.df['frame.time'], infer_datetime_format=True)
        self.frameTime = []
        self.throughput = []
        self.seconds = []
        self.throughputAVG = []
        self.secondsAVG = []
        self.ssExit = []
        self.ssExitAVG = 0

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
        pyplot.ylabel("Throughput (Mb/s)")
        pyplot.legend(self.legend)
        pyplot.title(f'{self.protocol} Throughput vs Time')
        pyplot.savefig(self.plotFilepath)

        pyplot.show()


def calculateConfidenceInterval(values, confidenceLevel):
    interval = stats.t.interval(alpha=confidenceLevel, df=len(values)-1, loc=numpy.mean(values), scale=stats.sem(values))
    # print(stats.sem(values))
    if math.isnan(interval[0]):
        interval = (numpy.mean(values), numpy.mean(values))
    return interval
    # sd = statistics.stdev(values)
    # tscore = stats.t.ppf(q=confidenceLevel, df=len(values)-1)
    # interval = tscore * sd/math.sqrt(sd)
    # return interval


class PlotAllData(Plot):
    def __init__(self, protocol, legend, csv, plotFile, title, numRuns=1):
        super().__init__(protocol=protocol, legend=legend, csv=csv, plotFile=plotFile)
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
        self.timeDelta = []
        self.timeDeltaAVG = []
        self.rttCI = []
        self.throughputCI = []
        self.cwndCI = []
        self.rwndCI = []
        self.retransmissionsCI = []
        self.timeDeltaCI = []
        self.ssExitCI = []
        self.producerSem = Lock()
        self.consumerSem = Lock()
        self.minRTT = []
        self.minRTTAVG = 0
        self.minRTTCI = []

    def calculateStats(self, data, pipe, pSem, count):
            df = data
            cutOffTime = 1
            bytesSent = 0
            throughput = []
            seconds = []

            rtt = []
            avgRTT = 0
            RTTSum = 0
            RTTCount = 0

            cwnd = []
            avgCwnd = 0
            cwndSum = 0
            cwndCount = 0

            rwnd = []
            avgRwnd = 0
            rwndSum = 0

            # serverCount = 0
            clientCount = 0

            timeDelta = []
            avgTD = 0
            TDsum = 0
            TDcount = 0
            prevTime = 0

            retransmissions = []
            retransmissionsCount = 0
            startFrame = 1

            for j in range(len(df)):
                # only packets from the Server
                if df['tcp.srcport'].iloc[j] == 5201:
                    # serverCount += 1
                    # Track bytes sent for tput calc
                    bytesSent += df['frame.len'].iloc[j]

                    # Only look at packets that have data bout CWND
                    if not pandas.isnull(df['tcp.analysis.bytes_in_flight'].iloc[j]):
                        cwndCount += 1
                        cwndSum += df['tcp.analysis.bytes_in_flight'].iloc[j]

                        # rolling avg for CWND est.
                        # if avgCwnd != 0:
                            # avgCwnd = (avgCwnd + df['tcp.analysis.bytes_in_flight'].iloc[j]) / 2
                        # else:
                            # avgCwnd = df['tcp.analysis.bytes_in_flight'].iloc[j]

                # only packets from the Client
                if df['tcp.dstport'].iloc[j] == 5201:
                    clientCount += 1

                    if not pandas.isnull(df['tcp.time_relative'].iloc[j]):
                        TDsum += df['tcp.time_relative'].iloc[j] - prevTime
                        TDcount += 1
                        prevTime = df['tcp.time_relative'].iloc[j]

                    if not pandas.isnull(df['tcp.analysis.ack_rtt'].iloc[j]):
                        RTTCount += 1
                        RTTSum += df['tcp.analysis.ack_rtt'].iloc[j]

                    # rolling avg for RTT est.
                    # if avgRTT != 0:
                        # avgRTT = (avgRTT + df['tcp.analysis.ack_rtt'].iloc[j]) / 2
                    # else:
                        # avgRTT = df['tcp.analysis.ack_rtt'].iloc[j]

                    rwndSum += df['tcp.window_size'].iloc[j]

                    # rolling avg for RWND est.
                    # if avgRwnd != 0:
                        # avgRwnd = (avgRwnd + df['tcp.window_size'].iloc[j]) / 2
                    # else:
                        # avgRwnd = df['tcp.window_size'].iloc[j]

                # count retransmissions from both server and client
                if not pandas.isnull(df['tcp.analysis.retransmission'].iloc[j]) or not pandas.isnull(
                        df['tcp.analysis.fast_retransmission'].iloc[j]):
                    retransmissionsCount += 1

                if df['tcp.time_relative'].iloc[j] > float(cutOffTime):
                    throughput.append((bytesSent * 8) / 1048576)
                    seconds.append(cutOffTime)
                    if RTTCount == 0:
                        rtt.append(0)
                    else:
                        rtt.append((RTTSum/RTTCount))
                    if cwndCount == 0:
                        cwnd.append(0)
                    else:
                        cwnd.append(cwndSum/cwndCount)
                    if clientCount == 0:
                        rwnd.append(0)
                    else:
                        rwnd.append(rwndSum/clientCount)
                        # if cutOffTime == 11:
                            # print(rwndSum/clientCount)
                    retransmissions.append((retransmissionsCount / (j - startFrame + 1))*100)
                    if TDcount == 0:
                        timeDelta.append(0)
                    else:
                        timeDelta.append((TDsum/TDcount))

                    bytesSent = 0
                    RTTSum = 0
                    RTTCount = 0
                    cwndSum = 0
                    cwndCount = 0
                    rwndSum = 0
                    clientCount = 0
                    retransmissionsCount = 0
                    startFrame = j
                    cutOffTime += 1
                    TDsum = 0
                    TDcount = 0

            results = (count, throughput, rtt, cwnd, rwnd, retransmissions, seconds, timeDelta)
            self.throughput.append(throughput)
            self.rtt.append(rtt)
            self.cwnd.append(cwnd)
            self.rwnd.append(rwnd)
            self.retransmissions.append(retransmissions)
            self.seconds.append(seconds)
            self.timeDelta.append(timeDelta)
            print(f"{count}: Results Ready")
            # pSem.acquire()
            pipe.send(results)
            pipe.close()
            # pSem.release()

    def analyzeThreaded3(self):
        results = []
        processes = []
        parentPipes = []
        # Create threads
        sortedData = []
        for df, i in zip(self.data, range(len(self.data))):
            if i % 3 == 0:
                # (cap enabled)
                sortedData.append(df)
        for df, i in zip(self.data, range(len(self.data))):
            if i % 3 == 1:
                # (cap disabled)
                sortedData.append(df)
        for df, i in zip(self.data, range(len(self.data))):
            if i % 3 == 2:
                # (hystart disabled)
                sortedData.append(df)
        self.data = sortedData
        for df, i in zip(self.data, range(len(self.data))):
            self.throughput.append([])
            self.rtt.append([])
            self.cwnd.append([])
            self.rwnd.append([])
            self.retransmissions.append([])
            self.seconds.append([])
            self.timeDelta.append([])
            parentPipe, childPipe = Pipe()
            parentPipes.append(parentPipe)
            p = Process(target=self.calculateStats, args=(df, childPipe, self.producerSem, i))
            p.start()
            processes.append(p)
        # Get results from threads
        for conn in parentPipes:
            # self.consumerSem.acquire()
            results.append(conn.recv())
            # self.consumerSem.release()
        # wait for threads to finish and join them
        for p in processes:
            p.join()
        # put results in the right order
        for result in results:
            i = result[0]
            throughput = result[1]
            rtt = result[2]
            cwnd = result[3]
            rwnd = result[4]
            retransmissions = result[5]
            seconds = result[6]
            timeDelta = result[7]
            self.throughput[i] = throughput
            self.rtt[i] = rtt
            self.cwnd[i] = cwnd
            self.rwnd[i] = rwnd
            self.retransmissions[i] = retransmissions
            self.seconds[i] = seconds
            self.timeDelta[i] = timeDelta

    def analyzeThreaded(self):
        results = []
        processes = []
        parentPipes = []
        # Create threads
        sortedData = []
        for df, i in zip(self.data, range(len(self.data))):
            if i % 2 == 0:
                # is even (tuning enabled)
                sortedData.append(df)
        for df, i in zip(self.data, range(len(self.data))):
            if i % 2 == 1:
                # is odd (tuning disabled)
                sortedData.append(df)
        self.data = sortedData
        for df, i in zip(self.data, range(len(self.data))):
            self.throughput.append([])
            self.rtt.append([])
            self.cwnd.append([])
            self.rwnd.append([])
            self.retransmissions.append([])
            self.seconds.append([])
            self.timeDelta.append([])
            parentPipe, childPipe = Pipe()
            parentPipes.append(parentPipe)
            p = Process(target=self.calculateStats, args=(df, childPipe, self.producerSem, i))
            p.start()
            processes.append(p)
        # Get results from threads
        for conn in parentPipes:
            # self.consumerSem.acquire()
            results.append(conn.recv())
            # self.consumerSem.release()
        # wait for threads to finish and join them
        for p in processes:
            p.join()
        # put results in the right order
        for result in results:
            i = result[0]
            throughput = result[1]
            rtt = result[2]
            cwnd = result[3]
            rwnd = result[4]
            retransmissions = result[5]
            seconds = result[6]
            timeDelta = result[7]
            self.throughput[i] = throughput
            self.rtt[i] = rtt
            self.cwnd[i] = cwnd
            self.rwnd[i] = rwnd
            self.retransmissions[i] = retransmissions
            self.seconds[i] = seconds
            self.timeDelta[i] = timeDelta

    def avgAllData(self, startPos):
        minLength = len(self.throughput[0])
        minPos = startPos * self.numRuns
        avgTput = []
        avgRTT = []
        avgCwnd = []
        avgRwnd = []
        avgRetrans = []
        avgTD = []

        ciTput = [[], []]
        ciRTT = [[], []]
        ciCwnd = [[], []]
        ciRwnd = [[], []]
        ciRetrans = [[], []]
        ciTD = [[], []]
        for i in range(len(self.throughput)):
            if minLength > len(self.throughput[i]):
                minLength = len(self.throughput[i])
        for t in range(minLength):
            tputSum = 0
            rttSum = 0
            cwndSum = 0
            rwndSum = 0
            retransSum = 0
            TDsum = 0

            tputValues = []
            rttValues = []
            cwndValues = []
            rwndValues = []
            retransValues = []
            TDvalues = []
            num = 0
            for i in range(self.numRuns):
                if len(self.throughput[i]) > t:
                    tputSum += self.throughput[i+minPos][t]
                    rttSum += self.rtt[i+minPos][t]
                    cwndSum += self.cwnd[i+minPos][t]
                    rwndSum += self.rwnd[i+minPos][t]
                    retransSum += self.retransmissions[i+minPos][t]
                    TDsum += self.timeDelta[i+minPos][t]

                    tputValues.append(self.throughput[i+minPos][t])
                    rttValues.append(self.rtt[i + minPos][t])
                    cwndValues.append(self.cwnd[i + minPos][t])
                    rwndValues.append(float(self.rwnd[i + minPos][t]))
                    retransValues.append(float(self.retransmissions[i + minPos][t]))
                    TDvalues.append(float(self.timeDelta[i + minPos][t]))

                    num += 1

            #avgTput.append(tputSum / num)
            #avgRTT.append(rttSum / num)
            #avgCwnd.append(cwndSum / num / 1048576)  # Bytes to MBytes
            #avgRwnd.append(rwndSum / num / 1048576)  # Bytes to MBytes
            #avgRetrans.append(retransSum / num)
            avgTput.append(numpy.mean(tputValues))
            avgRTT.append(numpy.mean(rttValues))
            avgCwnd.append(numpy.mean(cwndValues) / 1048576)  # Bytes to MBytes
            avgRwnd.append(numpy.mean(rwndValues) / 1048576)  # Bytes to MBytes
            avgRetrans.append(numpy.mean(retransValues))
            avgTD.append(numpy.mean(TDvalues))
            # if t == 10:
                # print(numpy.mean(rwndValues))
            ciTput[0].append(calculateConfidenceInterval(tputValues, 0.95)[0])
            ciTput[1].append(calculateConfidenceInterval(tputValues, 0.95)[1])
            ciRTT[0].append(calculateConfidenceInterval(rttValues, 0.95)[0])
            ciRTT[1].append(calculateConfidenceInterval(rttValues, 0.95)[1])
            ciCwnd[0].append(calculateConfidenceInterval(cwndValues, 0.95)[0])
            ciCwnd[1].append(calculateConfidenceInterval(cwndValues, 0.95)[1])
            ciRwnd[0].append(calculateConfidenceInterval(rwndValues, 0.95)[0])
            ciRwnd[1].append(calculateConfidenceInterval(rwndValues, 0.95)[1])
            ciTD[0].append(calculateConfidenceInterval(TDvalues, 0.95)[0])
            ciTD[1].append(calculateConfidenceInterval(TDvalues, 0.95)[1])
            ciRetrans[0].append(calculateConfidenceInterval(retransValues, 0.95)[0])
            ciRetrans[1].append(calculateConfidenceInterval(retransValues, 0.95)[1])

        self.throughputAVG.append(avgTput)
        self.rttAVG.append(avgRTT)
        self.cwndAVG.append(avgCwnd)
        self.rwndAVG.append(avgRwnd)
        self.retransmissionsAVG.append(avgRetrans)
        self.timeDeltaAVG.append(avgTD)

        self.throughputCI.append(ciTput)
        self.rttCI.append(ciRTT)
        self.cwndCI.append(ciCwnd)
        self.rwndCI.append(ciRwnd)
        self.retransmissionsCI.append(ciRetrans)
        self.timeDeltaCI.append(ciTD)

    def plot3Tests(self, maxY=None):
        # self.filterCSVs()
        # self.removeTimeOffset()
        if maxY is None:
            # maxY = [None, None, None, None, None, None]
            maxY = [None, None, None, None, None]
        self.analyzeThreaded3()
        # self.calculateStats()
        self.avgAllData(0)
        self.avgAllData(1)
        self.avgAllData(2)

        # Setup formatting of plots
        fig, axs = pyplot.subplots(5, gridspec_kw={'height_ratios': [2, 1, 1, 1, 1]})
        fig.set_figheight(8)

        # for i in range(len(self.throughputAVG)):
        # axs[0].plot(self.secondsAVG[i], self.throughputAVG[i], '.', color='tab:blue')
        minLength = len(self.seconds[0])
        minIndex = 0
        for i in range(len(self.seconds)):
            if minLength > len(self.seconds[i]):
                minIndex = i
                minLength = len(self.seconds[i])
        axs[0].plot(self.seconds[minIndex], self.throughputAVG[0], color='tab:orange')
        axs[0].fill_between(self.seconds[minIndex], self.throughputCI[0][0],
                            self.throughputCI[0][1], color='tab:orange', alpha=.2)

        axs[1].plot(self.seconds[minIndex], self.rttAVG[0], color='tab:orange')
        axs[1].fill_between(self.seconds[minIndex], self.rttCI[0][0],
                            self.rttCI[0][1], color='tab:orange', alpha=.2)

        axs[2].plot(self.seconds[minIndex], self.rwndAVG[0], color='tab:orange')
        axs[2].fill_between(self.seconds[minIndex], numpy.array(self.rwndCI[0][0]) / 1048576,
                            numpy.array(self.rwndCI[0][1]) / 1048576, color='tab:orange', alpha=.2)

        axs[3].plot(self.seconds[minIndex], self.cwndAVG[0], color='tab:orange')
        axs[3].fill_between(self.seconds[minIndex], numpy.array(self.cwndCI[0][0]) / 1048576,
                            numpy.array(self.cwndCI[0][1]) / 1048576, color='tab:orange', alpha=.2)
        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[0], color='tab:orange')
        axs[4].fill_between(self.seconds[minIndex], self.retransmissionsCI[0][0],
                            self.retransmissionsCI[0][1], color='tab:orange', alpha=.2)

        # axs[5].plot(self.seconds[minIndex], self.timeDeltaAVG[0], color='tab:orange')
        # axs[5].fill_between(self.seconds[minIndex], self.timeDeltaCI[0][0],
        #                    self.timeDeltaCI[0][1], color='tab:orange', alpha=.2)

        axs[0].plot(self.seconds[minIndex], self.throughputAVG[1], color='tab:blue')
        axs[0].fill_between(self.seconds[minIndex], self.throughputCI[1][0],
                            self.throughputCI[1][1], color='tab:blue', alpha=.2)

        axs[1].plot(self.seconds[minIndex], self.rttAVG[1], color='tab:blue')
        axs[1].fill_between(self.seconds[minIndex], self.rttCI[1][0],
                            self.rttCI[1][1], color='tab:blue', alpha=.2)


        axs[2].plot(self.seconds[minIndex], self.rwndAVG[1], color='tab:blue')
        axs[2].fill_between(self.seconds[minIndex], numpy.array(self.rwndCI[1][0]) / 1048576,
                            numpy.array(self.rwndCI[1][1]) / 1048576, color='tab:blue', alpha=.2)

        axs[3].plot(self.seconds[minIndex], self.cwndAVG[1], color='tab:blue')
        axs[3].fill_between(self.seconds[minIndex], numpy.array(self.cwndCI[1][0]) / 1048576,
                            numpy.array(self.cwndCI[1][1]) / 1048576, color='tab:blue', alpha=.2)

        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[1], color='tab:blue')
        axs[4].fill_between(self.seconds[minIndex], self.retransmissionsCI[1][0],
                            self.retransmissionsCI[1][1], color='tab:blue', alpha=.2)

        axs[0].plot(self.seconds[minIndex], self.throughputAVG[2], color='tab:green')
        axs[0].fill_between(self.seconds[minIndex], self.throughputCI[2][0],
                            self.throughputCI[2][1], color='tab:green', alpha=.2)

        axs[1].plot(self.seconds[minIndex], self.rttAVG[2], color='tab:green')
        axs[1].fill_between(self.seconds[minIndex], self.rttCI[2][0],
                            self.rttCI[2][1], color='tab:green', alpha=.2)

        axs[2].plot(self.seconds[minIndex], self.rwndAVG[2], color='tab:green')
        axs[2].fill_between(self.seconds[minIndex], numpy.array(self.rwndCI[2][0]) / 1048576,
                            numpy.array(self.rwndCI[2][1]) / 1048576, color='tab:green', alpha=.2)

        axs[3].plot(self.seconds[minIndex], self.cwndAVG[2], color='tab:green')
        axs[3].fill_between(self.seconds[minIndex], numpy.array(self.cwndCI[2][0]) / 1048576,
                            numpy.array(self.cwndCI[2][1]) / 1048576, color='tab:green', alpha=.2)

        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[2], color='tab:green')
        axs[4].fill_between(self.seconds[minIndex], self.retransmissionsCI[2][0],
                            self.retransmissionsCI[2][1], color='tab:green', alpha=.2)

        # axs[5].plot(self.seconds[minIndex], self.timeDeltaAVG[2], color='tab:green')
        # axs[5].fill_between(self.seconds[minIndex], self.timeDeltaCI[2][0],
        #                                            self.timeDeltaCI[2][1], color='tab:green', alpha=.2)

        axs[0].set_ylim([0, 10.1])
        axs[1].set_ylim([0, 1.5])
        axs[2].set_ylim([0, 6])
        axs[3].set_ylim([0, 6])
        axs[4].set_ylim([0, 2])
        # axs[5].set_ylim([0, 1])

        for i in range(len(maxY)):
            if maxY[i] is not None:
                axs[i].set_ylim([0, maxY[i]])
            axs[i].set_xlim([0, len(self.seconds[minIndex])])

        fig.suptitle(self.title)
        fig.legend(self.legend)

        axs[0].set_ylabel("Throughput (Mb/s)")
        axs[1].set_ylabel("RTT (s)")
        axs[2].set_ylabel("RWND (MB)")
        axs[3].set_ylabel("CWND (MB)")
        axs[4].set_ylabel("Retrans. (%)")
        # axs[5].set_ylabel("Time between frames")

        axs[4].set_xlabel("Time (seconds)")
        # axs[4].set_xlabel("Time (seconds)")

        pyplot.savefig(self.plotFilepath)
        pyplot.show()

        flag = True
        if flag:
            print(f'Max Tput: {max(self.throughputAVG[0])}')
            print(f'Min RTT: {min(self.rttAVG[2])}')
            print(f'Max RTT: {max(self.rttAVG[2])}')
            print(f'Max cwnd: {max(self.cwndAVG[0])}')
            print(f'Max rwnd: {max(self.rwndAVG[0])}')
            print(f'Max retransmission rate: {max(self.retransmissionsAVG[2])}')
            print(f'Max time between frames: {max(self.timeDeltaAVG[1])}')

        for i in range(len(self.throughputAVG)):
            if i == 0:
                print("With Tuning")
            else:
                print("Without Tuning")
            print(f'Avg Throughput: {sum(self.throughputAVG[i]) / len(self.throughputAVG[i])}')
            print(f'Avg rtt: {sum(self.rttAVG[i]) / len(self.rttAVG[i])}')
            print(f'Avg rwnd size: {sum(self.rwndAVG[i]) / len(self.rwndAVG[i])}')
            print(f'Avg cwnd size: {sum(self.cwndAVG[i]) / len(self.cwndAVG[i])}')
            print(f'Avg Retransmission rate: {sum(self.retransmissionsAVG[i]) / len(self.retransmissionsAVG[i])}')
            print(f'Avg time between frames: {sum(self.timeDeltaAVG[i]) / len(self.timeDeltaAVG[i])}')

    def plotStart(self, seconds):
        if not self.retransmissionsAVG:
            self.analyzeThreaded()
            #self.calculateStats()
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
                theoreticalCWND[i] = 1500/1048576
                theoreticalTput[i] = (12000 / 1048576)/(avgRTT/1000)
            else:
                theoreticalCWND[i] = theoreticalCWND[i - 1] * 2
                # theoreticalTput[i] = theoreticalCWND[i]*8 / (avgRTT/1000)
                theoreticalTput[i] = theoreticalTput[i - 1] * 2

        pyplot.clf()
        fig, axs = pyplot.subplots(4, gridspec_kw={'height_ratios': [2, 1, 1, 1]})
        fig.set_figheight(8)

        axs[0].plot(theoreticalTime, theoreticalTput, 'k--')
        axs[0].plot(time, self.throughputAVG[0][0:seconds + 1], color='tab:orange')
        axs[0].fill_between(time, self.throughputCI[0][0][0:seconds+1],
                                  self.throughputCI[0][1][0:seconds+1], color='tab:orange', alpha=.2)
        axs[0].plot(time, self.throughputAVG[1][0:seconds + 1], color='tab:blue')
        axs[0].fill_between(time, self.throughputCI[1][0][0:seconds + 1],
                                  self.throughputCI[1][1][0:seconds + 1], color='tab:blue', alpha=.2)

        axs[1].plot(theoreticalTime, theoreticalCWND, 'k--')
        axs[1].plot(time, self.cwndAVG[0][0:seconds+1], color='tab:orange')
        axs[1].fill_between(time, numpy.array(self.cwndCI[0][0][0:seconds + 1])/1048576,
                                  numpy.array(self.cwndCI[0][1][0:seconds + 1])/1048576, color='tab:orange', alpha=.2)
        axs[1].plot(time, self.cwndAVG[1][0:seconds+1], color='tab:blue')
        axs[1].fill_between(time, numpy.array(self.cwndCI[1][0][0:seconds + 1])/1048576,
                                  numpy.array(self.cwndCI[1][1][0:seconds + 1])/1048576, color='tab:blue', alpha=.2)

        axs[2].plot(time, self.rwndAVG[0][0:seconds + 1], color='tab:orange')
        axs[2].fill_between(time, numpy.array(self.rwndCI[0][0][0:seconds + 1])/1048576,
                                  numpy.array(self.rwndCI[0][1][0:seconds + 1])/1048576, color='tab:orange', alpha=.2)
        axs[2].plot(time, self.rwndAVG[1][0:seconds + 1], color='tab:blue')
        axs[2].fill_between(time, numpy.array(self.rwndCI[1][0][0:seconds + 1])/1048576,
                                  numpy.array(self.rwndCI[1][1][0:seconds + 1])/1048576, color='tab:blue', alpha=.2)
        axs[3].plot(time, self.retransmissionsAVG[0][0:seconds + 1], color='tab:orange')
        axs[3].plot(time, self.retransmissionsAVG[1][0:seconds + 1], color='tab:blue')

        axs[0].set_ylabel("Throughput (Mb/s)")
        axs[1].set_ylabel("CWND (MBytes)")
        axs[2].set_ylabel("RWND (MBytes)")
        axs[3].set_ylabel('Retrans. (%)')

        axs[2].set_xlabel("Time (seconds)")
        legend = ['Theoretical'] + self.legend
        #fig.legend(self.legend)
        fig.suptitle(self.title)

        maxY = max(self.rwndAVG[0][0:seconds+1])
        #axs[0].set_ylim([0, max(self.throughputAVG[0][0:seconds+1])])
        axs[0].set_ylim([0,20])
        axs[0].set_xlim([0, seconds])
        #axs[1].set_ylim([0, maxY])
        axs[1].set_ylim([0, 3])
        axs[1].set_xlim([0, seconds])
        #axs[2].set_ylim([0, maxY])
        axs[2].set_ylim([0, 3])
        axs[2].set_xlim([0, seconds])
        axs[3].set_ylim([0,2])
        axs[3].set_xlim([0, seconds])

        pyplot.savefig(self.plotFilepath.replace('.png', '_Start_CWND.png'))
        pyplot.show()

    def plotStartTput(self, seconds):
        if not self.retransmissionsAVG:
            self.analyzeThreaded()
            # self.calculateStats()
            self.avgAllData(0)
            self.avgAllData(1)
        avgRTT = 0
        for i in range(len(self.rttAVG)):
            avgRTT += sum(self.rttAVG[i][0:seconds])
        avgRTT /= seconds * len(self.rttAVG)
        theoreticalTime = numpy.arange(0., seconds+1, avgRTT)
        theoreticalTput = numpy.copy(theoreticalTime)
        for i in range(len(theoreticalTime)):
            if i == 0:
                theoreticalTput[i] = 12000/1048576
            else:
                theoreticalTput[i] = theoreticalTput[i - 1] * 2
        time = numpy.arange(0., seconds+1, 1)
        pyplot.clf()
        # pyplot.plot(theoreticalTime, theoreticalTput, 'k--')
        pyplot.plot(time, self.throughputAVG[0][0:seconds+1], color='tab:orange')
        pyplot.plot(time, self.throughputAVG[1][0:seconds+1], color='tab:blue')
        pyplot.ylabel("Throughput (Mb/s)")
        pyplot.xlabel("Time (seconds)")
        legend = ['Theoretical'] + self.legend
        # pyplot.legend(legend)
        pyplot.suptitle(self.title)
        pyplot.ylim([0, 20])
        pyplot.xlim([0, seconds])
        pyplot.fill_between(time, self.throughputCI[0][0][0:seconds + 1],
                            self.throughputCI[0][1][0:seconds + 1], color='tab:orange', alpha=.2)
        pyplot.fill_between(time, self.throughputCI[1][0][0:seconds + 1],
                            self.throughputCI[1][1][0:seconds + 1], color='tab:blue', alpha=.2)

        pyplot.savefig(self.plotFilepath.replace('.png', '_Start_TPUT.png'))

        pyplot.show()

    def plotTimeDelta(self):
        # self.filterCSVs()
        # self.removeTimeOffset()
        if not self.retransmissionsAVG:
            self.analyzeThreaded()
            # self.calculateStats()
            self.avgAllData(0)
            self.avgAllData(1)

        pyplot.clf()
        pyplot.suptitle(self.title)
        minLength = len(self.seconds[0])
        minIndex = 0
        for i in range(int(self.numRuns * 2)):
            if minLength > len(self.seconds[i]):
                minIndex = i
                minLength = len(self.seconds[i])


        pyplot.plot(self.seconds[minIndex], numpy.array(self.timeDeltaAVG[0])*1000, color='tab:orange')
        pyplot.plot(self.seconds[minIndex], numpy.array(self.timeDeltaAVG[1])*1000, color='tab:blue')
        pyplot.legend(['double TBF filter', 'Rate arg'])
        pyplot.ylim([0, 20])

        pyplot.savefig(self.plotFilepath.replace('.png', '_time_delta.png'))
        pyplot.show()


    def plotALL(self, maxY=None, minRTT=550):
        # self.filterCSVs()
        # self.removeTimeOffset()
        if maxY is None:
            #maxY = [None, None, None, None, None, None]
            maxY = [None, None, None, None, None]
        self.analyzeThreaded()
        # self.calculateStats()
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
        axs[0].fill_between(self.seconds[minIndex], self.throughputCI[0][0],
                                                    self.throughputCI[0][1], color='tab:orange', alpha=.2)

        axs[1].plot(self.seconds[minIndex], self.rttAVG[0], color='tab:orange')

        axs[2].plot(self.seconds[minIndex], self.rwndAVG[0], color='tab:orange')
        axs[2].fill_between(self.seconds[minIndex], numpy.array(self.rwndCI[0][0])/1048576,
                                                    numpy.array(self.rwndCI[0][1])/1048576, color='tab:orange', alpha=.2)

        axs[3].plot(self.seconds[minIndex], self.cwndAVG[0], color='tab:orange')
        axs[3].fill_between(self.seconds[minIndex], numpy.array(self.cwndCI[0][0])/1048576,
                                                    numpy.array(self.cwndCI[0][1])/1048576, color='tab:orange', alpha=.2)
        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[0], color='tab:orange')

        #axs[5].plot(self.seconds[minIndex], self.timeDeltaAVG[0], color='tab:orange')
        #axs[5].fill_between(self.seconds[minIndex], self.timeDeltaCI[0][0],
        #                    self.timeDeltaCI[0][1], color='tab:orange', alpha=.2)

        axs[0].plot(self.seconds[minIndex], self.throughputAVG[1], color='tab:blue')
        axs[0].fill_between(self.seconds[minIndex], self.throughputCI[1][0],
                                                    self.throughputCI[1][1], color='tab:blue', alpha=.2)

        axs[1].plot(self.seconds[minIndex], self.rttAVG[1], color='tab:blue')

        axs[2].plot(self.seconds[minIndex], self.rwndAVG[1], color='tab:blue')
        axs[2].fill_between(self.seconds[minIndex], numpy.array(self.rwndCI[1][0])/1048576,
                                                    numpy.array(self.rwndCI[1][1])/1048576, color='tab:blue', alpha=.2)

        axs[3].plot(self.seconds[minIndex], self.cwndAVG[1], color='tab:blue')
        axs[3].fill_between(self.seconds[minIndex], numpy.array(self.cwndCI[1][0])/1048576,
                                                    numpy.array(self.cwndCI[1][1])/1048576, color='tab:blue', alpha=.2)

        axs[4].plot(self.seconds[minIndex], self.retransmissionsAVG[1], color='tab:blue')

        #axs[5].plot(self.seconds[minIndex], self.timeDeltaAVG[1], color='tab:blue')
        #axs[5].fill_between(self.seconds[minIndex], self.timeDeltaCI[1][0],
        #                                            self.timeDeltaCI[1][1], color='tab:blue', alpha=.2)

        axs[0].set_ylim([0, 10.1])
        axs[1].set_ylim([0, 1.5])
        axs[2].set_ylim([0, 6])
        axs[3].set_ylim([0, 6])
        axs[4].set_ylim([0, 2])
        #axs[5].set_ylim([0, 1])


        for i in range(len(maxY)):
            if maxY[i] is not None:
                axs[i].set_ylim([0, maxY[i]])
            axs[i].set_xlim([0, len(self.seconds[minIndex])])

        fig.suptitle(self.title)
        # fig.legend(self.legend)

        axs[0].set_ylabel("Throughput (Mb/s)")
        axs[1].set_ylabel("RTT (s)")
        axs[2].set_ylabel("RWND (MB)")
        axs[3].set_ylabel("CWND (MB)")
        axs[4].set_ylabel("Retrans. (%)")
        #axs[5].set_ylabel("Time between frames")

        axs[4].set_xlabel("Time (seconds)")
        #axs[4].set_xlabel("Time (seconds)")

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
            print(f'Max time between frames: {max(self.timeDeltaAVG[1])}')

        for i in range(len(self.throughputAVG)):
            if i == 0:
                print("With Tuning")
            else:
                print("Without Tuning")
            print(f'Avg Throughput: {sum(self.throughputAVG[i])/len(self.throughputAVG[i])}')
            print(f'Avg rtt: {sum(self.rttAVG[i]) / len(self.rttAVG[i])}')
            print(f'Avg rwnd size: {sum(self.rwndAVG[i]) / len(self.rwndAVG[i])}')
            print(f'Avg cwnd size: {sum(self.cwndAVG[i]) / len(self.cwndAVG[i])}')
            print(f'Avg Retransmission rate: {sum(self.retransmissionsAVG[i]) / len(self.retransmissionsAVG[i])}')
            print(f'Avg time between frames: {sum(self.timeDeltaAVG[i])/len(self.timeDeltaAVG[i])}')


    def calculateStatsRTT(self, data, pipe, pSem, count):

        df = data
        timeOffset = df['time'][0]
        df['time'] -= timeOffset
        cutOffTime = 0.01
        seconds = []

        throughput = []
        avgthroughput = 0
        throughputSum = 0
        throughputCount = 0

        rtt = []
        avgRTT = 0
        RTTSum = 0
        RTTCount = 0

        cwnd = []
        avgCwnd = 0
        cwndSum = 0
        cwndCount = 0

        # serverCount = 0
        clientCount = 0
        prevTime = 0

        startFrame = 1
        minRTT = sys.maxsize
        ssExit = 0
        flag = False

        for j in range(len(df)):

            if not pandas.isnull(df['packets_out'].iloc[j]):
                # Calculate RTT by calculating number of bits in flight (packets*mss*8) and dividing by the RTT im ms
                throughputSum += ((df['packets_out'].iloc[j]*(df['mss'].iloc[j]*8))/(df['sampleRTT'].iloc[j]/1000))/1024/1024
                throughputCount += 1

            # Only look at packets that have data bout CWND
            if not pandas.isnull(df['cwnd'].iloc[j]):
               cwndCount += 1
               cwndSum += df['cwnd'].iloc[j]
               # rolling avg for CWND est.
                # if avgCwnd != 0:
                   # avgCwnd = (avgCwnd + df['tcp.analysis.bytes_in_flight'].iloc[j]) / 2
                # else:
                    # avgCwnd = df['tcp.analysis.bytes_in_flight'].iloc[j]

            if not flag and not pandas.isnull(df['exit'].iloc[j]):
                if df['exit'].iloc[j]:
                    ssExit = df['time'].iloc[j]
                    flag = True

            if not pandas.isnull(df['sampleRTT'].iloc[j]):
                RTTCount += 1
                RTTSum += df['sampleRTT'].iloc[j]
                if df['sampleRTT'].iloc[j] < minRTT:
                    minRTT = df['sampleRTT'].iloc[j]
            # rolling avg for RTT est.
            # if avgRTT != 0:
               # avgRTT = (avgRTT + df['tcp.analysis.ack_rtt'].iloc[j]) / 2
            # else:
               # avgRTT = df['tcp.analysis.ack_rtt'].iloc[j]

            # rolling avg for RWND est.
            # if avgRwnd != 0:
                # avgRwnd = (avgRwnd + df['tcp.window_size'].iloc[j]) / 2
            # else:
                # avgRwnd = df['tcp.window_size'].iloc[j]

            if df['time'].iloc[j] > float(cutOffTime):
                seconds.append(cutOffTime)
                if throughputCount == 0:
                    throughput.append(0)
                else:
                    throughput.append(throughputSum/throughputCount)
                if RTTCount == 0:
                     rtt.append(0)
                else:
                    rtt.append((RTTSum/RTTCount))
                if cwndCount == 0:
                    cwnd.append(0)
                else:
                     cwnd.append(cwndSum/cwndCount)

                throughputSum = 0
                throughputCount = 0
                RTTSum = 0
                RTTCount = 0
                cwndSum = 0
                cwndCount = 0
                cutOffTime += 0.01


        results = (count, throughput, rtt, cwnd, seconds,minRTT, ssExit)
        self.throughput.append(throughput)
        self.rtt.append(rtt)
        self.cwnd.append(cwnd)
        self.seconds.append(seconds)
        self.minRTT.append(minRTT)
        self.ssExit.append(ssExit)
        print(f"{count}: Results Ready")
        # pSem.acquire()
        pipe.send(results)
        pipe.close()
        # pSem.release()


    def analyzeThreadedRTT(self):
        results = []
        processes = []
        parentPipes = []
        # Create threads
        sortedData = []
        for df, i in zip(self.data, range(len(self.data))):
            if i % 2 == 0:
                # is even (tuning enabled)
                sortedData.append(df)
        for df, i in zip(self.data, range(len(self.data))):
            if i % 2 == 1:
                # is odd (tuning disabled)
                sortedData.append(df)
        self.data = sortedData
        for df, i in zip(self.data, range(len(self.data))):
            self.throughput.append([])
            self.rtt.append([])
            self.cwnd.append([])
            self.seconds.append([])
            parentPipe, childPipe = Pipe()
            parentPipes.append(parentPipe)
            p = Process(target=self.calculateStatsRTT, args=(df, childPipe, self.producerSem, i))
            p.start()
            processes.append(p)
        # Get results from threads
        for conn in parentPipes:
            # self.consumerSem.acquire()
            results.append(conn.recv())
            # self.consumerSem.release()
        # wait for threads to finish and join them
        for p in processes:
            p.join()
        # put results in the right order
        for result in results:
            i = result[0]
            throughput = result[1]
            rtt = result[2]
            cwnd = result[3]
            seconds = result[4]
            minRTT = result[5]
            ssExit = result[6]
            self.throughput[i] = throughput
            self.rtt[i] = rtt
            self.cwnd[i] = cwnd
            self.seconds[i] = seconds
            self.minRTT.append(minRTT)
            self.ssExit.append(ssExit)

    def removeTimeOffsetPing(self):
        minTime = self.data[1]['tSent_abs'].iloc[0]
        print(f'minTime is: {minTime}')
        self.data[1]['tSent_abs'] = self.data[1]['tSent_abs'] - minTime
        self.data[0]['time'] = self.data[0]['time'] - minTime


    def avgAllDataRTT(self, startPos):
        minLength = len(self.rtt[0])
        minPos = startPos * self.numRuns
        avgTput = []
        avgRTT = []
        avgCwnd = []

        ciTput = [[], []]
        ciRTT = [[], []]
        ciCwnd = [[], []]
        for i in range(len(self.rtt)):
            if minLength > len(self.rtt[i]):
                minLength = len(self.rtt[i])
        for t in range(minLength):
            rttSum = 0
            cwndSum = 0
            tputSum = 0

            rttValues = []
            cwndValues = []
            tputValues = []
            num = 0
            for i in range(self.numRuns):
                if len(self.rtt[i]) > t:
                    rttSum += self.rtt[i+minPos][t]
                    cwndSum += self.cwnd[i+minPos][t]
                    tputSum += self.throughput[i+minPos][t]

                    rttValues.append(self.rtt[i + minPos][t])
                    cwndValues.append(self.cwnd[i + minPos][t])
                    tputValues.append(self.throughput[i + minPos][t])

                    num += 1

            #avgRTT.append(rttSum / num)
            #avgCwnd.append(cwndSum / num / 1048576)  # Bytes to MBytes
            #avgRwnd.append(rwndSum / num / 1048576)  # Bytes to MBytes
            #avgRetrans.append(retransSum / num)
            avgRTT.append(numpy.mean(rttValues))
            avgCwnd.append(numpy.mean(cwndValues))  # Bytes to MBytes
            avgTput.append(numpy.mean(tputValues))
            # if t == 10:
                # print(numpy.mean(rwndValues))

            ciRTT[0].append(calculateConfidenceInterval(rttValues, 0.95)[0])
            ciRTT[1].append(calculateConfidenceInterval(rttValues, 0.95)[1])
            ciCwnd[0].append(calculateConfidenceInterval(cwndValues, 0.95)[0])
            ciCwnd[1].append(calculateConfidenceInterval(cwndValues, 0.95)[1])
            ciTput[0].append(calculateConfidenceInterval(tputValues, 0.95)[0])
            ciTput[1].append(calculateConfidenceInterval(tputValues, 0.95)[1])

        self.rttAVG.append(avgRTT)
        self.cwndAVG.append(avgCwnd)
        self.throughputAVG.append(avgTput)

        if numpy.count_nonzero(self.ssExit):
            self.ssExitAVG = sum(self.ssExit)/numpy.count_nonzero(self.ssExit)
        self.minRTTAVG = numpy.mean(self.minRTT)

        self.rttCI.append(ciRTT)
        self.cwndCI.append(ciCwnd)
        self.throughputCI.append(ciTput)

    def calculateStatsSingle(self):
        df = self.data[0]
        cutOffTime = 1
        bytesSent = 0
        throughput = []
        seconds = []

        rtt = []
        RTTSum = 0
        RTTCount = 0

        cwnd = []
        cwndSum = 0
        cwndCount = 0

        clientCount = 0


        for j in range(len(df)):
            # only packets from the Server
            if df['tcp.srcport'].iloc[j] == 5201:
                # serverCount += 1
                # Track bytes sent for tput calc
                bytesSent += df['frame.len'].iloc[j]

                # Only look at packets that have data bout CWND
                if not pandas.isnull(df['tcp.analysis.bytes_in_flight'].iloc[j]):
                    cwndCount += 1
                    cwndSum += df['tcp.analysis.bytes_in_flight'].iloc[j]/1024/1024

                    # rolling avg for CWND est.
                    # if avgCwnd != 0:
                    # avgCwnd = (avgCwnd + df['tcp.analysis.bytes_in_flight'].iloc[j]) / 2
                    # else:
                    # avgCwnd = df['tcp.analysis.bytes_in_flight'].iloc[j]

            # only packets from the Client
            if df['tcp.dstport'].iloc[j] == 5201:
                clientCount += 1

                if not pandas.isnull(df['tcp.analysis.ack_rtt'].iloc[j]):
                    RTTCount += 1
                    RTTSum += df['tcp.analysis.ack_rtt'].iloc[j]

                # rolling avg for RTT est.
                # if avgRTT != 0:
                # avgRTT = (avgRTT + df['tcp.analysis.ack_rtt'].iloc[j]) / 2
                # else:
                # avgRTT = df['tcp.analysis.ack_rtt'].iloc[j]

                # rolling avg for RWND est.
                # if avgRwnd != 0:
                # avgRwnd = (avgRwnd + df['tcp.window_size'].iloc[j]) / 2
                # else:
                # avgRwnd = df['tcp.window_size'].iloc[j]

            if df['tcp.time_relative'].iloc[j] > float(cutOffTime):
                throughput.append((bytesSent * 8) / 1048576)
                seconds.append(cutOffTime)
                if RTTCount == 0:
                    rtt.append(0)
                else:
                    rtt.append((RTTSum / RTTCount))
                if cwndCount == 0:
                    cwnd.append(0)
                else:
                    cwnd.append(cwndSum / cwndCount)



                bytesSent = 0
                RTTSum = 0
                RTTCount = 0
                cwndSum = 0
                cwndCount = 0
                clientCount = 0
                cutOffTime += 1

        self.throughput = throughput
        self.rtt = rtt
        self.cwnd = cwnd
        self.seconds = seconds
        print(f"Results Ready")

    def plotOnetcpdump(self):
        self.calculateStatsSingle()
        #self.removeTimeOffsetPing()
        fig, axs = pyplot.subplots(3, gridspec_kw={'height_ratios': [3, 3, 3]})
        fig.set_figheight(8)

        # throughput = (self.data[0]['packets_out'] * (self.data[0]['mss'] * 8)) / (self.data[0]['sampleRTT'] / 1000) / 1024 / 1024
        axs[0].plot(self.seconds, self.throughput, color='tab:orange')
        # axs[1].plot(self.data[1]['tSent_abs'], self.data[1]['rtt'], color='tab:blue')
        axs[1].plot(self.seconds, self.rtt, color='tab:orange')
        axs[2].plot(self.seconds, self.cwnd, color='tab:orange')

        fig.suptitle("Jul 13, 2020")
        # fig.legend(['TCP Flow (mlcnetb)', 'UDP Ping (mlcneta)'])

        axs[0].set_ylabel("Throughput (Mbits/s)")
        axs[1].set_ylabel("RTT (Secons)")
        axs[2].set_ylabel("CWND (MB)")
        axs[2].set_xlabel("Time (seconds)")

        axs[0].set_ylim(bottom=0)
        axs[1].set_ylim(bottom=0)
        axs[2].set_ylim(bottom=0)
        axs[0].set_xlim(xmin=0)
        axs[1].set_xlim(xmin=0)
        axs[2].set_xlim(xmin=0)
        #axs[0].set_xlim(xmax=self.data[1]['tSent_abs'].iloc[-1])
        #axs[1].set_xlim(xmax=self.data[1]['tSent_abs'].iloc[-1])
        #axs[2].set_xlim(xmax=self.data[1]['tSent_abs'].iloc[-1])

        pyplot.savefig(self.plotFilepath)
        pyplot.show()

    def update(slef, existingAggregate, newValue):
        (count, mean, M2) = existingAggregate
        count += 1
        delta = newValue - mean
        mean += delta / count
        delta2 = newValue - mean
        M2 += delta * delta2
        return (count, mean, M2)

    # Retrieve the mean, variance and sample variance from an aggregate
    def finalize(self, existingAggregate):
        (count, mean, M2) = existingAggregate
        if count < 2:
            return float("nan")
        else:
            (mean, variance, sampleVariance) = (mean, M2 / count, M2 / (count - 1))
            return (mean, variance, sampleVariance)

    def calculateSdev(self):
        aggregate = (0, 0, 0)
        sdev = []
        for rtt in self.data['sampleRTT']:
            aggregate = self.update(aggregate, rtt)
            sdev.append(self.finalize(aggregate)[1])
        return sdev




    pass

    def mdev_vs_sdev(self, title):
        sdev = self.calculateSdev()

        # Setup formatting of plots
        fig, axs = pyplot.subplots(1, gridspec_kw={'height_ratios': [3]})
        fig.set_figheight(4)

        axs[0].plot(self.data['time'], self.data['mdev'], color='tab:orange')
        axs[0].plot(self.data['time'], sdev, color='tab:blue')
        axs[0].plot(self.data['time'], self.data['sampleRTT'], color='black', alpha=0.8)

        fig.suptitle("Hystart Disabled")
        fig.legend(self.legend)
        axs[0].set_ylabel("Variance")

        axs[0].set_ylim(bottom=0)
        axs[0].set_xlim(xmin=0)
        pyplot.savefig(self.plotFilepath)
        pyplot.show()


if __name__ == "__main__":
    plot = PlotTputOneFlow("hybla", "C:\satellite-research/cubic_2021_04_13-20-28-37.csv", "C:/satellite-research/cubicTput")
    plot.plotTput()
    # plot = PlotRTTOneFlow("hybla", "C:/research/hybla_2021_04_12-23-07-43.csv", "C:/research/hyblaRTT")
    # plot.plotRTT()
    # csvs = ["C:/research/hybla_2021_04_12-23-07-43.csv", "C:/research/hybla_2021_04_12-23-07-46.csv"]
    # legend = ["Server", "Client"]
    # plot = PlotTputCompare("hybla", legend, csvs, "C:/research/hyblaCompareTput")
    # plot.plotTput()
