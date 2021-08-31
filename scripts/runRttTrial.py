import argparse
import os
from plot import PlotTputOneFlow, PlotTputCompare, PlotAllData
import subprocess
from fabric2 import Connection
import time

parser = argparse.ArgumentParser()
parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
parser.add_argument('--log', type=bool, help='Use logging output', default=True)
parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
parser.add_argument('--runNum', type=int, help="what run number is this", default=0, required=False)
parser.add_argument('--size', type=str, help='How much data do you want to download', default=None)
parser.add_argument('--time', type=int, help='How long do you want the download to run', default=15)
parser.add_argument('--numToRun', type=int, help='Total number of downloads to run', default=10)
parser.add_argument('--tcpSettings', type=int, help='Which settings should be used', default=None)
parser.add_argument('--rmem', type=str, help='Value for rmem', default="60000000 60000000 60000000")
parser.add_argument('--wmem', type=str, help='Value for wmem', default="60000000 60000000 60000000")
parser.add_argument('--mem', type=str, help='Value for mem', default="60000000 60000000 60000000")
parser.add_argument('--plotName', type=str, help='Name for plots created', default="Measured RTT")
parser.add_argument('--window', type=int, help='Specify size of wmem to be set by iperf', default=0)
parser.add_argument('--realtime', type=bool, help='Convert logs to realtime for easier syncing', default=False)
args = parser.parse_args()

dictionary = {
    "hybla": "mlcneta.cs.wpi.edu",
    "cubic": "mlcnetb.cs.wpi.edu",
    "bbr": "mlcnetc.cs.wpi.edu",
    "pcc": "mlcnetd.cs.wpi.edu"
}


def getData():
    try:
        os.mkdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
    except:
        print('Folder not created')

    makeCSVs = f'ssh btpeters@Andromeda \"python3 ~/Research/scripts/Logs2CSV.py --batch {args.batch} --realtime {args.realtime}\"'
    subprocess.call(makeCSVs, shell=True)

    getCSVs = f'scp btpeters@Andromeda:~/Research/Trial_{args.batch}/csvs/* C:/satellite-research/csvs/Trial_{args.batch}'
    #  The CSVs should be sorted by now (first is log csv second is ping csv)
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
    legend = ['Satellite', 'Emulated (Vorma)']
    for file, i in zip(files, range(len(files))):
        csvFilename = f'C:/satellite-research/csvs/Trial_{args.batch}/' + file
        csvs.append(csvFilename)
        # legend.append(hosts[i].split('.')[0])
    plotFilename = csvs[0].replace("/csvs/", "/plots/").replace(".csv", ".png")
    plot = PlotAllData(protocol=cc[0], csvFiles=csvs, plotFile=plotFilename, legend=legend,
                       numRuns=int(args.numToRun / 2), title=args.plotName)
    # plot = PlotTputOneFlow(protocol=self.cc[0], csvFilepath=csvFilename, plotFilepath=plotFilename)
    plot.plotWithPing(args.plotName)
    # TODO: add this back in
    #  plot.RTT(args.plotName)


def main():
    if args.time is not None:
        startTrial = f"python3 ~/Research/scripts/trialTrimmed.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--time {args.time} --numToRun {args.numToRun} " \
                     f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\' --window {args.window} --RTT 0 --Ping 1 "
    else:
        startTrial = f"python3 ~/Research/scripts/trialTrimmed.py " \
                     f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                     f"--size {args.size} --numToRun {args.numToRun}" \
                     f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\' --window {args.window} --RTT 0 --Ping 1 "
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