GWHELPDESK

When GroupWise 2014 was released, it included a brand new web based administration console.  With the new admin tool, administrators could assign other GroupWise users as administrators at a System, Domain or Post Office level.  While handy,  many GroupWise customers have requested that this be expanded to provide more of a helpdesk type role based administration model,  where users can be assigned a role to act as a user/group administrator across the entire GroupWise system,  but not be able to add or modify system objects.

GWHelpdesk is an attempt to address this need.   It uses the GroupWise REST API for all  GroupWise admin functions.  The application configuration consists of a record for your GroupWise Admin server, with IP addr/hostname, admin port, system admin name and password.  These settings are used for all communication to GroupWise admin service.  
The application has the ability to have 4 administrative roles:

  •	Administrator - Has all access to all GroupWise user objects.  Also use this role to create other administrators.
  •	Helpdesk – Can add/modify/delete GroupWise users.
  •	HelpDesk Light – Can only modify users, not add or delete.
  •	Password – Can only be used to change user passwords.

Requirements:

  •	A Linux server.  Tested and supported on openSuse 42.2, 42.3 - (Leap distribution)  https://software.opensuse.org/distributions/leap
    Also tested on SLES12 Sp2 and Sp3.  (on your own for licensing this OS,  the GroupWise SLES entitlement does not apply to this application.
  •	A valid internet connection, required to have access to github.
  •	A GroupWise 2014 system.  Only  tested against GroupWise 2014 SP2, no testing prior to that.

You can get by with a text only install for the OS, but you can do the whole GUI thing if you want. After you install, copy the gwhelpdesk_install.py script to the server, then run "python gwhelpdesk_install.py". This will install a few needed rpm's, python modules and download gwhelpdesk from github.com

After the script finishes, cd to your install directory/gwhelpdesk and run:
  python manage.py setup
This will walk you thru the setup to connect to your GW admin service, and create the initial site administrator, then do some configuration for running the application. It will also start the gwhelpdesk script and run nginx, which is the webserver used.

The app is written in Python use the Django framework. It also uses a python module called gunicorn to run the django application. The /etc/init.d/gwhelpdesk start script actually runs gunicorn. It listens on localhost port 8000.   nginx is configured to act as a proxy server for gunicorn. The setup scripts above will prompt you for an IPaddr and/or hostname and port, which is used for the application and nginx configuration. Port 80 should work fine.

If you wish to enable SSL for nginx, see:
http://nginx.org/en/docs/http/configuring_https_servers.html


