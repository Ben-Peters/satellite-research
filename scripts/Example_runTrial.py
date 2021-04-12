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
        self.cc = cc
        self.data = data
        self.batchNum = batchNum
        self.runNum = runNum
        self.user = user
        self.pcaps = []
        self.csvs = []
        self.commandsRun = []
        self.log = log
        self.timeout = timeout
        self.ports = ports
        self.serversRunning = 0
        self.clientsRunning = 0
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
        self.hosts = []
        dictionary = {
            "cubic": "mlcneta.cs.wpi.edu",
            "bbr": "mlcnetb.cs.wpi.edu",
            "hybla": "mlcnetc.cs.wpi.edu",
            "same": "mlcnetd.cs.wpi.edu"
        }

        if self.cc[0] == self.cc[1]:
            self.hosts.append(dictionary.get(self.cc[0]))
            self.hosts.append(dictionary.get('same'))
            command = f'ssh {self.user}@mlcnetd.cs.wpi.edu \"sudo sysctl -w net.ipv4.tcp_congestion_control=\'{self.cc[1]}\'\"'
        else:
            for c in self.cc:
                self.hosts.append(dictionary.get(c))
        print(self.cc)
        print(self.hosts)

    def setUpLocal(self):
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        hystart = f'{sshPrefix} \"sudo echo 0 > /sys/module/tcp_cubic/parameters/hystart\"'
        # os.system(hystart)

        for command in self.setupCommand:
            os.system(f'{sshPrefix} \"{command}\"')
        for host in self.hosts:
            os.system(
                f'{sshPrefix} \"mkdir {host[:7]}/pcap/trial-{self.batchNum}\"')
            os.system(
                f'{sshPrefix} \"mkdir {host[:7]}/csv/trial-{self.batchNum}\"')
        os.system(f'{sshPrefix} \'mkdir figures/graphs/trial-{self.batchNum}\'')
        os.system(f'{sshPrefix} \'mkdir figures/stats/trial-{self.batchNum}\'')
        os.system(f'mkdir trial-{self.batchNum}')
        os.chdir(f'trial-{self.batchNum}')

    def setProtocolsRemote(self):
        hosts = ['mlcneta', 'mlcnetb', 'mlcnetc', 'mlcnetd']
        protocols = ['cubic', 'cubic', 'bbr', 'hybla']
        for host in self.hosts:
            sshPrefix = f'ssh {self.user}@{host}'
            for command in self.setupCommand:
                os.system(f'{sshPrefix} \'{command}\'')
            hystart = f'{sshPrefix} \"sudo echo 0 > /sys/module/tcp_cubic/parameters/hystart\"'
        # os.system(hystart)
        # for i in range(len(self.hosts)):
        #     command = f'ssh {self.user}@{self.hosts[i]} \"sudo sysctl -w net.ipv4.tcp_congestion_control=\'{self.cc[i]}\'\"'
        #     os.system(command)
        #     self.commandsRun.append(command)
        return

    def sleep(self, sec):
        for i in range(1, sec + 1):
            print(f'\tTime left to sleep {sec + 1 - i} seconds')
            time.sleep(1)

    def getTimeStamp(self):
        return datetime.now().strftime('%Y_%m_%d-%H-%M-%S')

    def startIperf3Server(self):
        for host in self.hosts:
            iperf3ServerStart = f"ssh {self.user}@{host} \"iperf3 -s -p {self.ports[self.serversRunning]}\"&"
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
            iperf3ClientStartCommand = f"ssh {self.user}@glomma.cs.wpi.edu \'iperf3 --reverse -i \"eno2\" -c {host} -n{self.data} -p {self.ports[self.clientsRunning]}\'&"
            self.clientsRunning += 1
            print(f'\trunning command: \n{iperf3ClientStartCommand}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ClientStartCommand)
            self.commandsRun.append((timeStamp, iperf3ClientStartCommand))
        self.sleep(self.timeout)
        # while exitCodes[0].poll() is None or exitCodes[1].poll() is None:
        #     if time.time() - time1 > 600.0:
        #         break
        #     pass

    def startTcpdump(self):
        for host in self.hosts:
            timeStamp = self.getTimeStamp()
            filename = f'{self.cc[self.tcpdumpsRunning]}-{timeStamp}.pcap'
            tcpdump = f"ssh {self.user}@{host} \"sudo tcpdump -s 96 src port {self.ports[self.tcpdumpsRunning]} -w '{filename}'\"&"
            self.tcpdumpsRunning += 1
            print(f'\trunning command: \n{tcpdump}')
            os.system(tcpdump)
            self.commandsRun.append((timeStamp, tcpdump))
            self.pcaps.append(filename)
            self.sleep(3)

    def getPcaps(self):
        for file in self.pcaps:
            host = self.hosts[self.pcapsSent]
            scpToCS = f'scp {self.user}@{host}:~/{file} ~/SatelliteCode/trial-{self.batchNum}'
            scpFromCS = f'scp ~/SatelliteCode/trial-{self.batchNum}/{file} {self.user}@glomma.cs.wpi.edu:~/{host[:7]}/pcap/trial-{self.batchNum}/{file}'
            print(f'\trunning command: \n{scpToCS}')
            timeStamp = self.getTimeStamp()
            os.system(scpToCS)
            self.commandsRun.append((timeStamp, scpToCS))
            self.sleep(3)
            print(f'\trunning command: \n{scpFromCS}')
            timeStamp = self.getTimeStamp()
            os.system(scpFromCS)
            self.commandsRun.append((timeStamp, scpFromCS))
            self.pcapsSent += 1
            self.sleep(3)

    def pcapToCsv(self):
        for file in self.pcaps:
            host = f'{self.hosts[self.csvsGenerated][:7]}'
            csvFilename = file.split('.')[0] + '.csv'
            tshark = f'tshark -r {host}/pcap/trial-{self.batchNum}/{file} -T fields \
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
                    > ~/{host}/csv/trial-{self.batchNum}/{csvFilename}'
            fullCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'{tshark}\''
            self.csvs.append(csvFilename)
            # print(f'\trunning command: \n{fullCommand}')
            timeStamp = self.getTimeStamp()
            # os.system(fullCommand)
            self.commandsRun.append((timeStamp, fullCommand))
            self.csvsGenerated += 1
            # self.sleep(5)

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

    def cleanUp(self):
        self.terminateCommands()
        if self.done:
            os.system(f'rm *.pcap')
            for host in self.hosts:
                for file in self.pcaps:
                    remove = f'ssh {self.user}@{host} \'sudo rm {file}\''
                    os.system(remove)
            if self.log:
                self.makeLogFile()

    def generateGraphGlomma(self):
        hostA_filename = f"{self.hosts[0][:7]}/pcap/trial-{self.batchNum}/{self.pcaps[0]}"
        hostB_filename = f"{self.hosts[1][:7]}/pcap/trial-{self.batchNum}/{self.pcaps[1]}"
        runScript = f'ssh {self.user}@glomma.cs.wpi.edu python3 graph.py {hostA_filename} {hostB_filename} {self.cc[0]} {self.cc[1]} {self.batchNum} {self.runNum} {self.hosts[0][:7]} {self.hosts[1][:7]}'
        self.graphCommand = runScript
        print(f'\trunning command: \n{runScript}')

    # timeStamp = self.getTimeStamp()
    # os.system(runScript)
    # self.commandsRun.append(runScript)

    def start(self):
        os.chdir(os.path.expanduser("~/SatelliteCode"))
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
        print("Running startTcpdump()")
        self.startTcpdump()
        print("Running startIperf3Client()")
        self.startIperf3Client()
        print("Sleeping")
        # self.sleep(self.timeout)
        print('Killing tcpdump and iperf3')
        self.terminateCommands()
        print("Getting pcaps to glomma.cs.wpi.edu")
        self.getPcaps()
        print("Running pcapToCsv()")
        self.pcapToCsv()  # move to other file
        print('Generating graphs on glomma.cs.wpi.edu')
        self.generateGraphGlomma()  # move to other file
        self.done = True
        print("Running cleanUp()")
        self.cleanUp()
        return self.graphCommand


def main():
    # machines = ['mlcneta.cs.wpi.edu', 'mlcnetb.cs.wpi.edu',
    #             'mlcnetc.cs.wpi.edu', 'mlcnetd.cs.wpi.edu']

    t = Trial(data='1G', cc=['cubic', 'hybla'],
              batchNum=111, timeout=100, log=True)
    t.start()
    print("All done")


if __name__ == "__main__":
    main()

'''
Run on the specific hosts for trial n, and run on glomma.cs.wpi.edu.
Set every trial.
'''