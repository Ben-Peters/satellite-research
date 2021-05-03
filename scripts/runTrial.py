import argparse
import os
from plot import PlotTputOneFlow, PlotTputCompare, PlotAllData
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--log', type=bool, help='Use logging output', default=True)
parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
parser.add_argument('--runNum', type=int, help="what run number is this", default=0)
parser.add_argument('--size', type=str, help='How much data do you want to download', default="250M")
parser.add_argument('--time', type=int, help='How long do you want the download to run', default=None)
parser.add_argument('--numToRun', type=int, help='Total number of downloads to run', default=10)
parser.add_argument('--tcpSettings', type=int, help='Which settings should be used', default=None)
parser.add_argument('--rmem', type=str, help='Value for rmem', default="4096 131072 6291456")
parser.add_argument('--wmem', type=str, help='Value for wmem', default="4096 16384 4194304")
parser.add_argument('--mem', type=str, help='Value for mem', default="382185 509580 764370")
parser.add_argument('--plotName', type=str, help='Name for plots created', default="TCP Performance")
args = parser.parse_args()

dictionary = {
    "cubic": "mlcneta.cs.wpi.edu",
    "hybla": "mlcnetb.cs.wpi.edu",
    "bbr": "mlcnetc.cs.wpi.edu",
    "pcc": "mlcnetd.cs.wpi.edu"
}
# Settings for quick recalls format is (rmem, wmem, mem, title)
tcpSettings = [["4096 131072 6291456", "4096 16384 4194304", "382185 509580 764370", "Default Settings"],               # 0
               ["4096 262144 6291456", "4096 16384 4194304", "382185 509580 764370", "Default Value Doubled"],          # 1
               ["4096 131072 12582912", "4096 16384 4194304", "382185 509580 764370", "Max Value Doubled"],             # 2
               ["60000000 60000000 60000000", "4096 16384 4194304", "382185 509580 764370", "All at 60MB"],             # 3
               ["4096 131072 6291456", "60000000 60000000 60000000", "382185 509580 764370", "Default Settings"],       # 4
               ["4096 262144 6291456", "60000000 60000000 60000000", "382185 509580 764370", "Default Value Doubled"],  # 5
               ["4096 131072 12582912", "60000000 60000000 60000000", "382185 509580 764370", "Max Value Doubled"],     # 6
               ["60000000 60000000 60000000", "60000000 60000000 60000000", "382185 509580 764370", "All at 60MB"],     # 7
               ["4096 60000000 6291456", "60000000 60000000 60000000", "382185 509580 764370", "Default at 60MB"],      # 8
               ["4096 131072 60000000", "60000000 60000000 60000000", "382185 509580 764370", "Max at 60MB"],           # 9
               ["4096 3145728 6291456", "60000000 60000000 60000000", "382185 509580 764370", "Default value half of Max"],  # 10
               ["4096 131072 6291456", "4096 16384 4194304", "382185 509580 764370", "Default wmem"],  # 11
               ["4096 131072 6291456", "60000000 60000000 60000000", "382185 509580 764370", "Large wmem"]]  # 12

if args.tcpSettings is not None:
    args.rmem = tcpSettings[args.tcpSettings][0]
    args.wmem = tcpSettings[args.tcpSettings][1]
    args.mem = tcpSettings[args.tcpSettings][2]
    args.plotName = tcpSettings[args.tcpSettings][3]

def getData():
    try:
        os.mkdir(f'G:/satellite-research/csvs/Trial_{args.batch}')
    except:
        print('Folder not created')
    getCSVs = f'scp btpeters@andromeda.dyn.wpi.edu:~/Research/Trial_{args.batch}/csvs/* G:/satellite-research/csvs/Trial_{args.batch}'
    os.system(getCSVs)


def plotData():
    hosts = []
    cc = []
    for c in args.cc.split(" "):
        cc.append(c)
    for c in cc:
        hosts.append(dictionary.get(c))
    files = os.listdir(f'G:/satellite-research/csvs/Trial_{args.batch}')
    try:
        os.mkdir(f'G:/satellite-research/plots/Trial_{args.batch}')
    except:
        print("Folder not created")

    hosts += ["glomma.cs.wpi.edu"]
    csvs = []
    legend = ['With Proxy', 'Without Proxy']
    for file, i in zip(files, range(len(files))):
        csvFilename = f'G:/satellite-research/csvs/Trial_{args.batch}/' + file
        csvs.append(csvFilename)
        # legend.append(hosts[i].split('.')[0])
    plotFilename = csvs[0].replace("/csvs/", "/plots/").replace(".csv", "_TPUT.png")
    plot = PlotAllData(protocol=cc[0], csvFiles=csvs, plotFile=plotFilename, legend=legend,
                       numRuns=int(args.numToRun / 2), title=f'{args.plotName}\nwmem={args.wmem}')
    # plot = PlotTputOneFlow(protocol=self.cc[0], csvFilepath=csvFilename, plotFilepath=plotFilename)
    plot.plotALL()
    # plot.plotStartTput(20)
    plot.plotStart(15)


def main():
    if args.time is not None:
        startTrial = f"ssh btpeters@Andromeda.dyn.wpi.edu \" python3 ~/Research/scripts/trial.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--time {args.time} --numToRun {args.numToRun} " \
                     f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\'\" "
    else:
        startTrial = f"ssh btpeters@Andromeda.dyn.wpi.edu \" python3 ~/Research/scripts/trial.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--size {args.size} --numToRun {args.numToRun}" \
                     f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\'\" "
    print("Running command: " + startTrial)
    try:
        os.listdir(f'G:/satellite-research/csvs/Trial_{args.batch}')
        print("This trial has already been run, just creating plots")
    except:
        subprocess.call(startTrial, shell=True)
        getData()
    plotData()


if __name__ == "__main__":
    main()
