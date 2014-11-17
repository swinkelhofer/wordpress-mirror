import os
import re
import subprocess
import fileinput
from functools import partial

# callback method for incrementing the stringlengths of the serialized theme settings
def evaluate(match):
	return match.group(1) + str(int(match.group(2))+7) + match.group(3)

remote_sql_pw = "FIDHaZky";
local_sql_pw = "FD26Ur2k"
remote_user = "web5"
local_user = "web10"
local_db = "usr_web10_1"
path = "/var/www/web10/html"
remote_path = "/var/www/web5/html"
host = "88.80.210.101"

# Reads Domains into an array
domainList = []
with open('domains.txt', 'r') as domains:
	for line in domains:
		domainList.append(re.sub(r"\n", "", line))

print "# Dropping local database"
subprocess.call("mysqldump --all-databases -u %s --password=%s --extended-insert=FALSE --complete-insert=TRUE > %s/dump.txt" % (remote_user, remote_sql_pw, path,), shell=True)

print "# Dumping remote database"
subprocess.call("echo \"DROP DATABASE %s;\" | mysql --user=%s --password=%s" % (local_db, local_user, local_sql_pw,), shell=True)

print "# Replacing usernames and domains and serialized theme settings"
# loops through the lines of the file, replacing all strange content
with open(path + '/out.txt', 'w') as output:
	with open(path + '/dump.txt', 'r') as file:
		for line in file:
			line = re.sub(r"%s" % (remote_user,), "%s" % (local_user,), line)
			for domain in domainList:
				line = re.sub(r"%s"%domain, "mirror.%s"%domain, line)
			line = re.sub(r"(s:)([0-9]+)(:\\\"http)", evaluate, line)
			output.write(line)
print "# Importing modified dump"
subprocess.call("mysql --user=%s --password=%s < %s/out.txt" % (local_user, local_sql_pw, path), shell=True)

print "# Syncing WordPress files"
subprocess.call("rsync -az -e ssh %s@%s:%s/* %s/" % (remote_user, host, remote_path, path), shell=True)
subprocess.call("scp %s@%s:%s/wp-config.php %s/" % (remote_user, host, remote_path, path), shell=True)

print "# Replacing wp-config content"
for line in fileinput.input(path + "/wp-config.php", inplace=True):
	line = re.sub(r"%s" % (remote_user), "%s" % (local_user), line)
	line = re.sub(r"%s" % (remote_sql_pw), "%s" % (local_sql_pw), line)
	line = re.sub(r"blog.zawiw.de", "blog.mirror.zawiw.de", line)
	print "%s" % (line)
print "# Removing intermediate files"
os.remove(path+"/dump.txt")
os.remove(path+"/out.txt")
