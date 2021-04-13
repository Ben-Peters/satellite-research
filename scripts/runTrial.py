import argparse
import os
from plot import PlotTputOneFlow
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--log', type=bool, help='Use logging output', default=True)
parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
parser.add_argument('--runNum', type=int, help="what run number is this", required=True)
args = parser.parse_args()


def getData():
    os.mkdir(f'G:/research/csvs/Trial_{args.batch}')
    getCSVs = f'scp btpeters@andromeda.dyn.wpi.edu:~/Research/Trial_{args.batch}/csvs/* G:/research/csvs/Trial_{args.batch}'
    os.system(getCSVs)


def plotData():
    files = os.listdir(f'G:/research/csvs/Trial_{args.batch}')
    try: os.mkdir(f'G:/research/plots/Trial_{args.batch}')
    except:
        print("Folder not created")
    for file in files:
        csvFilename = f'G:/research/csvs/Trial_{args.batch}' + file
        plotFilename = csvFilename.replace("/csvs/", "/plots/").replace(".csv", "_RTT.png")
        plot = PlotTputOneFlow(protocol=args.cc, csvFilepath=csvFilename, plotFilepath=plotFilename)
        plot.plotTput()
    pass


def main():
    startTrial = f"ssh btpeters@Andromeda.dyn.wpi.edu \" python3 ~/Research/scripts/trial.py --batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} \" "
    print("Running command: " + startTrial)
    subprocess.call(startTrial, shell=True)
    # time.sleep(600)
    getData()
    plotData()


if __name__ == "__main__":
    main()