# This script was adapted from work by Kush Shah whose work can be
# found here: https://github.com/kush5683/TCP-over-Satellite/blob/main/MediatorCode/trial.py

import argparse
import os
import time
import datetime
from datetime import datetime
from fabric2 import Connection


# Returns formatted timestamp
def get_timestamp():
    return datetime.now().strftime('%Y_%m_%d-%H-%M-%S')


class Trial:

    def __init__(self, congestion_algorithm, batch_num, run_num, run_len, num_to_run, user, data='20M', timeout=600,
                 log=False, port=None, tcp_mem="60000000", tcp_wmem="60000000", tcp_rmem="60000000", debug=False):
        if port is None:
            port = ['5201']
        # Maps congestion control to which server the experiment should use
        self.dictionary = {"hybla": "mlcneta.cs.wpi.edu",
                           "cubic": "mlcnetb.cs.wpi.edu",
                           "bbr": "mlcnetc.cs.wpi.edu",
                           "pcc": "mlcnetd.cs.wpi.edu"}
        self._congestion_algorithm = congestion_algorithm
        self._data = data
        self._time = run_len
        self._batch_num = batch_num
        self._run_num = run_num
        self._user = user
        self._num_to_run = num_to_run
        self._pcaps = []
        self._client_pcaps = []
        self._commands_run = []
        self._log = log
        self._timeout = timeout
        self._port = port
        self._pcaps_sent = 0
        self._csvs_generated = 0
        self._done = False
        self._tcp_mem = tcp_mem
        self._tcp_wmem = tcp_wmem
        self._tcp_rmem = tcp_rmem
        self._host = self.dictionary.get(congestion_algorithm)
        self._glomma = Connection(host='glomma.cs.wpi.edu', user=self._user)
        self._server = Connection(host=self._host, user=self._user)
        self._vorma = Connection(host='vorma.cs.wpi.edu', user=self._user)
        self._setup_commands = [
            f'sudo sysctl -w net.ipv4.tcp_mem=\"{self._tcp_mem}\"',
            f'sudo sysctl -w net.ipv4.tcp_wmem=\"{self._tcp_wmem}\"',
            f'sudo sysctl -w net.ipv4.tcp_rmem=\"{self._tcp_rmem}\"',
        ]
        self._debug = debug
        print(self._congestion_algorithm)
        print(self._host)
        # for use if running two downloads at once

        # if self.cc[0] == self.cc[1]:
        #    self.hosts.append(dictionary.get(self.cc[0]))
        #    self.hosts.append(dictionary.get('same'))
        #    command = f'ssh {self.user}@mlcnetd.cs.wpi.edu \"sudo sysctl -w net.ipv4.tcp_congestion_control=\'{self.cc[1]}\'\"'

    # Logs the command that is run and then runs it
    def log_and_run(self, connection, command):
        if self._debug:
            print(f'\trunning command: {command}')
        self._commands_run.append((get_timestamp, command))
        if connection is None:
            os.system(command)
        else:
            connection.run(command)

    # Sleep and update on how much longer
    def sleep(self, sec):
        for i in range(1, sec + 1):
            if self._debug:
                print(f'\tTime left to sleep {sec + 1 - i} seconds')
            time.sleep(1)

    # Remove files from the last run and ensure settings are all correct 
    def set_up(self):
        # Setup filesystem
        self.log_and_run(None, f'rm -r tmp')
        self.log_and_run(None, f'mkdir tmp')
        os.chdir(f'tmp')
        file_prefix = f'Trial_{self._batch_num}'
        self.log_and_run(None, f'mkdir {file_prefix}')
        self.log_and_run(self._glomma, f'mkdir {file_prefix}')
        self.log_and_run(self._server, f'mkdir {file_prefix}')
        self.log_and_run(None, f'mkdir {file_prefix}/pcaps')
        self.log_and_run(None, f'mkdir {file_prefix}/csvs')
        self.log_and_run(None, f'mkdir {file_prefix}/plots')
        self.log_and_run(None, f'mkdir {file_prefix}/logs')
        os.chdir(f'{file_prefix}')

        # Ensure settings are correct on the server
        self.enable_tuning()
        self.enable_hystart()
        self.disable_max_cap()
    
        # Ensure routes are correct on Glomma
        self.log_and_run(self._glomma, f'./setup_routes.sh')  # TODO: make changing between vorma and satellite easier
        
        # Set buffer sizes on both glomma and server
        for command in self._setup_commands:
            self.log_and_run(self._glomma, command)
            self.log_and_run(self._server, command)

        # Ensure Vorma is running the right netem settings
        self.log_and_run(self._vorma, 'sudo ./satellite.sh')
        return

    # Ensure sever is using the right congestion control algorithm
    def set_protocol_remote(self):
        protocol = list(self.dictionary.keys())[list(self.dictionary.values()).index(self._host)]
        command = f'sudo sysctl -w net.ipv4.tcp_congestion_control=\'{protocol}\''
        self.log_and_run(self._server, command)
        return

    # Start the iperf server
    # This runs the ssh command directly as to avoid waiting for the command to return
    def start_iperf3_server(self):
        iperf3_server_start = f"ssh {self._user}@{self._host} \"iperf3 -s -p {self._port}\""
        self.log_and_run(None, iperf3_server_start)

    # Start the iperf client
    # This uses the connection object to ensure it finishes before moving on
    def start_iperf3_client(self):
        # This just decides if it should run a download for an amount of data or for a time
        if self._data is not None:
            iperf3_start_client = f'iperf3 -R -c {self._host} -n {self._data} -p {self._port}'
        else:
            iperf3_start_client = f'iperf3 -R -c {self._host} -t {self._time} -p {self._port}'
        self.log_and_run(self._glomma, iperf3_start_client)

    # Start the tcpdump on the server
    # Run with raw ssh for reasons stated above
    def start_tcpdump_server(self):
        timestamp = get_timestamp()
        filename = f'Trial_{self._batch_num}/{self._congestion_algorithm}_{timestamp}.pcap'
        tcpdump = f'ssh {self._user}@{self._host} \"sudo tcpdump -s 96 port {self._port} -w {filename}\"'
        self._pcaps.append(filename)
        self.log_and_run(None, tcpdump)
        
    # Start the tcpdump on the client
    def start_tcpdump_client(self):
        timestamp = get_timestamp()
        filename = f'Trial_{self._batch_num}/{self._congestion_algorithm}_{timestamp}.pcap'
        tcpdump = f'ssh {self._user}@glomma.cs.wpi.edu \"sudo tcpdump -i 2 -s 96 port {self._port} -w {filename}\"'
        self._client_pcaps.append(filename)
        self.log_and_run(None, tcpdump)

    # Gets the pcaps from the client and server
    def get_pcaps(self):
        for file in self._pcaps:
            scp_from_server = f'scp -i ~/.ssh/id_rsa {self._user}@{self._host}:~/{file} '\
                            f'/csusers/{self._user}/Research/tmp/Trial_{self._batch_num}/pcaps&'
            self.log_and_run(None, scp_from_server)
            self.sleep(3)

        for file in self._client_pcaps:
            host = "glomma.cs.wpi.edu"
            scp_from_client = f'scp -i ~/.ssh/id_rsa {self._user}@{host}:~/{file} '\
                              f'/csusers/{self._user}/Research/tmp/Trial_{self._batch_num}/pcaps&'
            self.log_and_run(None, scp_from_client)
            self.sleep(3)

    # Parses commands run into a log to be saved
    def make_log_file(self):
        timestamp = get_timestamp()
        filename = f'{timestamp}-command-log.txt'
        f = open(filename, "x")
        for command in self._commands_run:
            f.write(f'{command[0]} : {command[1]}\n')
        f.close()

    # Terminate any of the programs we were running
    def terminate_commands(self):
        commands = ['iperf3', 'tcpdump', 'UDPing']
        for command in commands:
            pkill = f'sudo pkill -2 {command}'
            self.log_and_run(self._glomma, pkill)
            self.log_and_run(self._server, pkill)

    # Stop any commands that are still running and cleanup files
    def cleanup(self):
        self.terminate_commands()
        if self._done:
            remove = f'sudo rm -r Trial_{self._batch_num}'
            self.log_and_run(self._glomma, remove)
            self.log_and_run(self._server, remove)
            if self._log:
                self.make_log_file()

    # What follows are a series of short functions mostly created for readability
    def enable_tuning(self):
        command = 'sudo sysctl net.ipv4.tcp_moderate_rcvbuf=1'
        self.log_and_run(self._glomma, command)

    def disable_tuning(self):
        command = 'sudo sysctl net.ipv4.tcp_moderate_rcvbuf=0'
        self.log_and_run(self._glomma, command)

    def remove_limit(self):
        command = 'sudo ~/remove.sh'
        self.log_and_run(self._vorma, command)

    def enable_hystart(self):
        command = 'sudo sh -c \'echo 1 >> /sys/module/tcp_cubic/parameters/hystart\''
        self.log_and_run(self._server, command)

    def disable_hystart(self):
        command = 'sudo sh -c \'echo 0 >> /sys/module/tcp_cubic/parameters/hystart\''
        self.log_and_run(self._server, command)

    def enable_max_cap(self):
        command = 'sudo sh -c \'echo 1 >> /sys/module/tcp_cubic/parameters/hystart_delay_max\''
        self.log_and_run(self._server, command)

    def disable_max_cap(self):
        command = 'sudo sh -c \'echo 0 >> /sys/module/tcp_cubic/parameters/hystart_delay_max\''
        self.log_and_run(self._server, command)

    def setup_kern_log(self):
        command = 'sudo sh -c \'echo \"\" > /var/log/kern.log\''
        self.log_and_run(self._server, command)

    # This moves the file that is currently in the kernal log and then resets it to a blank file
    def move_kern_log(self):
        timestamp = get_timestamp()
        command = f'sudo sh -c \'cp /var/log/kern.log ~/Trial_{self._batch_num}/{self._congestion_algorithm}_{timestamp}.log\''
        self.log_and_run(self._server, command)
        self.setup_kern_log()

    def route_satellite(self):
        command = '~/setup_routes.sh'
        self.log_and_run(self._glomma, command)

    def route_vorma(self):
        command = '~/setup_routes.sh vorma'
        self.log_and_run(self._glomma, command)

    # move all files in the logs folder to the local logs folder
    def get_logs(self):
        host = self._host
        change_ownership = f'sudo chown -R {self._user}: ~/Trial_{self._batch_num}'
        self.log_and_run(self._server, change_ownership)
        scp_from_server = f'scp -i ~/.ssh/id_rsa {self._user}@{host}:~/Trial_{self._batch_num}/* /csusers/{self._user}/Research/tmp/Trial_{self._batch_num}/logs&'
        self.log_and_run(None, scp_from_server)

    # start UDPing server and uses raw ssh to not wait
    def start_udping_server(self):
        command = f'ssh {self._user}@{self._host} \"~/sUDPing\"'
        self.log_and_run(None, command)

    # starts corresponding UDPing client using raw ssh
    def start_udping_client(self):
        filename = f'Trial_{self._batch_num}/ping_{get_timestamp()}.csv'
        command = f'ssh {self._user}@glomma.cs.wpi.edu \"~/myUDPing -h {self._host} -p 1234 -n 5 -c {filename}\"'
        self.log_and_run(None, command)

    # move all files in the csvs folder to the local csvs folder
    def get_csv(self):
        prefix = f'/csusers/{self._user}/Research/tmp/Trial_{self._batch_num}'
        scp_from_server = f'scp -i ~/.ssh/id_rsa {self._user}@glomma.cs.wpi.edu:~/Trial_{self._batch_num}/* {prefix}/csvs&'
        self.log_and_run(None, scp_from_server)

    # Actually runs the trial calling all the previous methods
    def start(self):
        os.chdir(os.path.expanduser("~/Research"))
        os.system('clear')
        self.cleanup()
        if self._run_num == 0:
            self.set_up()
            self.set_protocol_remote()
            self.disable_max_cap()
        self.setup_kern_log()

        # run downloads
        for i in range(self._num_to_run):
            print(f'Running Trial #{i+1} of {self._num_to_run}')
            # For comparing runs with different settings make changes here
            if i % 2 == 0:
                self.route_satellite()
            else:
                self.route_vorma()
            self.start_iperf3_server()
            self.start_iperf3_client()
            self.move_kern_log()
            self.terminate_commands()

        # Get data collected
        self.get_logs()

        self._done = True

        # Done with Trials now put things back
        self.remove_limit()
        self.enable_hystart()
        self.enable_max_cap()
        self.cleanup()

    # This is the same as above but without the for loop
    def start_single(self):
        os.chdir(os.path.expanduser("~/Research"))
        os.system('clear')
        self.cleanup()
        if self._run_num == 0:
            self.set_up()
            self.disable_max_cap()
            self.set_protocol_remote()
        self.enable_hystart()
        self.route_satellite()
        self.start_iperf3_server()
        self.start_udping_server()
        self.start_udping_client()
        self.sleep(5)
        self.start_iperf3_client()
        self.sleep(5)
        self.move_kern_log()
        self.terminate_commands()
        self.get_logs()
        self.get_csv()
        self._done = True
        self.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, help='What batch number is this', required=True)
    parser.add_argument('--user', type=str, help='user to log into all machines with', required=True)
    parser.add_argument('--log', type=bool, help='Use log all commands run', default=True)
    parser.add_argument('--cc', type=str, help="congestion control algorithm", required=True)
    parser.add_argument('--runNum', type=int, help="what run number is this", required=True)
    parser.add_argument('--time', type=int, help="How long should the download run for", default=60)
    parser.add_argument('--size', type=str, help="How much data should be downloaded (exclusive use with time arg)",
                        default=None)
    parser.add_argument('--numToRun', type=int, help="Total number of trial to run")
    parser.add_argument('--rmem', type=str, help='Value for rmem', default="60000000 60000000 60000000")
    parser.add_argument('--wmem', type=str, help='Value for wmem', default="60000000 60000000 60000000")
    parser.add_argument('--mem', type=str, help='Value for mem', default="60000000 60000000 60000000")
    parser.add_argument('--port', type=int, help='Port number to run iperf3 on', defualt=5201)
    args = parser.parse_args()

    congestion_algorithm = []

    for c in args.cc.split(" "):
        congestion_algorithm.append(c)

    os.system(f'echo {args.rmem}')
    if args.window:
        args.wmem = f'4096 16384 {args.window}'
    t = Trial(data=args.size, batch_num=args.batch, log=args.log, congestion_algorithm=congestion_algorithm,
              run_num=args.runNum, num_to_run=args.numToRun, run_len=args.time, tcp_rmem=args.rmem, tcp_mem=args.mem,
              tcp_wmem=args.wmem, port=args.port, user=args.user)

    t.start_single()
    print("All done")
    exit(0)


if __name__ == "__main__":
    main()
