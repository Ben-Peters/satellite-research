import argparse
import os
from plot import PlotTputOneFlow, PlotTputCompare, PlotAllData
import subprocess
import time
from fabric2 import Connection

parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--log', type=bool, help='Use logging output', default=True)
parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
parser.add_argument('--runNum', type=int, help="what run number is this", default=0, required=False)
parser.add_argument('--size', type=str, help='How much data do you want to download', default="250M")
parser.add_argument('--time', type=int, help='How long do you want the download to run', default=None)
parser.add_argument('--numToRun', type=int, help='Total number of downloads to run', default=10)
parser.add_argument('--tcpSettings', type=int, help='Which settings should be used', default=None)
parser.add_argument('--rmem', type=str, help='Value for rmem', default="60000000 60000000 60000000")
parser.add_argument('--wmem', type=str, help='Value for wmem', default="60000000 60000000 60000000")
parser.add_argument('--mem', type=str, help='Value for mem', default="60000000 60000000 60000000")
parser.add_argument('--plotName', type=str, help='Name for plots created', default="TCP Performance")
parser.add_argument('--window', type=int, help='Specify size of wmem to be set by iperf', default=0)
args = parser.parse_args()

dictionary = {
    "cubic": "mlcneta.cs.wpi.edu",
    "hybla": "mlcnetb.cs.wpi.edu",
    "bbr": "mlcnetc.cs.wpi.edu",
    "pcc": "mlcnetd.cs.wpi.edu"
}
# Settings for quick recalls format is (rmem, wmem, mem, title, maxY, window)
tcpSettings = [["4096 131072 6291456", "4096 16384 4194304", "382185 509580 764370",
                "Default Settings\n"+r"rmem=4096 131072 6291456", [140, 1.5, 6, 6, 2], 0],                        # 0

               ["4096 262144 6291456", "4096 16384 4194304", "382185 509580 764370",
                "Default Value Doubled\n"+r"rmem=4096 $\bf{262144}$ 6291456", [140, 1.5, 6, 6, 2], 0],            # 1

               ["4096 131072 12582912", "4096 16384 4194304", "382185 509580 764370",
                "Max Value Doubled\n"+r"rmem=4096 131072 $\bf{12582912}$", [140, 1.5, 6, 6, 2], 0],               # 2

               ["60000000 60000000 60000000", "4096 16384 4194304", "382185 509580 764370",
                "All at 60MB\n"+r"rmem=$\bf{60000000\:60000000\:60000000}$", [140, 1.5, 30, 6, 2], 0],            # 3

               ["4096 131072 6291456", "60000000 60000000 60000000", "382185 509580 764370",
                "Default Settings\n"+r"rmem=4096 131072 6291456", [140, 2, 6.5, 6.5, 15], 0],                   # 4

               ["4096 262144 6291456", "60000000 60000000 60000000", "382185 509580 764370",
                "Default Value Doubled\n"+r"rmem=4096 $\bf{262144}$ 6291456", [140, 2, 6.5, 6.5, 15], 0],       # 5

               ["4096 131072 12582912", "60000000 60000000 60000000", "382185 509580 764370",
                "Max Value Doubled\n"+r"rmem=4096 131072 $\bf{12582912}$", [140, 2, 6.5, 6.5, 15], 0],          # 6

               ["60000000 60000000 60000000", "60000000 60000000 60000000", "382185 509580 764370",
                "All at 60MB\n"+r"rmem=$\bf{60000000\:60000000\:60000000}$", [140, 2, 30, 30, 15], 0],          # 7

               ["4096 60000000 6291456", "60000000 60000000 60000000", "382185 509580 764370",
                "Default at 60MB\n"+r"rmem=4096 $\bf{60000000}$ 6291456", [140, 2, 30, 30, 15], 0],             # 8

               ["4096 131072 60000000", "60000000 60000000 60000000", "382185 509580 764370",
                "Max at 60MB\n"+r"rmem=4096 131072 $\bf{60000000}$", [140, 2, 6.5, 6.5, 15], 0],                # 9

               ["4096 3145728 6291456", "60000000 60000000 60000000", "382185 509580 764370",
                "Default value half of Max\n"+r"rmem=4096 $\bf{3145728}$ 6291456", [140, 2, 6.5, 6.5, 15], 0],  # 10

               ["4096 131072 6291456", "4096 16384 4194304", "382185 509580 764370",
                "Default wmem"],                                                                                # 11

               ["4096 131072 6291456", "60000000 60000000 60000000", "382185 509580 764370",
                "60MB wmem"],                                                                                   # 12

               ["4096 3145728 6291456", "4096 16384 4194304", "382185 509580 764370",
                "Default value half of max", [140, 2, 6.5, 6.5, 15], 0],                                        # 13

               ["4096 131072 6291456", "4096 16384 4194304", "382185 509580 764370",
                "Default settings\n"+r"wmem=4096 16384 4194304", [140, 2, 6.5, 6.5, 10], 4194304],                    # 14

               ["4096 131072 6291456", "4096 32768 4194304", "382185 509580 764370",
                "Default Value Doubled\n" + r"wmem=4096 $\bf{32768}$ 4194304", [140, 2, 6.5, 6.5, 10], 4194304],     # 15

               ["4096 131072 6291456", "4096 16384 8388608", "382185 509580 764370",
                "Max Value Doubled\n" + r"wmem=4096 16384 $\bf{8388608}$", [140, 2, 6.5, 6.5, 10], 8388608],           # 16

               ["4096 131072 6291456", "60000000 60000000 60000000", "382185 509580 764370",
                "All at 60MB\n" + r"wmem=$\bf{60000000\:60000000\:60000000}$", [140, 2, 6.5, 6.5, 10], 60000000],     # 17

               ["60000000 60000000 60000000", "4096 16384 4194304", "382185 509580 764370",
                "Default settings\n"+r"wmem=4096 16384 4194304", [140, 2, 30, 6.5, 10], 4194304],                    # 18

               ["60000000 60000000 60000000", "4096 32768 4194304", "382185 509580 764370",
                "Default Value Doubled\n" + r"wmem=4096 $\bf{32768}$ 4194304", [140, 2, 30, 6.5, 10], 4194304],           # 19

               ["60000000 60000000 60000000", "4096 16384 8388608", "382185 509580 764370",
                "Max Value Doubled\n" + r"wmem=4096 16384 $\bf{8388608}$", [140, 2, 30, 6.5, 10], 8388608],            # 20

               ["60000000 60000000 60000000", "60000000 60000000 60000000", "382185 509580 764370",
                "All at 60MB\n" + r"wmem=$\bf{60000000\:60000000\:60000000}$", [140, 2, 30, 30, 10], 60000000],        # 21

               ["60000000 60000000 60000000", "4096 16384 4194304", "382185 509580 764370",
                "iperf testing\n"+r"rmem=4096 131072 6291456", [140, 2, 65, 30, 10], 60000000]                  # 22
               ]

maxY = None

if args.tcpSettings is not None:
    args.rmem = tcpSettings[args.tcpSettings][0]
    args.wmem = tcpSettings[args.tcpSettings][1]
    args.mem = tcpSettings[args.tcpSettings][2]
    args.plotName = tcpSettings[args.tcpSettings][3]
    try:
        maxY = tcpSettings[args.tcpSettings][4]
        args.window = tcpSettings[args.tcpSettings][5]
    except:
        maxY = None

def getData():
    try:
        os.mkdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
    except:
        print('Folder not created')

    makeCSVs = f'ssh btpeters@Andromeda \"python3 ~/Research/scripts/Logs2CSV.py --batch {args.batch} --realtime 0\"'
    subprocess.call(makeCSVs, shell=True)

    getCSVs = f'scp btpeters@Andromeda:~/Research/Trial_{args.batch}/csvs/* C:/satellite-research/csvs/Trial_{args.batch}'
    os.system(getCSVs)


def plotData():
    hosts = []
    cc = []
    for c in args.cc.split(" "):
        cc.append(c)
    for c in cc:
        hosts.append(dictionary.get(c))
    files = os.listdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
    try:
        os.mkdir(f'C:/satellite-research/plots/Trial_{args.batch}')
    except:
        print("Folder not created")

    hosts += ["glomma.cs.wpi.edu"]
    csvs = []
    #legend = ['With Receiver Auto-Tune', 'Without Receiver Auto-Tune']
    for file, i in zip(files, range(len(files))):
        csvFilename = f'C:/satellite-research/csvs/Trial_{args.batch}/' + file
        csvs.append(csvFilename)
        # legend.append(hosts[i].split('.')[0])
    plotFilename = csvs[0].replace("/csvs/", "/plots/").replace(".csv", ".png")
    plot = PlotAllData(protocol=cc[0], csvs=csvs, plotFile=plotFilename, legend=None,
                       numRuns=int(args.numToRun / 2), title=args.plotName)
    # plot = PlotTputOneFlow(protocol=self.cc[0], csvFilepath=csvFilename, plotFilepath=plotFilename)
    plot.mdev_vs_sdev()
    #plot.plotStartTput(15)
    #plot.plotStart(15)
    #plot.plotTimeDelta()


def main():
    if args.time is not None:
        startTrial = f"python3 ~/Research/scripts/trialTrimmed.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--time {args.time} --numToRun {args.numToRun} " \
                     f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\' --window {args.window} --RTT 1 --Ping 0 "
    else:
        startTrial = f"python3 ~/Research/scripts/trialTrimmed.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--size {args.size} --numToRun {args.numToRun}" \
                     f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\' --window {args.window} --RTT 1 --Ping 0 "
        #  TODO: Replace this with what it was before (RTT: 1, Ping: 0)
    print("Running command: " + startTrial)
    try:
        os.listdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
        print("This trial has already been run, just creating plots")
    except:
        ssh = Connection(host='cs.wpi.edu', user='btpeters')
        ssh.run(startTrial)
        print("getting Data")
    getData()
    plotData()


if __name__ == "__main__":
    main()
