# gwhelpdesk

install your own opensuse server.   I use leap version:   https://software.opensuse.org/422/en
SLES 12 sp2 and sp3 are also supported.

You can get by with a text only install,  but you can do the whole gui thing if you want.  After you install,  copy the attached gwhelpdesk_install.py script to the server, then run "python gwhelpdesk_install.py".    This will install a few needed rpm's , python modules and get the download from git.

After the script runs, cd to your install directory/gwhelpdesk and run:

python manage.py setup

This will walk you thru the setup to connect to your GW admin service, and create the initial site administrator, then do some configuration for running the application.   It will also start the gwhelpdesk script and run nginx, which is the webserver used.

FYI,  the app is written in Python use the Django framework.  It also uses a python module called gunicorn to run the django application.  The /etc/init.d/gwhelpdesk start script actually runs gunicorn.  It listens on localhost port 8000,  Then nginx is configured to act as a proxy server for gunicorn.    The setup scripts above will prompt you for an IPaddr and/or hostname and port, which is used for the appliation and nginx configuration.  Port 80 should work fine.  
