import subprocess

#a = subprocess.Popen("python3 ./runTrial.py --batch 86 --cc cubic --time 20 --tcpSettings 0")
#b = subprocess.Popen("python3 ./runTrial.py --batch 87 --cc cubic --time 20 --tcpSettings 2")
#c = subprocess.Popen("python3 ./runTrial.py --batch 88 --cc cubic --time 20 --tcpSettings 3")
#d = subprocess.Popen("python3 ./runTrial.py --batch 100 --cc cubic --time 20 --tcpSettings 1")

#a = subprocess.Popen("python3 ./runTrial.py --batch 89 --cc cubic --time 20 --tcpSettings 4")
#b = subprocess.Popen("python3 ./runTrial.py --batch 90 --cc cubic --time 20 --tcpSettings 5")
#c = subprocess.Popen("python3 ./runTrial.py --batch 91 --cc cubic --time 20 --tcpSettings 6")
#d = subprocess.Popen("python3 ./runTrial.py --batch 92 --cc cubic --time 20 --tcpSettings 7")

a = subprocess.Popen("python3 ./runTrial.py --batch 93 --cc cubic --time 20 --tcpSettings 8")
b = subprocess.Popen("python3 ./runTrial.py --batch 95 --cc cubic --time 20 --tcpSettings 10")
c = subprocess.Popen("python3 ./runTrial.py --batch 101 --cc cubic --time 20 --tcpSettings 9")

a.wait()
b.wait()
c.wait()
#d.wait()
