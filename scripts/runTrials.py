# This script was adapted from work by Kush Shah whos work can be 
# found at https://github.com/kush5683/TCP-over-Satellite/blob/main/MediatorCode/trial.py

import argparse
import sys
import os
import time
import subprocess
import datetime
from datetime import datetime


class Trial:

    def __init__(self, cc, batchNum, runNum,
                 user='btpeters', data='20M', timeout=600, log=False, ports=['5201', '5202'],
                 tcp_mem=60000000, tcp_wmem=60000000, tcp_rmem=60000000):
        self.dictionary = {}
        self.hosts = []
        self.cc = cc
        self.data = data
        self.batchNum = batchNum
        self.runNum = runNum
        self.user = user
        self.pcaps = []
        self.clientPcaps = []
        self.csvs = []
        self.commandsRun = []
        self.log = log
        self.timeout = timeout
        self.ports = ports
        self.serversRunning = 0
        self.clientsRunning = 0
        self.clientDumpsRunning = 0
        self.tcpdumpsRunning = 0
        self.pcapsSent = 0
        self.csvsGenerated = 0
        self.done = False
        self.tcp_mem = tcp_mem
        self.tcp_wmem = tcp_wmem
        self.tcp_rmem = tcp_rmem
        self.setupCommand = [
            f'sudo sysctl -w net.ipv4.tcp_mem=\'{self.tcp_mem}\'',
            f'sudo sysctl -w net.ipv4.tcp_wmem=\'{self.tcp_wmem}\'',
            f'sudo sysctl -w net.ipv4.tcp_rmem=\'{self.tcp_rmem}\'',
            # 'sudo sysctl -p'
        ]
        self.graphCommand = ''

    def setHosts(self):
        self.dictionary = {
            "cubic": "mlcneta.cs.wpi.edu",
            "hybla": "mlcnetb.cs.wpi.edu",
            "bbr": "mlcnetc.cs.wpi.edu",
            "pcc": "mlcnetd.cs.wpi.edu"
        }

        # for use if running two downloads at once

        # if self.cc[0] == self.cc[1]:
        #    self.hosts.append(dictionary.get(self.cc[0]))
        #    self.hosts.append(dictionary.get('same'))
        #    command = f'ssh {self.user}@mlcnetd.cs.wpi.edu \"sudo sysctl -w net.ipv4.tcp_congestion_control=\'{self.cc[1]}\'\"'

        for c in self.cc:
            self.hosts.append(self.dictionary.get(c))
        print(self.cc)
        print(self.hosts)

    def setUpLocal(self):
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        # hystart = f'{sshPrefix} \"sudo echo 0 > /sys/module/tcp_cubic/parameters/hystart\"'
        # os.system(hystart)

        for command in self.setupCommand:
            os.system(f'{sshPrefix} \"{command}\"')
        filePrefix = f'Trial_{self.batchNum}'
        os.system(f'mkdir {filePrefix}')
        os.system(f'{sshPrefix} \"mkdir {filePrefix}\"')
        for host in self.hosts:
            os.system(f'ssh {self.user}@{host} \"mkdir {filePrefix}\"')
        os.system(f'mkdir {filePrefix}/pcaps')
        os.system(f'mkdir {filePrefix}/csvs')
        os.system(f'mkdir {filePrefix}/plots')
        #os.system(f'{sshPrefix} \'mkdir figures/stats/trial-{self.batchNum}\'')

        os.chdir(f'{filePrefix}')

    def setProtocolsRemote(self):
        # hosts = ['mlcneta', 'mlcnetb', 'mlcnetc', 'mlcnetd']
        protocols = ['cubic', 'hybla', 'bbr', 'pcc']
        for host in self.hosts:
            sshPrefix = f'ssh {self.user}@{host}'
            for command in self.setupCommand:
                os.system(f'{sshPrefix} \'{command}\'')
            hystart = f'{sshPrefix} \"sudo echo 0 > /sys/module/tcp_cubic/parameters/hystart\"'
        # os.system(hystart)
        for i in range(len(self.hosts)):
             protocol = list(self.dictionary.keys())[list(self.dictionary.values()).index(self.hosts[i])]
             command = f'ssh {self.user}@{self.hosts[i]} \"sudo sysctl -w net.ipv4.tcp_congestion_control=\'{protocol}\'\"'
             os.system(command)
             self.commandsRun.append(command)
        return

    def sleep(self, sec):
        for i in range(1, sec + 1):
            print(f'\tTime left to sleep {sec + 1 - i} seconds')
            time.sleep(1)

    def getTimeStamp(self):
        return datetime.now().strftime('%Y_%m_%d-%H-%M-%S')

    def startIperf3Server(self):
        for host in self.hosts:
            iperf3ServerStart = f"ssh {self.user}@{host} \"iperf3 -s &\"&"
            self.serversRunning += 1
            print(f'\trunning command: \n {iperf3ServerStart}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ServerStart)
            self.commandsRun.append((timeStamp, iperf3ServerStart))
            # self.sleep(1)

    def startIperf3Client(self):
        time1 = time.time()
        exitCodes = []
        for host in self.hosts:
            # exitCodes.append(subprocess.Popen(["ssh", f"{self.user}@glomma.cs.wpi.edu", "iperf3", "--reverse", "-i", "\"eno2\"",
            #                                    "-c", f"{host}", f"-n{self.data}", f"-p{self.ports[self.clientsRunning]}"], stdout=subprocess.DEVNULL))
            iperf3ClientStartCommand = f"ssh {self.user}@glomma.cs.wpi.edu \'iperf3 -i 30 -R -c {host} -n {self.data} > /dev/null\'"
            self.clientsRunning += 1
            print(f'\trunning command: \n{iperf3ClientStartCommand}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ClientStartCommand)
            self.commandsRun.append((timeStamp, iperf3ClientStartCommand))
        #self.sleep(self.timeout)
        # while exitCodes[0].poll() is None or exitCodes[1].poll() is None:
        #     if time.time() - time1 > 600.0:
        #         break
        #     pass

    def startTcpdumpServer(self):
        for host in self.hosts:
            timeStamp = self.getTimeStamp()
            filename = f'Trial_{self.batchNum}/{self.cc[self.tcpdumpsRunning]}_{timeStamp}.pcap'
            tcpdump = f"ssh {self.user}@{host} \"sudo tcpdump -s 96 port {self.ports[self.tcpdumpsRunning]} -w '{filename}'\"&"
            self.tcpdumpsRunning += 1
            print(f'\trunning command: \n{tcpdump}')
            os.system(tcpdump)
            self.commandsRun.append((timeStamp, tcpdump))
            self.pcaps.append(filename)
            self.sleep(3)

    def startTcpdumpClient(self):
        timestamp = self.getTimeStamp()
        filename = f'Trial_{self.batchNum}/{self.cc[self.clientDumpsRunning]}_{timestamp}.pcap'
        tcpdump = f'ssh {self.user}@glomma.cs.wpi.edu \"sudo tcpdump -i 2 -w {filename} port {self.ports[self.clientsRunning]} -s 96\"&'
        self.clientDumpsRunning += 1
        print(f'\trunning command: \n{tcpdump}')
        os.system(tcpdump)
        self.commandsRun.append((timestamp, tcpdump))
        self.clientPcaps.append(filename)
        self.sleep(3)

    def getPcaps(self):
        for file in self.pcaps:
            host = self.hosts[self.pcapsSent]
            scpFromServer = f'scp -i ~/.ssh/id_rsa {self.user}@{host}:~/{file} ~/Research/Trial_{self.batchNum}/pcaps&'
            print(f'\trunning command: \n{scpFromServer}')
            timeStamp = self.getTimeStamp()
            os.system(scpFromServer)
            self.commandsRun.append((timeStamp, scpFromServer))
            self.sleep(3)
            #scpToCS = f'scp {self.user}@{host}:~/{file} ~/SatelliteCode/trial-{self.batchNum}'
            #scpFromCS = f'scp ~/SatelliteCode/trial-{self.batchNum}/{file} {self.user}@glomma.cs.wpi.edu:~/{host[:7]}/pcap/trial-{self.batchNum}/{file}'
            #print(f'\trunning command: \n{scpToCS}')
            #timeStamp = self.getTimeStamp()
            #os.system(scpToCS)
            #self.commandsRun.append((timeStamp, scpToCS))
            #self.sleep(3)
            #print(f'\trunning command: \n{scpFromCS}')
            #timeStamp = self.getTimeStamp()
            #os.system(scpFromCS)
            #self.commandsRun.append((timeStamp, scpFromCS))
            self.pcapsSent += 1
        for file in self.clientPcaps:
            host = "glomma.cs.wpi.edu"
            scpFromClient = f'scp -i ~/.ssh/id_rsa {self.user}@{host}:~/{file} ~/Research/Trial_{self.batchNum}/pcaps&'
            print(f'\trunning command: \n{scpFromClient}')
            timeStamp = self.getTimeStamp()
            os.system(scpFromClient)
            self.commandsRun.append((timeStamp, scpFromClient))
            self.sleep(3)

    def pcapToCsv(self):
        files = os.listdir("pcaps")
        # files = [f for f in os.listdir("pcaps") if os.path.isfile("pcaps/".join(f))]
        for file in files:
            #host = f'{self.hosts[self.csvsGenerated][:7]}'
            csvFilename = file.split('.')[0] + '.csv'
            tshark = f'echo \
                    \"time,frame.len,protocol,srcPort,dstPort,seq,ack,len,rtt,fin\" \
                    > csvs/{csvFilename} && \
                    tshark -r pcaps/{file} -Y "tcp.stream==1" \
                    -T fields\
                    -e frame.time_relative \
                    -e frame.len \
                    -e tcp \
                    -e tcp.analysis.ack_rtt \
                    -e tcp.flags.fin \
                    -E separator=, \
                    -E occurrence=f \
                    >> csvs/{csvFilename}'

            """
            -e frame.number \
            -e frame.len \
            -e tcp.window_size \
            -e ip.src \
            -e ip.dst \
            -e tcp.srcport \
            -e tcp.dstport \
            -e frame.time \
            -E header=y \
            -E separator=, \
            -E quote=d \
            -E occurrence=f \
            """
            # fullCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'{tshark}\''
            self.csvs.append(csvFilename)
            print(f'\trunning command: \n{tshark}')
            timeStamp = self.getTimeStamp()
            os.system(tshark)
            self.commandsRun.append((timeStamp, tshark))
            self.csvsGenerated += 1
            self.sleep(5)

    def makeLogFile(self):
        timeStamp = self.getTimeStamp()
        filename = f'{timeStamp}-command-log.txt'
        f = open(filename, "x")
        for command in self.commandsRun:
            f.write(f'{command[0]} : {command[1]}\n')
        f.close()

    def terminateCommands(self):
        commands = ['iperf3', 'tcpdump']
        for host in self.hosts:
            for command in commands:
                pkill = f'ssh {self.user}@{host} \"sudo pkill -2 {command}\"'
                timeStamp = self.getTimeStamp()
                os.system(pkill)
                self.commandsRun.append((timeStamp, pkill))
        pkill = f'ssh {self.user}@glomma.cs.wpi.edu \"sudo pkill -2 tcpdump\"'
        timeStamp = self.getTimeStamp()
        os.system(pkill)
        self.commandsRun.append((timeStamp, pkill))

    def cleanUp(self):
        self.terminateCommands()
        if self.done:
            os.system(f'rm -r pcaps')
            for host in self.hosts:
                remove = f'ssh {self.user}@{host} \'sudo rm -r Trial_{self.batchNum}\''
                os.system(remove)
            remove = f'ssh {self.user}@glomma.cs.wpi.edu \'sudo rm -r Trial_{self.batchNum}\''
            os.system(remove)
            if self.log:
                self.makeLogFile()

    def generateGraphs(self):
        # hostA_filename = f"{self.hosts[0][:7]}/pcap/trial-{self.batchNum}/{self.pcaps[0]}"
        # hostB_filename = f"{self.hosts[1][:7]}/pcap/trial-{self.batchNum}/{self.pcaps[1]}"
        # runScript = f'ssh {self.user}@glomma.cs.wpi.edu python3 graph.py {hostA_filename} {hostB_filename} {self.cc[0]} {self.cc[1]} {self.batchNum} {self.runNum} {self.hosts[0][:7]} {self.hosts[1][:7]}'
        files = os.listdir("csvs")
        # files = [f for f in os.listdir("csvs") if os.path.isfile("csvs/".join(f))]
        for file in files:
            csvFilename = os.path.realpath("csvs/" + file)
            plotFilename = csvFilename.replace("/csvs/","/plots/").replace(".csv","_RTT.png")
            runScript = f'Rscript --vanilla ~/Research/AnalysisTools/plotRTT.R {csvFilename} {plotFilename} &'
            print(f'\trunning command: \n{runScript}')
            timeStamp = self.getTimeStamp()
            os.system(runScript)
            self.commandsRun.append((timeStamp, runScript))
            self.sleep(3)

            plotFilename = plotFilename.replace("RTT", "TPUT")
            runScript = f'Rscript --vanilla ~/Research/AnalysisTools/plotThroughput.R {csvFilename} {plotFilename} &'
            print(f'\trunning command: \n{runScript}')
            timeStamp = self.getTimeStamp()
            os.system(runScript)
            self.commandsRun.append((timeStamp, runScript))
            self.sleep(3)

    # timeStamp = self.getTimeStamp()
    # os.system(runScript)
    # self.commandsRun.append(runScript)

    def start(self):
        os.chdir(os.path.expanduser("~/Research"))
        os.system('clear')
        print('Running setHosts()')
        self.setHosts()
        print("Running cleanUp()")
        self.cleanUp()
        if self.runNum == 0:
            print("Running setupLocal()")
            self.setUpLocal()
            print("Running setProtocolsRemote()")
            self.setProtocolsRemote()
        print("Running startIperf3Server()")
        self.startIperf3Server()
        print("Running startTcpdumpServer()")
        self.startTcpdumpServer()
        print("Running startTcpdumpClient()")
        self.startTcpdumpClient()
        print("Running startIperf3Client()")
        self.startIperf3Client()
        # print("Sleeping")
        # self.sleep(self.timeout)
        print('Killing tcpdump and iperf3')
        self.terminateCommands()
        print("Getting pcaps")
        self.getPcaps()
        print("Running pcapToCsv()")
        self.pcapToCsv()  # move to other file
        print('Generating graphs')
        self.generateGraphs()  # move to other file
        self.done = True
        print("Running cleanUp()")
        self.cleanUp()
        return self.graphCommand


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, help='What batch number is this',required=True)
    parser.add_argument('--log', type=bool, help='Use logging output', default=True)
    parser.add_argument('--cc', type=str, help="congestion control algorithm",required=True)
    parser.add_argument('--runNum', type=int, help="what run number is this", required=True)
    args = parser.parse_args()

    cc = []

    for c in args.cc.split(" "):
        cc.append(c)

    # machines = ['mlcneta.cs.wpi.edu', 'mlcnetb.cs.wpi.edu',
    #             'mlcnetc.cs.wpi.edu', 'mlcnetd.cs.wpi.edu']

    # t = Trial(data='1G', cc=['cubic', 'hybla'],
    #          batchNum=111, timeout=100, log=True)

    t = Trial(data='250M', batchNum=args.batch, timeout=100, log=args.log, cc=cc, runNum=args.runNum)
    t.start()
    print("All done")


if __name__ == "__main__":
    main()
