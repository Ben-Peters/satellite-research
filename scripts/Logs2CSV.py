import argparse
import os
import subprocess
import time

parser = argparse.ArgumentParser()

parser.add_argument('--batch', type=int, help='What batch number is this', required=True)

args = parser.parse_args()

def sleep(sec):
    for i in range(1, sec + 1):
        print(f'\tTime left to sleep {sec + 1 - i} seconds')
        time.sleep(1)


def logToCsv(files):
    for file in files:
        log = open(file, 'r')
        lines = log.readlines()
        csv = open(f'csvs/{file.replace(".log", ".csv")}', 'w')
        sampleRTT = 0
        cwnd = 0
        currRTT = 0
        minRTT = 0
        delayThresh = 0
        sampleCount = 0
        numPackets = 0
        time = 0
        exit = 0
        flag = False
        for line in lines:
            if "(5201)" in line:
                if "packets since start:" in line:
                    if flag:
                        csv.write(f"{numPackets},{time},{sampleRTT},{cwnd},{sampleCount},{currRTT},{minRTT},{delayThresh},{exit}\n")
                        sampleRTT = 0
                        cwnd = 0
                        currRTT = 0
                        minRTT = 0
                        delayThresh = 0
                        sampleCount = 0
                        numPackets = 0
                        time = 0
                    else:
                        csv.write(f'numPackets,time,sampleRTT,cwnd,sampleCount,currRTT,minRTT,delayThresh,exit\n')
                        flag = True
                    numPackets = int(line.split("$")[-1])
                    time = float(line.split("[ ")[1].split(']')[0])
                elif "sample RTT:" in line:
                    sampleRTT = int(line.split("$")[-1])
                elif "cwnd:" in line:
                    cwnd = int(line.split("$")[-1])
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
        csv.write(f"{numPackets},{time},{sampleRTT},{cwnd},{sampleCount},{currRTT},{minRTT},{delayThresh},{exit}\n")
        log.close()
        csv.close()


def getData():
    print("getting data")
    os.system(f'mkdir Trial_{args.batch}')
    os.system(f'mkdir Trial_{args.batch}/csvs Trial_{args.batch}/logs')
    os.system(f'scp -i ~/.ssh/id_rsa btpeters@cs.wpi.edu:~/Research/tmp/Trial_{args.batch}/logs/* ~/Research/Trial_{args.batch}/logs&')
    sleep(60)


def main():
    os.chdir(f'Research')
    print("in Research")
    # os.listdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
    getData()
    os.chdir(f'Trial_{args.batch}')
    print(os.getcwd())
    logToCsv(files=os.listdir(f'./logs'))

if __name__ == "__main__":
    main()