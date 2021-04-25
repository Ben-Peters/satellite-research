import argparse
import os
from plot import PlotTputOneFlow, PlotTputCompare, PlotAllData
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--log', type=bool, help='Use logging output', default=True)
parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
parser.add_argument('--runNum', type=int, help="what run number is this", required=True)
parser.add_argument('--size', type=str, help='How much data do you want to download', default="250M")
parser.add_argument('--time', type=int, help='How long do you want the download to run', default=None)
parser.add_argument('--numToRun', type=int, help='Total number of downloads to run', default=10)
parser.add_argument('--tcpSettings', type=str, help='Which settings should be used', required=True)
args = parser.parse_args()

dictionary = {
    "cubic": "mlcneta.cs.wpi.edu",
    "hybla": "mlcnetb.cs.wpi.edu",
    "bbr": "mlcnetc.cs.wpi.edu",
    "pcc": "mlcnetd.cs.wpi.edu"
}


def getData():
    os.mkdir(f'G:/satellite-research/csvs/Trial_{args.batch}')
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
    legend = ['With Tuning', 'Without Tuning']
    for file, i in zip(files, range(len(files))):
        csvFilename = f'G:/satellite-research/csvs/Trial_{args.batch}/' + file
        csvs.append(csvFilename)
        # legend.append(hosts[i].split('.')[0])
    plotFilename = csvs[0].replace("/csvs/", "/plots/").replace(".csv", "_TPUT.png")
    plot = PlotAllData(protocol=cc[0], csvFiles=csvs, plotFile=plotFilename, legend=legend,
                       numRuns=int(args.numToRun / 2), title=f'default')
    # plot = PlotTputOneFlow(protocol=self.cc[0], csvFilepath=csvFilename, plotFilepath=plotFilename)
    plot.plotALL()
    # plot.plotStartTput(20)
    plot.plotStart(20)


def main():
    if args.time is not None:
        startTrial = f"ssh btpeters@Andromeda.dyn.wpi.edu \" python3 ~/Research/scripts/trial.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--time {args.time} --numToRun {args.numToRun}\" "
    else:
        startTrial = f"ssh btpeters@Andromeda.dyn.wpi.edu \" python3 ~/Research/scripts/trial.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--size {args.size} --numToRun {args.numToRun}\" "
    print("Running command: " + startTrial)
    subprocess.call(startTrial, shell=True)
    getData()
    plotData()


if __name__ == "__main__":
    main()
