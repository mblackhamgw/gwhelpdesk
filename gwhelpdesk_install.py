import sys
import subprocess
import os, stat

#check version of Suse
with open('/etc/SuSE-release') as f:
    data = f.readlines()

print "OS is %s" % data[0]
if data[0] == 'openSUSE':
    print "openSuse is supported"
elif 'SUSE' in data[0]:
    print 'OS is %s' % data[0]
    print data[1], data[2]
    print 'Adding repository for nginx install...'
    p = subprocess.Popen(['zypper', 'addrepo', '-G', '-t', 'yum', '-c', 'http://nginx.org/packages/sles/12', 'nginix'], stdout=subprocess.PIPE)
    for line in p.stdout:
        print line

# Check python verision- 2.7 is required
pyver = '%s.%s' % (sys.version_info[0], sys.version_info[1])

if pyver == '2.7':
    print 'Python version is: %s' % pyver
else:
    print "Incorrect Python version.  Python 2.7 is required.  Ending install."
    sys.exit()

#install some needed rpms - python-pip fails on sles,  but pip is in python-setuptools
rpms = ['python-pip', 'nginx', 'git', 'python-setuptools']
for rpm in rpms:
    p = subprocess.Popen(['zypper', '-n', 'in', rpm],stdout=subprocess.PIPE)
    for line in p.stdout:
        print line

# install some python modules using pip
import pip

piplist = ['django', 'gunicorn', 'requests', 'django-baseurl' ,'django-ipware']
for mod in piplist:
    print 'pip installing: %s' % mod
    pip.main(['install', mod])

# gitpython fail using normal pip install,  had to do it this way.
p = subprocess.Popen(['pip', 'install', '--trusted-host', 'pypi.python.org' , 'gitpython'], stdout=subprocess.PIPE)
for line in p.stdout:
    print line
p.wait()

import git
print "Getting the gwhelpdesk app from git.."

# Prompt for where you want gwhelpdesk installed
baseDir = raw_input('Enter path for gwhelpdesk directory: ')
if not os.path.isdir(baseDir):
    answer = raw_input("%s path not found,  create it?  (y/n)" % baseDir)
    if answer.lower() == 'yes' or answer.lower() == 'y':
        os.mkdir(baseDir)
    else:
        'Rerun script to enter a valid diretory'
        sys.exit()

installDir = '%s/gwhelpdesk' % baseDir

# run git to fetch the code.
gitUrl = "https://github.com/mblackhamgw/gwhelpdesk.git"
repo = git.Repo.init(installDir)
origin = repo.create_remote('origin', gitUrl)
origin.fetch()
origin.pull(origin.refs[0].remote_head)

# need to modify nginx.conf to point the static dir to install directory
nginxConf = '%s/helpdesk/management/commands/nginx.conf' % installDir
newfile = '%s/helpdesk/management/commands/nginx.conf.bak' % installDir
aliasLine = '''
	        alias %s/helpdesk/static/;
	    ''' % installDir

os.rename(nginxConf, newfile)
with open(newfile, 'r') as input_file, open(nginxConf, 'w') as output_file:
    for line in input_file:
        line.strip()
        if 'alias' in line:
            output_file.write(aliasLine + '\n')
        else:
            output_file.write(line)

# run dos2unix for some files
files = ['%s/updateHelpdesk.sh' % installDir,
            '%s/enableHelpdesk.sh' % installDir,
            '%s/helpdesk/management/commands/gwhelpdesk' % installDir,
            '%s/helpdesk/management/commands/nginix.conf' % installDir,
            '%s/helpdesk/management/commands/rcnginx' % installDir,
            ]

for f in files:
    p = subprocess.Popen(['dos2unix', f], stdout=subprocess.PIPE)
    for lin in p.stdout:
        print lin

# set executable bit on some files
os.chmod('%s/enableHelpdesk.sh' % installDir, stat.S_IRWXU)
os.chmod('%s/updateHelpdesk.sh' % installDir, stat.S_IRWXU)
os.chmod('%s/manage.py' % installDir, stat.S_IRWXU)
print ''
print '---- Done with installation ----'
print ''

print '--  cd to %s,  then run python manage.py setup to modify some db records.' % installDir

