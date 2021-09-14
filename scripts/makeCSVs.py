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

def pcapToCsv(files):
    # files = [f for f in os.listdir("pcaps") if os.path.isfile("pcaps/".join(f))]
    csvsGenerated = 0
    numToRun = 5
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
                > csvs/{csvFilename} 2> /dev/null'

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
        print(f'\trunning command: \n{tshark}')
        if csvsGenerated == numToRun * 2 - 1:
            subprocess.Popen(tshark, shell=True).wait()
        else:
            subprocess.Popen(tshark, shell=True)
    sleep(10)

def getData():
    print("getting data")
    os.system(f'mkdir Trial_{args.batch}')
    os.system(f'mkdir Trial_{args.batch}/csvs Trial_{args.batch}/pcaps')
    os.system(f'scp -i ~/.ssh/id_rsa btpeters@cs.wpi.edu:~/Research/tmp/Trial_{args.batch}/pcaps/* ~/Research/Trial_{args.batch}/pcaps&')


def main():
    os.chdir(f'Research')
    print("in Research")
    # os.listdir(f'C:/satellite-research/csvs/Trial_{args.batch}')
    getData()
    os.chdir(f'Trial_{args.batch}')
    print(os.getcwd())
    pcapToCsv(files=os.listdir(f'./pcaps'))

if __name__ == "__main__":
    main()
