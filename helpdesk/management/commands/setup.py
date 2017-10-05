from django.core.management import BaseCommand
from helpdesk.models import GWSettings
from helpdesk.lib import gwlib
from shutil import copy2, move
import stat, os
from socket import gethostbyname, gethostname, getfqdn
from sys import exit
from stat import *
from helpdesk.models import Admin
from getpass import getpass
from django.contrib.auth.hashers import PBKDF2PasswordHasher

import gwhelp.settings


# The class must be named Command, and subclass BaseCommand
class Command(BaseCommand):
    help = "This doesn't do anything yet"

    def handle(self, *args, **options):


        baseDir = gwhelp.settings.BASE_DIR
        print "Let's get the info about your GroupWise Admin Server..."
        gwconfig = GWSettings.objects.all()
        if len(gwconfig) == 0:
            print 'GroupWise Admin Server Settings Configuration\n'
            gwhost = raw_input("GroupWise Admin Server IP/Hostname: ")
            gwport = raw_input('Admin Server PORT: ')
            gwadmin = raw_input('GroupWise System Administrator: ')
            gwpass = raw_input('Administrator Password: ')
            gwconfig = GWSettings(gwHost=gwhost, gwPort=gwport, gwAdmin=gwadmin, gwPass=gwpass)
            try:
                gwconfig.save()
                print 'Record saved'
            except:
                print 'Save record failed'

        elif len(gwconfig) == 1:
            print "GroupWise Settings exist"
            print 'Record shows GW Server is: %s' % gwconfig[0].gwHost
            answer = raw_input('Modify Existing record?  (y/n) :')
            if answer.lower() == 'y':
                self.updateConfig()
        print ''
        print "Okay, that's done.  Now we need to create a site Administrator.."
        admins = Admin.objects.all()
        if len(admins) == 0:
            self.createAdmin()
        else:
            print 'Hmmmm,  there is an administrator already defined'
            admin = Admin.objects.all()[0]
            print 'The admin name is %s' % admin.username
            answer = raw_input('Do you want to nuke it an create a new Admin?  (y/n) :')
            if answer.lower() == 'y':
                admin.delete()
                self.createAdmin()


        print "Two more tasks to go, create a gwhelpdesk init script and the nginx conf file"
        helpdeskScript = 'helpdesk/management/commands/gwhelpdesk'
        if os.path.isfile(helpdeskScript):
            destination = '/etc/init.d/gwhelpdesk'
            if os.path.isfile(destination):
                print "gwhelpdesk script exists,  will rename it and replace"
                move('/etc/init.d/gwhelpdesk', '/etc/init.d/gwhelpdesk.bak')
            copy2(helpdeskScript, destination)
        else:
            print "Script not found"
            exit()

        nginxConfig = 'helpdesk/management/commands/nginx.conf'
        nginxScript = 'helpdesk/management/commands/rcnginx'

        if os.path.isfile(nginxScript):
            try:
                dest = '/usr/sbin/rcnginx'
                if os.path.isfile(dest):
                    print "rcnginx exists"
                else:
                    print "copying rcnginx to /usr/sbin"
                    copy2(nginxScript, dest)
            except IOError as e:
                print e

        if os.path.isfile(nginxConfig):
            try:
                destination = '/etc/nginx/nginx.conf'

                if os.path.isfile(destination):
                    os.remove(destination)
                    bak = '/etc/nginx/nginx.conf.bak'
                    if os.path.isfile(bak):
                        os.remove(bak)
                    copy2(nginxConfig, '/etc/nginx/')
                    move('/etc/nginx/nginx.conf', '/etc/nginx/nginx.conf.bak')
                else:
                    copy2(nginxConfig, '/etc/nginx/')
                    move('/etc/nginx/nginx.conf', '/etc/nginx/nginx.conf.bak')
            except IOError as e:
                print e

        if os.path.isfile('/usr/sbin/gwhelpdesk'):
            move('/usr/sbin/gwhelpdesk', '/opt/sbin/gwhelpdesk.bak')

        if os.path.isfile('/usr/sbin/rcgwhelpdesk'):
            os.remove('/usr/sbin/rcgwhelpdesk')



        os.symlink('/etc/init.d/gwhelpdesk', '/usr/sbin/rcgwhelpdesk')
        os.chmod('/etc/init.d/gwhelpdesk', stat.S_IRWXU)
        os.chmod('enableHelpdesk.sh', stat.S_IRWXU)
        print "That's done.."

        print ''
        print ''
        self.editSettings()

        print '''
OK,  one more step for you..

Run the enableHelpdesk.sh script to enable the gwhelpdesk script for systemd.
It also enables gwhelpdesk and nginx to start at boot time. and will start
both services if you wish.

Thanks and good luck with the application.
'''

        print ''
        print ''

    def editSettings(self):
        host = ''
        ipaddr = gethostbyname(gethostname())
        print 'First, we need the ip address and/or hostname and port for the'
        print 'application to listen on.  (Yeh I now,  bad grammer)'
        print ''

        answer = raw_input('Use IP address, DNS hostname, or Both (ip / host/ both): ')
        if answer.lower() == 'ip':
            ipaddr = self.ip()
        elif answer.lower() == 'host':
            host = self.host()
        elif answer.lower() == 'both':
            ipaddr = self.ip()
            host = self.host()
        else:
            ipaddr = gethostbyname(gethostname())

        nginxport = raw_input("Listen port for ")

        if ipaddr and host:
            newline = "ALLOWED_HOSTS = ['%s', '%s']" % (ipaddr, host)
        elif ipaddr and not host:
            newline = "ALLOWED_HOSTS = ['%s']" % ipaddr
        elif host and not ipaddr:
            newline = "ALLOWED_HOSTS = ['%s']" % host




        if ipaddr != None:
            print "Using IP address: %s " % ipaddr

        if host != None:
            print "Using Hostname : %s " % host

        filename = os.path.join(os.getcwd(), 'gwhelp/settings.py')
        newfile = os.path.join(os.getcwd(), 'gwhelp/settings.py.bak')

        os.rename(filename, newfile)
        with open(newfile, 'r') as input_file, open(filename, 'w') as output_file:
            for line in input_file:
                line.strip()
                if 'ALLOWED_HOSTS' in line:
                    output_file.write(newline + '\n')
                else:
                    output_file.write(line)

        ngconf = '/etc/nginx/nginx.conf'
        newngconf = '/etc/nginx/nginx.conf.bak'

        # ngconf = 'nginx.conf'
        # newngconf = 'nginx.conf.bak'
        if not os.path.isfile(newngconf):
            os.rename(ngconf, newngconf)

        with open(newngconf, 'r') as input_file, open(ngconf, 'w') as output_file:
            for line in input_file.readlines():
                line.strip()
                if 'proxy_set_header' in line:
                    output_file.write(line)
                    continue

                if 'listen' in line:
                    listenline = '''
                listen     %s;
        ''' % nginxport
                    output_file.write(listenline)
                    continue

                if 'server_name' in line:
                    serverline = '''
                server_name     %s;

        ''' % ipaddr
                    output_file.write(serverline)
                    continue

                else:
                    output_file.write(line)

    def ip(self):
        print 'Server IP is %s' % gethostbyname(gethostname())
        use = raw_input('Use %s ? (y/n): ' % gethostbyname(gethostname()))
        if use.lower() == 'y' or use.lower() == 'yes':
            ipaddr = gethostbyname(gethostname())
        else:
            ipaddr = raw_input('Enter IP Address: ')
        return ipaddr

    def host(self):
        print 'Server FQDN name is %s' % getfqdn()

        use = raw_input('Use %s ? (y/n): ' % getfqdn())
        if use.lower() == 'y' or use.lower() == 'yes':
            host = getfqdn()
        else:
            host = raw_input('Enter FQDN : ')
            return host

    def whoami(self, gwhost, gwport, gwadmin, gwpass):
        gw = gwlib.gw(gwhost, gwport, gwadmin, gwpass)
        who = gw.whoami()
        return who

    def updateConfig(self):
        print 'GroupWise Admin Server Settings Configuration\n'
        gwhost = raw_input("GroupWise Admin Server IP/Hostname: ")
        gwport = raw_input('Admin Server PORT: ')
        gwadmin = raw_input('GroupWise System Administrator: ')
        gwpass = raw_input('Administrator Password: ')
        gwconfig = GWSettings.objects.all()[0]

        gwconfig.gwHost = gwhost
        gwconfig.gwPort = gwport
        gwconfig.gwAdmin = gwadmin
        gwconfig.gwPass = gwpass
        gwconfig.save()
        whoami = self.whoami(gwhost, gwport, gwadmin, gwpass)
        # print whoami
        if whoami == 1:
            print "Connection to GroupWise Admin Service Failed"

        elif 'roles' in whoami.keys():
            if 'SYSTEM_RECORD' in whoami['roles']:

                print "Login to GroupWise Admin service successful"

            else:
                print "%s is not a System Administrator.  Supply proper GroupWise system admin credentials" % gwadmin
                answer = raw_input('Shall we try again?  (y/n) :')
                if answer.lower() == 'y':
                    self.updateConfig()
        else:
            print "Error validating Administrator login: %s " % whoami['statusMsg']
            answer = raw_input('Shall we try again?  (y/n) :')
            if answer.lower() == 'y':
                self.updateConfig()

    def createPassword(self, password):
        hasher = PBKDF2PasswordHasher()
        mypassword = hasher.encode(password=password,
                                   salt='salt',
                                   iterations=10000
                                   )
        return mypassword

    def createAdmin(self):
        admin = Admin()
        admin.username = raw_input("Administrator User Name: ")
        admin.first_name = raw_input("First Name: ")
        admin.last_name = raw_input('Last Name: ')
        password = getpass('Password: ')
        admin.password = self.createPassword(password)
        admin.role = 'AD'
        admin.save()
        print "Administrator: %s created" % admin.username


