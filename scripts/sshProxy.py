import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--run', type=str, help="Command to run on remote server", required=False)
# parser.add_argument('--host', type=str, help="Name of remote host to run command on", required=False)
# parser.add_argument('--get', type=bool, help="If get flag is set pull pcaps from remote server instead of running ssh"
    # , default=False, required=False)
args = parser.parse_args()
os.system(args.run)
