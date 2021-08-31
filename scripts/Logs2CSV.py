import argparse
import os
import subprocess
import time

parser = argparse.ArgumentParser()

parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--realtime', type=bool, help='Should time be converted to realime', default=False)

args = parser.parse_args()

def sleep(sec):
    for i in range(1, sec + 1):
        print(f'\tTime left to sleep {sec + 1 - i} seconds')
        time.sleep(1)


def logToCsv(files, prefix):
    bootTime = 0
    if args.realtime:
        sshProxy = "ssh btpeters@cs.wpi.edu 'ssh btpeters@mlcnetb.cs.wpi.edu \"stat -c %Z /proc/ > bootTime.txt\"'"
        os.system(sshProxy)
        sshProxy = "ssh btpeters@cs.wpi.edu 'ssh btpeters@mlcnetb.cs.wpi.edu \"stat -c %z /proc/ >> bootTime.txt\"'"
        os.system(sshProxy)
        scp = "ssh btpeters@cs.wpi.edu 'scp btpeters@mlcnetb.cs.wpi.edu:bootTime.txt bootTime.txt'"
        os.system(scp)
        scp = "scp btpeters@cs.wpi.edu:bootTime.txt bootTime.txt"
        os.system(scp)
        timeStr = ''
        for line in open('bootTime.txt', 'r').readlines():
            print(f"{line}")
            line.replace('\n', '')
            if '.' not in line:
                timeStr = line
            else:
                timeStr = timeStr + '.' + (line.split('.')[-1]).split(' ')[0]
        print(timeStr)
        bootTime = float(timeStr)
    for file in files:
        log = open((prefix + file), 'r')
        lines = log.readlines()
        csv = open(f'csvs/{file.replace(".log", ".csv")}', 'w')
        sampleRTT = 0
        cwnd = 0
        packets_out = 0
        mss = 0
        currRTT = 0
        minRTT = 0
        delayThresh = 0
        sampleCount = 0
        numPackets = 0
        logTime = 0
        exit = 0
        flag = False
        for line in lines:
            if "(5201)" in line:
                if "packets since start:" in line:
                    if flag:
                        csv.write(f"{numPackets},{logTime},{sampleRTT},{cwnd},{packets_out},{mss},{sampleCount},{currRTT},{minRTT},{delayThresh},{exit}\n")
                        sampleRTT = 0
                        cwnd = 0
                        packets_out = 0
                        mss = 0
                        currRTT = 0
                        minRTT = 0
                        delayThresh = 0
                        sampleCount = 0
                        numPackets = 0
                        logTime = 0
                    else:
                        csv.write(f'numPackets,time,sampleRTT,cwnd,packets_out,mss,sampleCount,currRTT,minRTT,delayThresh,exit\n')
                        flag = True
                    numPackets = int(line.split("$")[-1])
                    logTime = float(line.split("[")[1].split(']')[0]) + bootTime
                elif "sample RTT:" in line:
                    sampleRTT = int(line.split("$")[-1])
                elif "cwnd:" in line:
                    cwnd = int(line.split("$")[-1])
                elif "packets in flight:" in line:
                    packets_out = int(line.split("$")[-1])
                elif "mss:" in line:
                    mss = int(line.split("$")[-1])
                elif "Sample count:" in line:
                    sampleCount = int(line.split("$")[-1])
                elif "curr RTT:" in line:
                    currRTT = int(line.split("$")[-1])
                elif "min RTT:" in line:
                    minRTT = int(line.split("$")[-1])
                elif "delay thresh:" in line:
                    delayThresh = int(line.split("$")[-1])
                elif "Exit due to delay detect" in line:
                    exit = 1
        csv.write(f"{numPackets},{logTime},{sampleRTT},{cwnd},{packets_out},{mss},{sampleCount},{currRTT},{minRTT},{delayThresh},{exit}\n")
        log.close()
        csv.close()


def getData():
    print("getting data")
    os.system(f'mkdir Trial_{args.batch}')
    os.system(f'mkdir Trial_{args.batch}/csvs Trial_{args.batch}/logs')
    os.system(f'scp -i ~/.ssh/id_rsa btpeters@cs.wpi.edu:~/Research/tmp/Trial_{args.batch}/logs/* ~/Research/Trial_{args.batch}/logs&')
    os.system(f'scp -i ~/.ssh/id_rsa btpeters@cs.wpi.edu:~/Research/tmp/Trial_{args.batch}/csvs/* ~/Research/Trial_{args.batch}/csvs&')
    sleep(60)


def main():
    os.chdir(f'Research')
    print("in Research")
    # os.listdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
    #getData()
    os.chdir(f'Trial_{args.batch}')
    print(os.getcwd())
    prefix = f'{os.getcwd()}/logs/'
    logToCsv(files=os.listdir(f'./logs'), prefix=prefix)

if __name__ == "__main__":
    main()