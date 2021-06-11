import argparse
import os
import subprocess
import time

parser = argparse.ArgumentParser()

parser.add_argument('--batch', type=int, help='What batch number is this', required=True)

args = parser.parse_args()

def sleep(self, sec):
    for i in range(1, sec + 1):
        print(f'\tTime left to sleep {sec + 1 - i} seconds')
        time.sleep(1)

def pcapToCsv(self):
    files = os.listdir("pcaps")
    # files = [f for f in os.listdir("pcaps") if os.path.isfile("pcaps/".join(f))]
    for file in files:
        # host = f'{self.hosts[self.csvsGenerated][:7]}'
        csvFilename = file.split('.')[0] + '.csv'
        tshark = f'/bin/tshark -r pcaps/{file} -Y "tcp.stream==1" \
                -T fields\
                -e frame.len \
                -e tcp.srcport \
                -e tcp.dstport \
                -e tcp.len \
                -e tcp.window_size \
                -e tcp.analysis.retransmission \
                -e tcp.analysis.fast_retransmission \
                -e tcp.analysis.bytes_in_flight \
                -e tcp.analysis.ack_rtt \
                -e frame.time \
                -e tcp.time_relative \
                -E header=y \
                -E quote=d \
                -E separator=, \
                -E occurrence=f \
                >> csvs/{csvFilename} 2> /dev/null'

        """
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
        """
        # fullCommand = f'ssh {self.user}@glomma.cs.wpi.edu \'{tshark}\''
        self.csvs.append(csvFilename)
        print(f'\trunning command: \n{tshark}')
        timeStamp = self.getTimeStamp()
        if self.csvsGenerated == self.numToRun * 2 - 1:
            subprocess.Popen(tshark, shell=True).wait()
        else:
            subprocess.Popen(tshark, shell=True)
        self.commandsRun.append((timeStamp, tshark))
        self.csvsGenerated += 1
    self.sleep(60)

    def getData():
        os.system(f'ssh btpeters@')

    def main():
        if args.time is not None:
            startTrial = f"ssh btpeters@cs.wpi.edu \" python3 ~/Research/scripts/trialTrimmed.py " \
                         f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                         f"--time {args.time} --numToRun {args.numToRun} " \
                         f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\'\" "
        else:
            startTrial = f"ssh btpeters@cs.wpi.edu \" python3 ~/Research/scripts/trialTrimmed.py " \
                         f"--batch {args.batch} --log {args.log} --cc {args.cc} --runNum {args.runNum} " \
                         f"--size {args.size} --numToRun {args.numToRun}" \
                         f"--rmem \'{args.rmem}\' --wmem \'{args.wmem}\' --mem \'{args.mem}\'\" "
        print("Running command: " + startTrial)
        try:
            os.listdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
            print("This trial has already been run, just creating plots")
        except:
            subprocess.call(startTrial, shell=True)
            getData()
        pcapToCsv()

    if __name__ == "__main__":
        main()
