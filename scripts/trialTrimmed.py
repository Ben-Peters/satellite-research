# This script was adapted from work by Kush Shah whose work can be
# found here: https://github.com/kush5683/TCP-over-Satellite/blob/main/MediatorCode/trial.py

import argparse
import os
import time
import subprocess
import datetime
from datetime import datetime


class Trial:

    def __init__(self, cc, batchNum, runNum, time, numToRun,
                 user='btpeters', data='20M', timeout=600, log=False, ports=['5201', '5202'],
                 tcp_mem="60000000", tcp_wmem="60000000", tcp_rmem="60000000", iperf_w_arg=0):
        self.dictionary = {}
        self.hosts = []
        self.cc = cc
        self.data = data
        self.time = time
        self.batchNum = batchNum
        self.runNum = runNum
        self.user = user
        self.numToRun = numToRun
        self.pcaps = []
        self.logs = []
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
        self.iperf_w_arg = iperf_w_arg
        self.logsSent = 0
        self.setupCommand = [
            f'sudo sysctl -w net.ipv4.tcp_mem=\"{self.tcp_mem}\"',
            f'sudo sysctl -w net.ipv4.tcp_wmem=\"{self.tcp_wmem}\"',
            f'sudo sysctl -w net.ipv4.tcp_rmem=\"{self.tcp_rmem}\"',
            # 'sudo sysctl -p'
        ]
        self.graphCommand = ''

    def setHosts(self):
        self.dictionary = {
            "hybla": "mlcneta.cs.wpi.edu",
            "cubic": "mlcnetb.cs.wpi.edu",
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
        os.system(f'rm -r tmp')
        os.system(f'mkdir tmp')
        os.chdir(f'tmp')
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        self.enableTuning()
        self.enableHystart()
        self.disableMaxCap()
        #hystart = f'{sshPrefix} \"sudo sh -c \'echo 1 > /sys/module/tcp_cubic/parameters/hystart\'\"'
        #os.system(hystart)

        for command in self.setupCommand:
            os.system(f'{sshPrefix} \'{command}\'')
        filePrefix = f'Trial_{self.batchNum}'
        os.system(f'mkdir {filePrefix}')
        os.system(f'{sshPrefix} \"mkdir {filePrefix}\"')
        os.system(f'{sshPrefix} \"./setup_routes.sh vorma\"') # TODO: make changing between vorma and satellite easier
        #os.system(f'ssh {self.user}@vorma.cs.wpi.edu \"sudo ./satellite.sh\"')
        for host in self.hosts:
            os.system(f'ssh {self.user}@{host} \"mkdir {filePrefix}\"')
        os.system(f'mkdir {filePrefix}/pcaps')
        os.system(f'mkdir {filePrefix}/csvs')
        os.system(f'mkdir {filePrefix}/plots')
        os.system(f'mkdir {filePrefix}/logs')
        # os.system(f'{sshPrefix} \'mkdir figures/stats/trial-{self.batchNum}\'')

        os.chdir(f'{filePrefix}')

    def setProtocolsRemote(self):
        # hosts = ['mlcneta', 'mlcnetb', 'mlcnetc', 'mlcnetd']
        protocols = ['cubic', 'hybla', 'bbr', 'pcc']
        for host in self.hosts:
            sshPrefix = f'ssh {self.user}@{host}'
            for command in self.setupCommand:
                os.system(f'{sshPrefix} \'{command}\'')
            hystart = f'{sshPrefix} \"sudo sh -c \'echo 1 > /sys/module/tcp_cubic/parameters/hystart\'\"'
            os.system(hystart)
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
            iperf3ServerStart = f"ssh {self.user}@{host} \"iperf3 -s\"&"
            self.serversRunning += 1
            print(f'\trunning command: \n {iperf3ServerStart}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ServerStart)
            self.commandsRun.append((timeStamp, iperf3ServerStart))
            # self.sleep(1)

    def startIperf3ClientTuneOff(self):
        time1 = time.time()
        exitCodes = []
        for host in self.hosts:
            # exitCodes.append(subprocess.Popen(["ssh", f"{self.user}@glomma.cs.wpi.edu", "iperf3", "--reverse", "-i", "\"eno2\"",
            #                                    "-c", f"{host}", f"-n{self.data}", f"-p{self.ports[self.clientsRunning]}"], stdout=subprocess.DEVNULL))
            if self.data is not None:
                iperf3ClientStartCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'~/iperf/src/iperf3 -R -c {host} -n {self.data} -w {self.iperf_w_arg} -V\''
            else:
                iperf3ClientStartCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'~/iperf/src/iperf3 -R -c {host} -t {self.time} -w {self.iperf_w_arg} -V\''
            self.clientsRunning += 1
            print(f'\trunning command: \n{iperf3ClientStartCommand}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ClientStartCommand)
            self.commandsRun.append((timeStamp, iperf3ClientStartCommand))
        self.sleep(5)

    def startIperf3ClientTuneOn(self):
        time1 = time.time()
        exitCodes = []
        for host in self.hosts:
            # exitCodes.append(subprocess.Popen(["ssh", f"{self.user}@glomma.cs.wpi.edu", "iperf3", "--reverse", "-i", "\"eno2\"",
            #                                    "-c", f"{host}", f"-n{self.data}", f"-p{self.ports[self.clientsRunning]}"], stdout=subprocess.DEVNULL))
            if self.data is not None:
                iperf3ClientStartCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'~/iperf/src/iperf3 -R -c {host} -n {self.data}\''
            else:
                iperf3ClientStartCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'~/iperf/src/iperf3 -R -c {host} -t {self.time}\''
            self.clientsRunning += 1
            print(f'\trunning command: \n{iperf3ClientStartCommand}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ClientStartCommand)
            self.commandsRun.append((timeStamp, iperf3ClientStartCommand))
        self.sleep(5)

    def startIperf3Client(self):
        time1 = time.time()
        exitCodes = []
        for host in self.hosts:
            # exitCodes.append(subprocess.Popen(["ssh", f"{self.user}@glomma.cs.wpi.edu", "iperf3", "--reverse", "-i", "\"eno2\"",
            #                                    "-c", f"{host}", f"-n{self.data}", f"-p{self.ports[self.clientsRunning]}"], stdout=subprocess.DEVNULL))
            if self.data is not None:
                iperf3ClientStartCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'iperf3 -R -c {host} -n {self.data}\''
            else:
                iperf3ClientStartCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'iperf3 -R -c {host} -t {self.time}\''
            self.clientsRunning += 1
            print(f'\trunning command: \n{iperf3ClientStartCommand}')
            timeStamp = self.getTimeStamp()
            os.system(iperf3ClientStartCommand)
            self.commandsRun.append((timeStamp, iperf3ClientStartCommand))
        self.sleep(5)
        # self.sleep(self.timeout)
        # while exitCodes[0].poll() is None or exitCodes[1].poll() is None:
        #     if time.time() - time1 > 600.0:
        #         break
        #     pass

    def startTcpdumpServer(self):
        for host in self.hosts:
            timeStamp = self.getTimeStamp()
            filename = f'Trial_{self.batchNum}/{self.cc[self.tcpdumpsRunning]}_{timeStamp}.pcap'
            # tcpdump = f"ssh {self.user}@{host} \"sudo tcpdump -s 96 port {self.ports[self.tcpdumpsRunning]} -w '{filename}'\"&"
            tcpdump = f"ssh {self.user}@{host} \"sudo tcpdump -s 96 port {self.ports[0]} -w '{filename}'\"&"
            self.tcpdumpsRunning += 1
            print(f'\trunning command: \n{tcpdump}')
            os.system(tcpdump)
            self.commandsRun.append((timeStamp, tcpdump))
            self.pcaps.append(filename)
            self.sleep(3)

    def startTcpdumpClient(self):
        timestamp = self.getTimeStamp()
        filename = f'Trial_{self.batchNum}/{self.cc[self.clientDumpsRunning]}_{timestamp}.pcap'
        # tcpdump = f'ssh {self.user}@glomma.cs.wpi.edu \"sudo tcpdump -i 2 -w {filename} port {self.ports[self.clientsRunning]} -s 96\"&'
        tcpdump = f'ssh {self.user}@glomma.cs.wpi.edu \"sudo tcpdump -i 2 -w {filename} port {self.ports[0]} -s 96\"&'
        self.clientDumpsRunning += 1
        print(f'\trunning command: \n{tcpdump}')
        os.system(tcpdump)
        self.commandsRun.append((timestamp, tcpdump))
        self.clientPcaps.append(filename)
        self.sleep(3)

    def getPcaps(self):
        for file in self.pcaps:
            # host = self.hosts[self.pcapsSent]
            host = self.hosts[0]
            scpFromServer = f'scp -i ~/.ssh/id_rsa {self.user}@{host}:~/{file} /csusers/btpeters/Research/tmp/Trial_{self.batchNum}/pcaps&'
            print(f'\trunning command: \n{scpFromServer}')
            timeStamp = self.getTimeStamp()
            os.system(scpFromServer)
            self.commandsRun.append((timeStamp, scpFromServer))
            self.sleep(3)
            # scpToCS = f'scp {self.user}@{host}:~/{file} ~/SatelliteCode/trial-{self.batchNum}'
            # scpFromCS = f'scp ~/SatelliteCode/trial-{self.batchNum}/{file} {self.user}@glomma.cs.wpi.edu:~/{host[:7]}/pcap/trial-{self.batchNum}/{file}'
            # print(f'\trunning command: \n{scpToCS}')
            # timeStamp = self.getTimeStamp()
            # os.system(scpToCS)
            # self.commandsRun.append((timeStamp, scpToCS))
            # self.sleep(3)
            # print(f'\trunning command: \n{scpFromCS}')
            # timeStamp = self.getTimeStamp()
            # os.system(scpFromCS)
            # self.commandsRun.append((timeStamp, scpFromCS))
            self.pcapsSent += 1
        for file in self.clientPcaps:
            host = "glomma.cs.wpi.edu"
            scpFromClient = f'scp -i ~/.ssh/id_rsa {self.user}@{host}:~/{file} /csusers/btpeters/Research/tmp/Trial_{self.batchNum}/pcaps&'
            print(f'\trunning command: \n{scpFromClient}')
            timeStamp = self.getTimeStamp()
            os.system(scpFromClient)
            self.commandsRun.append((timeStamp, scpFromClient))
            self.sleep(3)



    def makeLogFile(self):
        timeStamp = self.getTimeStamp()
        filename = f'{timeStamp}-command-log.txt'
        f = open(filename, "x")
        for command in self.commandsRun:
            f.write(f'{command[0]} : {command[1]}\n')
        f.close()

    def terminateCommands(self):
        commands = ['iperf3', 'tcpdump', 'UDPing']
        hosts = self.hosts.copy()
        hosts.append('glomma.cs.wpi.edu')
        hosts.append('mlcneta.cs.wpi.edu')
        for host in hosts:
            for command in commands:
                pkill = f'ssh {self.user}@{host} \"sudo pkill -2 {command}\"'
                timeStamp = self.getTimeStamp()
                os.system(pkill)
                self.commandsRun.append((timeStamp, pkill))
            self.tcpdumpsRunning -= 1
            self.serversRunning -= 1
            self.clientsRunning -= 1
            self.clientDumpsRunning -= 1
        pkill = f'ssh {self.user}@glomma.cs.wpi.edu \"sudo pkill -2 tcpdump\"'
        timeStamp = self.getTimeStamp()
        os.system(pkill)
        self.commandsRun.append((timeStamp, pkill))

    def cleanUp(self):
        self.terminateCommands()
        if self.done:
            # os.system(f'rm -r pcaps')
            for host in self.hosts:
                remove = f'ssh {self.user}@{host} \'sudo rm -r Trial_{self.batchNum}\''
                os.system(remove)
            remove = f'ssh {self.user}@glomma.cs.wpi.edu \'sudo rm -r Trial_{self.batchNum}\''
            os.system(remove)
            self.enableTuning()
            if self.log:
                self.makeLogFile()

    def enableTuning(self):
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        command = f'{sshPrefix} \"sudo sysctl net.ipv4.tcp_moderate_rcvbuf=1\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)
        # Proxy Mode
        # command = f'{sshPrefix} \"./setProxyMode.sh 1\"'
        # os.system(command)
        # os.system('echo Proxy should be enabled')
        # self.sleep(30)

    def disableTuning(self):
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        command = f'{sshPrefix} \"sudo sysctl net.ipv4.tcp_moderate_rcvbuf=0\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)
        # command = f'{sshPrefix} \"./setProxyMode.sh 3\"'
        # os.system(command)
        # os.system('echo Proxy should be disabled!')
        # self.sleep(30)

    def limitWithTBF(self):
        sshPrefix = f'ssh {self.user}@vorma.cs.wpi.edu'
        command = f'{sshPrefix} \"sudo ~/tbf.sh\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def emulateNormal(self, delay, jitter):
        sshPrefix = f'ssh {self.user}@vorma.cs.wpi.edu'
        command = f'{sshPrefix} \"sudo ~/normal.sh {delay} {jitter}\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def removeLimit(self):
        sshPrefix = f'ssh {self.user}@vorma.cs.wpi.edu'
        command = f'{sshPrefix} \"sudo ~/remove.sh\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def enableHystart(self):
        sshPrefix = f'ssh {self.user}@{self.hosts[0]}'
        command = f'{sshPrefix} \"sudo sh -c \'echo 1 >> /sys/module/tcp_cubic/parameters/hystart\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def enableMaxCap(self):
        sshPrefix = f'ssh {self.user}@{self.hosts[0]}'
        command = f'{sshPrefix} \"sudo sh -c \'echo 1 >> /sys/module/tcp_cubic/parameters/hystart_delay_max\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def disableMaxCap(self):
        sshPrefix = f'ssh {self.user}@{self.hosts[0]}'
        command = f'{sshPrefix} \"sudo sh -c \'echo 0 >> /sys/module/tcp_cubic/parameters/hystart_delay_max\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def disableHystart(self):
        sshPrefix = f'ssh {self.user}@{self.hosts[0]}'
        command = f'{sshPrefix} \"sudo sh -c \'echo 0 >> /sys/module/tcp_cubic/parameters/hystart\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def setupKernLog(self):
        sshPrefix = f'ssh {self.user}@{self.hosts[0]}'
        command = f'{sshPrefix} \"sudo sh -c \'echo \"\" > /var/log/kern.log\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def moveKernLog(self, variation):
        sshPrefix = f'ssh {self.user}@{self.hosts[0]}'
        command = f'{sshPrefix} \"sudo sh -c \'cp /var/log/kern.log ~/Trial_{self.batchNum}/{variation}_{self.getTimeStamp()}.log\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)
        command = f'{sshPrefix} \"sudo sh -c \'echo \"\" > /var/log/kern.log\'\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)
        self.logs.append(f"Trial_{self.batchNum}/{variation}_{self.getTimeStamp()}.log")

    def routeSatellite(self):
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        command = f'{sshPrefix} \"~/setup_routes.sh\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def routeVorma(self):
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        command = f'{sshPrefix} \"~/setup_routes.sh vorma\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        os.system(command)

    def getLogs(self):
        for file in self.logs:
            # host = self.hosts[self.pcapsSent]
            host = self.hosts[0]
            changeOwnership = f'ssh {self.user}@{self.hosts[0]} \"sudo chown -R btpeters: ~/Trial_{self.batchNum}\"'
            timeStamp = self.getTimeStamp()
            os.system(changeOwnership)
            self.commandsRun.append((timeStamp, changeOwnership))
            scpFromServer = f'scp -i ~/.ssh/id_rsa {self.user}@{host}:~/Trial_{self.batchNum}/* /csusers/btpeters/Research/tmp/Trial_{self.batchNum}/logs&'
            print(f'\trunning command: \n{scpFromServer}')
            timeStamp = self.getTimeStamp()
            os.system(scpFromServer)
            self.commandsRun.append((timeStamp, scpFromServer))
            self.sleep(3)
            self.logsSent += 1

    def startUDPingServer(self):
        # TODO: This should be changed back to whatever the host is
        sshPrefix = f'ssh {self.user}@mlcneta.cs.wpi.edu'
        command = f'{sshPrefix} \"~/sUDPing\"'
        self.commandsRun.append((self.getTimeStamp(), command))
        subprocess.Popen(command, shell=True)

    def startUDPingClient(self):
        os.system("echo 'in Start UDP client'")
        sshPrefix = f'ssh {self.user}@glomma.cs.wpi.edu'
        filename = f'Trial_{self.batchNum}/ping_{self.getTimeStamp()}.csv'
        # command = f'{sshPrefix} \"mkdir Trial_{self.batchNum}/logs\"'
        # os.system(command)
        # self.commandsRun.append((self.getTimeStamp(), command))
        # TODO: This should try to ping the sever not a differnet one
        command = f'{sshPrefix} \"~/myUDPing -h mlcneta.cs.wpi.edu -p 1234 -n 5 -c {filename}\"'
        os.system(f"echo '{command}'")
        self.csvs.append(filename)
        self.commandsRun.append((self.getTimeStamp(), command))
        subprocess.Popen(command, shell=True)

    def getCSV(self):
        prefix = f'/csusers/btpeters/Research/tmp/Trial_{self.batchNum}'
        scpFromServer = f'scp -i ~/.ssh/id_rsa {self.user}@glomma.cs.wpi.edu:~/Trial_{self.batchNum}/* {prefix}/csvs&'
        # os.system(f'mkdir {prefix}/csvs')
        self.commandsRun.append((self.getTimeStamp(), scpFromServer))
        os.system(scpFromServer)
        self.sleep(3)

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

        # run downloads
        if self.iperf_w_arg:
            #self.enableTuning()
            # Use w arg in iperf to set wmem for disabled trials
            for i in range(self.numToRun):
                print("Running startIperf3Server()")
                self.startIperf3Server()
                print("Running startTcpdumpServer()")
                self.startTcpdumpServer()
                if i % 2 == 0:
                    os.system(f"echo \"Trial Num: {i}\nEnabling tuning\"")
                    print("Running startIperf3Client()")
                    self.startIperf3ClientTuneOn()
                else:
                    os.system(f"echo \"Trial Num: {i}\nDisabling tuning\"")
                    print("Running startIperf3Client()")
                    self.startIperf3ClientTuneOff()
                print('Killing tcpdump and iperf3')
                self.terminateCommands()
        else:
            # Set wmem the traditional way
            for i in range(self.numToRun):
                if i % 2 == 0:
                    print(f"Trial Num: {i}\nEnabling tuning")
                    #self.enableTuning()
                    self.limitWithTBF()
                # elif i == self.numToRun/2:
                    # os.system('echo Please disable the Proxy NOW!')
                    # self.sleep(90)
                else:
                    print(f"Trial Num: {i}\nDisabling tuning")
                    #self.disableTuning()
                    self.limitWithRate()

                print("Running startIperf3Server()")
                self.startIperf3Server()
                #print("Running startTcpdumpServer()")
                #self.startTcpdumpServer()
                print("Running startTcpdumpClient()")
                self.startTcpdumpClient()
                print("Running startIperf3Client()")
                self.startIperf3Client()
                # print("Sleeping")
                # self.sleep(self.timeout)
                print('Killing tcpdump and iperf3')
                self.terminateCommands()

        #self.enableTuning()
        self.removeLimit()
        # self.disableTuning()
        print("Getting pcaps")
        self.getPcaps()
        #print("Running pcapToCsv()")
        #self.pcapToCsv()
        # print('Generating graphs')
        # self.plotTputVTime()
        # self.generateGraphs()  # move to other file
        self.done = True
        print("Running cleanUp()")
        self.cleanUp()
        return self.graphCommand

    def startPingRTT(self):
        os.chdir(os.path.expanduser("~/Research"))
        os.system('clear')
        print('Running setHosts()')
        self.setHosts()
        print("Running cleanUp()")
        self.cleanUp()
        if self.runNum == 0:
            print("Running setupLocal()")
            self.setUpLocal()
            print("Disabling max cap")
            self.disableMaxCap()
            print("Running setProtocolsRemote()")
            self.setProtocolsRemote()
        print("Enabling Hystart")
        self.enableHystart()
        print('setting Routes')
        self.routeSatellite()
        print('starting iperf3 server')
        self.startIperf3Server()
        print('Starting ping server')
        self.startUDPingServer()
        print('Starting ping client')
        self.startUDPingClient()
        self.sleep(5)
        print('Starting Iperf3 client')
        self.startIperf3Client()
        print('moving kern log')
        self.moveKernLog()
        print('killing iperf and UDPing')
        self.terminateCommands()
        print('getting logs')
        self.getLogs()
        print('geting CSV')
        self.getCSV()
        self.done = True
        self.cleanUp()
        return self.graphCommand

    def startRTT(self):
        os.chdir(os.path.expanduser("~/Research"))
        os.system('clear')
        print('Running setHosts()')
        self.setHosts()
        print("Running cleanUp()")
        self.cleanUp()
        if self.runNum == 0:
            print("Running setupLocal()")
            self.setUpLocal()
            print("Disabling max cap")
            self.disableMaxCap()
            print("Running setProtocolsRemote()")
            self.setProtocolsRemote()
        print("Disabling HyStart")
        self.disableHystart()
        for i in range(self.numToRun*5):
            print("Setting up vorma")
            self.emulateNormal(600, (i % 5) * 30)
            print("Running startIperf3Server()")
            self.startIperf3Server()
            # run download
            self.routeVorma()
            self.setupKernLog()
            print("Running startIperf3Client()")
            self.startIperf3Client()
            self.moveKernLog((i % 5) * 30)
            self.sleep(5)
        self.enableTuning()
        self.removeLimit()
        # self.disableTuning()
        print("Getting pcaps")
        self.getLogs()
        # print("Running pcapToCsv()")
        # self.pcapToCsv()
        # print('Generating graphs')
        # self.plotTputVTime()
        # self.generateGraphs()  # move to other file
        self.done = True
        print("Running cleanUp()")
        self.cleanUp()
        return self.graphCommand


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
    parser.add_argument('--log', type=bool, help='Use logging output', default=True)
    parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
    parser.add_argument('--runNum', type=int, help="what run number is this", required=True)
    parser.add_argument('--run', type=bool, help="Run the trial or just get the files and analyze locally",
                        default=True)
    parser.add_argument('--time', type=int, help="How long should the download run for", default=60)
    parser.add_argument('--size', type=str, help="How much data should be downloaded (exclusive use with time param)",
                        default=None)
    parser.add_argument('--numToRun', type=int, help="Total number of trial to run")
    parser.add_argument('--rmem', type=str, help='Value for rmem', default="60000000 60000000 60000000")
    parser.add_argument('--wmem', type=str, help='Value for wmem', default="60000000 60000000 60000000")
    parser.add_argument('--mem', type=str, help='Value for mem', default="60000000 60000000 60000000")
    parser.add_argument('--window', type=int, help='Specify size of wmem to be set by iperf', default=0)
    parser.add_argument('--RTT', type=bool, help='Measure RTT or track all stats', default=False)
    parser.add_argument('--Ping', type=bool, help="run UDP at the same time", default=False)
    args = parser.parse_args()

    cc = []

    for c in args.cc.split(" "):
        cc.append(c)

    # machines = ['mlcneta.cs.wpi.edu', 'mlcnetb.cs.wpi.edu',
    #             'mlcnetc.cs.wpi.edu', 'mlcnetd.cs.wpi.edu']

    # t = Trial(data='1G', cc=['cubic', 'hybla'],
    #          batchNum=111, timeout=100, log=True)
    os.system(f'echo {args.rmem}')
    if args.window:
        args.wmem = f'4096 16384 {args.window}'
    t = Trial(data=args.size, batchNum=args.batch, timeout=100, log=args.log, cc=cc, runNum=args.runNum,
              numToRun=args.numToRun, time=args.time, tcp_rmem=args.rmem,
              tcp_mem=args.mem, tcp_wmem=args.wmem, ports=['5201', '5201'], iperf_w_arg=args.window)
    #if args.RTT:
    t.startRTT()
    #elif args.Ping:
    # t.startPingRTT()
    #else:
    #    t.start()
    print("All done")
    exit(0)


if __name__ == "__main__":
    main()
