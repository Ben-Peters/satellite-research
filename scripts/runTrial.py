import argparse
import os
from plot import PlotTputOneFlow, PlotTputCompare
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--log', type=bool, help='Use logging output', default=True)
parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
parser.add_argument('--runNum', type=int, help="what run number is this", required=True)
parser.add_argument('--size', type=str, help='How much data do you want to download', default="250M")
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
    legend = []
    for file, i in zip(files, range(len(files))):
        csvFilename = f'G:/satellite-research/csvs/Trial_{args.batch}/' + file
        csvs.append(csvFilename)
        legend.append(hosts[i].split('.')[0])
    plotFilename = csvs[0].replace("/csvs/", "/plots/").replace(".csv", "_TPUT.png")
    plot = PlotTputCompare(protocol=cc[0], csvFiles=csvs, plotFile=plotFilename, legend=legend)
    # plot = PlotTputOneFlow(protocol=self.cc[0], csvFilepath=csvFilename, plotFilepath=plotFilename)
    plot.plotTput()


def main():
    startTrial = f"ssh btpeters@Andromeda.dyn.wpi.edu \" python3 ~/Research/scripts/trial.py " \
                 f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} --size {args.size}\" "
    print("Running command: " + startTrial)
    subprocess.call(startTrial, shell=True)
    # time.sleep(600)
    getData()
    plotData()


if __name__ == "__main__":
    main()