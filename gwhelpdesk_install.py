import sys, subprocess, os, stat, logging
from time import sleep

def log(msg):
    logging.info(msg)
    print msg

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m-%d-%Y %H:%M',
                    filename='gwhelpdesk_install.log',
                    filemode='w')

#check version of Suse
with open('/etc/SuSE-release') as f:
    data = f.readlines()

log("OS is %s" % data[0])
sp2 = ''
sp3 = ''
if 'openSUSE' in data[0]:
    log("openSuse is supported")

elif '12' in data[1]:
    log("Adding SDK repository for git install")
    if '2' in data[2]:
        sp2 = True
        repo = 'sle-sdk/12.2/x86_64'
    if '3' in data[2]:
        sp3 = True
        repo = 'sle-sdk/12.3/x86_64'

    p = subprocess.Popen('SUSEConnect v -p %s' % repo , shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        log(line)

    print 'Adding repository for nginx install...'
    p = subprocess.Popen('zypper addrepo -G -t yum -c http://nginx.org/packages/sles/12 nginix', shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        log(line)

# Check python verision- 2.7 is required
pyver = '%s.%s' % (sys.version_info[0], sys.version_info[1])

if pyver == '2.7':
    log('Python version is: %s' % pyver)
else:
    log("Incorrect Python version.  Python 2.7 is required.  Ending install.")
    sys.exit()

#install some needed rpms - python-pip fails on sles,  but pip is in python-setuptools
log('Installing some needed rpms from Suse repository.. Please be patient')
rpms = ['python-pip', 'nginx', 'git', 'python-setuptools', 'dos2unix', 'net-tools']
for rpm in rpms:
    p = subprocess.Popen('zypper -n in %s' % rpm ,shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        log(line)

# have to install pip using easy_install
if sp3 == True or sp2 == True:
    from setuptools.command import easy_install
    easy_install.main(['-U','pip'])
    sleep(3)

# install some python modules using pip

p = subprocess.Popen('pip install --trusted-host "pypi.python.org" --upgrade pip', shell=True, stdout=subprocess.PIPE)
for line in p.stdout:
    log(line)
p.wait()

piplist = ['django', 'gunicorn', 'requests', 'django-baseurl' ,'django-ipware', 'gitpython']
for mod in piplist:
    log('pip installing: %s' % mod)
    p = subprocess.Popen('pip install --trusted-host "pypi.python.org" %s' % mod, shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        log(line)
    p.wait()
    sleep(1)

log("Getting the gwhelpdesk app from git..")

# Prompt for where you want gwhelpdesk installed
baseDir = raw_input('Enter path for gwhelpdesk directory: ')
if not os.path.isdir(baseDir):
    answer = raw_input("%s path not found,  crmbeate it?  (y/n)" % baseDir)
    if answer.lower() == 'yes' or answer.lower() == 'y':
        os.mkdir(baseDir)
    else:
        'Rerun script to enter a valid diretory'
        sys.exit()

installDir = '%s/gwhelpdesk' % baseDir

# run git to fetch the code.
gitUrl = "https://github.com/mblackhamgw/gwhelpdesk.git"
p = subprocess.Popen('GIT_SSL_NO_VERIFY=true git clone %s %s' % (gitUrl, installDir ), shell=True, stdout=subprocess.PIPE)
for line in p.stdout:
    log(line)
p.wait()
sleep(1)

#modify gwhelpdesk init script to add install directory
gwfile = '%s/helpdesk/management/commands/gwhelpdesk' % installDir
newgwfile = '%s/helpdesk/management/commands/gwhelpdesk.bak' % installDir
appdirline = 'APPDIR=%s' % installDir

os.rename(gwfile, newgwfile)

with open(newgwfile, 'r') as inputfile, open(gwfile,'w') as outputfile:
    for line in inputfile:
        line.strip()
        if 'APPDIR=' in line:
            print 'Line = %s' % line
            outputfile.write(appdirline + '\n')
        else:
            outputfile.write(line)

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
            '%s/helpdesk/management/commands/gwhelpdesk' % installDir,
            '%s/helpdesk/management/commands/nginx.conf' % installDir,
            '%s/helpdesk/management/commands/rcnginx' % installDir,
            ]

for f in files:
    p = subprocess.Popen('dos2unix %s' % f, shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        log(line)

# set executable bit on some files
os.chmod('%s/updateHelpdesk.sh' % installDir, stat.S_IRWXU)
os.chmod('%s/manage.py' % installDir, stat.S_IRWXU)
log('')
log('---- Done with installation ----')
log('')

print '--  cd to %s,  then run python manage.py setup to modify some db records.' % installDir
