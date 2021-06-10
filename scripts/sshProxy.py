import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--run', type=str, help="Command to run on remote server", required=False)
parser.add_argument('--host', type=str, help="Name of remote host to run command on", required=True)
parser.add_argument('--get', type=bool, help="If get flag is set pull csvs from remote server instead of running ssh",
                    default=False, required=False)
args = parser.parse_args()

if args.get:
    #  TODO: runs SCP to copy from selected host
    pass
else:
    #  TODO: runs ssh to command remote server to run command
    pass
