import subprocess

def subprocess_cmd(command):
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    print proc_stdout
    return proc_stdout

cmd = "ps -x | grep python"
resp = subprocess_cmd(cmd)
lines = resp.split("\n")
#print lines
pids = ""
for i in lines:
	print i
	if "ttys" in i:
		pid, _ = i.split("ttys")
	elif "pts" in i:
		pid, _ = i.split("pts")
	elif "?" in i:
		pid, _ = i.split("?")
	pids += pid

#for Mac
cmd = "kill " + pids

#for Linux
#cmd = "kill -9 " + pids

print cmd
resp = subprocess_cmd(cmd)
