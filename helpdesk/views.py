from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponseRedirect, reverse, render_to_response
from django.contrib.auth.hashers import check_password, make_password, is_password_usable, PBKDF2PasswordHasher
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages
from .forms import *
from django.conf import settings
import logging, os
import logging.config
from lib import gwlib

from logging.handlers import RotatingFileHandler
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logfile = '%s/logs/helpdesk.log' % settings.BASE_DIR
if not os.path.isfile(logfile):
    open(logfile, 'a').close()


logConfig = {
    'version' : 1,
    'handlers' : {
        'filehandler': {
            'class' : 'logging.handlers.RotatingFileHandler',
            'maxBytes': 500000,
            'backupCount': 5,
            'formatter':'myFormatter',
            'filename': logfile
        }
    },
    'loggers': {
      'helpdesk':{
          'handlers':['filehandler'],
          'level':'INFO',
      }
    },
    'formatters': {
        'myFormatter':{
            'format': '%(asctime)s - %(message)s',
            'datefmt': '%m/%d/%Y %H:%M:%S'
        }
    }
}
logging.config.dictConfig(logConfig)
logger = logging.getLogger('helpdesk')

# Create your views here.

def addadmin(request):
    request.session.header = 'Add Site or GroupWise Administrator'
    if request.method == "POST":
        form = AdminForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            pwd = cd['password']
            pwd2 = cd['password2']
            enc = createPassword(pwd)
            enc2 = createPassword(pwd2)
            obj = form.save(commit=False)
            obj.password = enc
            obj.password2 = enc2
            obj.save()
            if 'username' in cd.keys():
                log(request,'Admin: %s added' % cd['username'])
            return HttpResponseRedirect(reverse('admins'))
    else:
        form = AdminForm()
    return render(request, 'helpdesk/addadmin.html', {'form': form})

def admins(request):

    ads = Admin.objects.all()
    if request.method == "POST":

        form = AdminForm(request.POST)
        print form.errors
        if form.is_valid():

            cd = form.cleaned_data
            user = Admin.objects.get(username=cd['username'])

            if 'save' in request.POST:
                first_name = cd['first_name']
                last_name = cd['last_name']
                role = cd['role']
                user.first_name = first_name
                user.last_name = last_name
                user.role = role
                user.save()
                log(request, 'Admin: %s modified' % cd ['username'])

            elif 'chpwd' in request.POST:
                id = cd['username']
                form = AdminForm(request.POST)
                return render(request, 'helpdesk/changeadminpassword.html', {'form': form, 'id': id} )

            elif 'delete' in request.POST:
                user.delete()
                log(request, 'Administrator: %s deleted' % cd['username'])

        ads = Admin.objects.all()
        return render(request, 'helpdesk/admins.html', {'form': form, 'ads': ads})
    else:
        form = AdminForm()
    return render(request, 'helpdesk/admins.html', {'form': form, 'ads': ads})

def addtogroups(request):
    gw = gwInit()
    if request.method == "POST":
        form = Groups(request.POST)
        return render(request, 'helpdesk/groups.html',
                     {'form': form})
    else:
        form = Groups()
        groupList = gw.getGroups()
        return render(request, 'helpdesk/addtogroups.html',
                      {'form': form, 'groups': groupList})

def adduser(request):
    request.session.header = 'New GroupWise User'
    gw = gwInit()
    polist = gw.getPolist()
    if request.method == "POST":
        form = AddUser(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            pwd = cd['password']
            pwd2 = cd['password2']
            po = cd['postOfficeName']

            for postoffice in polist:
                if po == postoffice['name']:
                    pourl = postoffice['url']
                    externalpo = postoffice['external']

            name = cd['name']
            givenName = cd['givenName']
            surname = cd ['surname']

            postdata = {}
            postdata['name'] = name
            postdata['givenName'] = givenName
            postdata['surname'] = surname
            if externalpo == False:
                postdata['password'] = pwd
            retvalues = gw.addUser(pourl, postdata)

            if 'error' in retvalues.keys():
                messages.add_message(request, messages.ERROR,retvalues['statusMsg'])

            else:
                if 'location' in retvalues:
                    log(request, 'GroupWise User %s added to %s' % (name, po))
                    userData = gw.getObjectByUrl(retvalues['location'])
                    request.session['id'] = userData['id']

                    addressFormats = gw.addrFormats()
                    emailAddrs = gw.userAddresses(userData['@url'])
                    ldap = gw.checkPoLdap(userData['postOfficeName'])

                    if (ldap == 1) and 'ldapDn' in userData.keys():
                        userData['ldap'] = 'true'
                    else:
                        userData['ldap'] = 'false'
                    form = UserDetails()
                    return render(request, 'helpdesk/userdata.html',
                                  {'form': form, 'user': userData, 'addressFormats': addressFormats,
                                   'emailAddrs': emailAddrs})
    else:
        form = UserDetails()
    return render(request, 'helpdesk/adduser.html', {'form': form, 'polist': polist})

def changeadminpassword(request):
    username = request.session['adminname']
    request.session.header = 'Change Password for Administrator %s' %username
    admin = Admin.objects.get(username = username)
    form = AdminForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            cd = form.cleaned_data
            pwd = cd['password']
            pwd2 = cd['password2']
            if pwd != pwd2:
                messages.add_message(request, messages.WARNING, "Passwords Do Not Match")
                return render(request, 'helpdesk/changeadminpassword.html', {'form': form, 'admin': admin})
            enc = createPassword(pwd)
            enc2 = createPassword(pwd2)
            admin.password = enc
            admin.save()
            log(request, 'Password changed for admin: %s' % username)
            return HttpResponseRedirect('/logout/')
    return render(request, 'helpdesk/changeadminpassword.html', {'form': form, 'admin': admin})

def changepassword(request):
    if request.method == "POST":
        form = changePassword(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            id = cd['id']
            name = cd['name']
            pwd = cd['password']
            pwd2 = cd['password2']
            if pwd != pwd2:
                messages.add_message(request, messages.WARNING, "Passwords Do Not Match")
                return render(request, 'helpdesk/changepassword.html', {'form': form, 'id': id, 'name': name})
            else:
                gw = gwInit()
                pwdchange = gw.changePass(id, pwd)
                log(request, 'GroupWise password changed for user: %s' % name)
                messages.add_message(request, messages.SUCCESS, "Password Changed")
                return render(request, 'helpdesk/changepassword.html', {'name': name})
        else:
            return render(request, 'helpdesk/changepassword.html')
    else:
        return render(request, 'helpdesk/changepassword.html')

def checkLdap(postoffice, polist):
    for po in polist:
        if po['name'] == postoffice:
            return po['ldap']

def createPassword(password):
    hasher = PBKDF2PasswordHasher()
    mypassword = hasher.encode(password=password,
        salt='salt',
        iterations=10000
        )
    return mypassword

def deluser(request):
    id = request.session['id']
    name = id.split('.')[3]

    gw = gwInit()
    response = gw.delUser(id)
    log(request, 'Deleted GroupWise user %s' % name)
    return render(request, 'helpdesk/deluser.html')

def dissociate(request):
    id = request.session['id']
    gw = gwInit()
    addressFormats = gw.addrFormats()
    response = gw.dissociate(id)
    if response == "":
        userData = gw.getObject(id)
        log(request, 'Dissociated %s from directory' % userData['name'])

        emailAddrs = gw.userAddresses(userData['@url'])
        ldap = gw.checkPoLdap(userData['postOfficeName'])

        if (ldap == 1) and 'ldapDn' in userData.keys():
            userData['ldap'] = 'true'
        else:
            userData['ldap'] = 'false'
        form = UserDetails()
        return render(request, 'helpdesk/userdata.html',
                      {'form': form, 'user': userData, 'addressFormats': addressFormats,
                       'emailAddrs': emailAddrs})
    else:
        userData = gw.getObject(id)
        emailAddrs = gw.userAddresses(userData['@url'])
        ldap = gw.checkPoLdap(userData['postOfficeName'])

        if (ldap == 1) and 'ldapDn' in userData.keys():
            userData['ldap'] = 'true'
        else:
            userData['ldap'] = 'false'
        form = UserDetails()
        return render(request, 'helpdesk/userdata.html',
                      {'form': form, 'user': userData, 'addressFormats': addressFormats,
                       'emailAddrs': emailAddrs})

def groups(request):
    request.session.header = 'Group Membership'
    gw = gwInit()
    gwid = request.session['id']
    groupList = gw.userGroupMembership(gwid)


    if request.method == "POST":
        form = UserGroups(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            userid = request.session['id']
            grpid = cd['grpid']
            groupname = cd['group']
            participation = cd['participation']
            if 'edit' in request.POST.keys():
                x = gw.updateGroupMembership(userid, grpid, participation)
                log(request, 'Modified Group Participation for user: %s in group: %s' % (request.session['name'], groupname))
                groupList = gw.userGroupMembership(gwid)
                return render(request, 'helpdesk/groups.html', {'form': form, 'groupList': groupList})

            elif 'remove' in request.POST.keys():
                remove = gw.removeFromGroup(userid, grpid)
                log(request, 'Removed %s from group: %s' % (request.session['name'], groupname))
                groupList = gw.userGroupMembership(gwid)
                return render(request, 'helpdesk/groups.html', {'form': form, 'groupList': groupList})

            elif 'add' in request.POST.keys():
                grps = request.POST.getlist('groups')
                gw.addUserToGroups(grps, request.session['id'])
                groupList = gw.userGroupMembership(request.session['id'])
                return render(request, 'helpdesk/groups.html', {'form': form, 'groupList': groupList})

        return render(request, 'helpdesk/groups.html', {'form': form, 'groupList': groupList})
    else:
        form = UserGroups()
    return render(request, 'helpdesk/groups.html', {'form': form, 'groupList': groupList})

def gwconfig(request):
    request.session.header = 'GroupWise Admin Service Configuration'
    gwdata = GWSettings.objects.all()
    if len(gwdata) == 1:
        form = GWConfig(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            record = gwdata[0]
            record.gwHost = cd['gwHost']
            record.gwPort = cd['gwPort']
            record.gwAdmin = cd['gwAdmin']
            record.gwPass = cd['gwPass']
            record.save()
            gw = gwInit()

            whoami = gw.whoami()

            if whoami == 1:
                messages.add_message(request, messages.ERROR,
                                         "Connection to GroupWise Admin Service Failed,  Check settings.")

            elif 'roles' in whoami.keys():
                if 'SYSTEM_RECORD' in whoami['roles']:
                    messages.add_message(request, messages.SUCCESS, "Login to GroupWise Admin service successful")
                    # form.save()
                else:
                    messages.add_message(request, messages.WARNING,
                                         "%s is not a System Administrator.  Supply proper GroupWise system admin credentials" % record.gwAdmin)
            else:
                status = whoami['statusMsg']
                messages.add_message(request, messages.ERROR, status)
            gwdata = GWSettings.objects.all()
        return render(request, 'helpdesk/gwconfig.html', {'form': form, 'gwconfig': gwdata[0]})

    if request.method == "POST":
        form = GWConfig(request.POST)
        if form.is_valid():

            cd = form.cleaned_data
            if len(gwdata) == 0:
                form.save()
            elif len(gwdata) == 1:
                record = GWSettings.objects.get(gwHost=cd['gwHost'])
                record.gwHost = cd['gwHost']
                record.gwPort = cd['gwPort']
                record.gwAdmin = cd['gwAdmin']
                record.gwPass = cd['gwPass']
                record.save()
                gw = gwInit()

                whoami = gw.whoami()
                if 'roles' in whoami.keys():
                    if 'SYSTEM_RECORD' in whoami['roles']:
                        messages.add_message(request, messages.SUCCESS, "OK")
                    else:
                       messages.add_message(request, messages.WARNING, "%s is not a System Administrator.  Supply proper GroupWise system admin credentials" % gwadmin)
                else:
                    status = whoami['statusMsg']
                    messages.add_message(request, messages.ERROR, status)
                return render(request, 'helpdesk/gwconfig.html')
    else:
        form = GWConfig()
        return render(request, 'helpdesk/gwconfig.html', {'form': form })

    gwdata = GWSettings.objects.all()

    return render(request, 'helpdesk/gwconfig.html', {'form': form, 'gwconfig': gwdata[0]})

def gwInit():
    gwall = GWSettings.objects.all()
    if len(gwall) == 1:
        gwdata = gwall[0]
        gwhost = gwdata.gwHost
        gwport = gwdata.gwPort
        gwadmin = gwdata.gwAdmin
        gwpass = gwdata.gwPass
        gw = gwlib.gw(gwhost, gwport, gwadmin, gwpass)
        return gw
    else:
        return 1

def index(request):
    if 'adminname' not in request.session:
        return HttpResponseRedirect('/login/')

    return render(request, 'helpdesk/index.html')

def log(request, msg):
    message = '[%s] - %s' % (request.session['adminname'], msg)
    logger.info(message)

def login(request):
    admins = Admin.objects.all()
    if len(admins) == 0:
        messages.add_message(request, messages.ERROR, "There are no Administrators defined.\n  Please stop gwhelpdesk and run /var/gwhepdesk/manage.py setup." )


    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            username = cd['username']
            try:
                user = Admin.objects.get(username=username)
            except:
                messages.add_message(request, messages.ERROR, "%s login id not found." % username)
                return render(request, 'helpdesk/login.html', {'form': form})
            pwd = cd['password']
            encodedpwd = createPassword(pwd)
            if encodedpwd != user.password:

                messages.add_message(request, messages.ERROR, "Incorrect password for %s ." % username)
                return render(request, 'helpdesk/login.html', {'form': form})
            else:
                adminuser = Admin.objects.get(username=username)
                role = adminuser.role
                request.session['adminname'] = username
                request.session['role'] = role
                request.session['last_name'] = adminuser.last_name

                from ipware.ip import get_ip
                ip = get_ip(request)
                if ip is not None:
                    log(request, "Logged in as %s from IP %s" % (username, ip))
                else:
                    print("we don't have an IP address for user")

                return HttpResponseRedirect('/index/')

            return render(request, 'helpdesk/login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'helpdesk/login.html', {'form':form})

def logout(request):
    log(request,'%s Logged out' % request.session['adminname'])
    del request.session['adminname']
    del request.session['role']
    request.session.modified = True
    return HttpResponseRedirect('/login/')

def search(request):
    request.session.header = 'GroupWise User Search'
    form = Search()
    return render(request, 'helpdesk/search.html', {'form': form})

def searchresults(request):
    request.session.header = 'GroupWise User Search Results'
    if request.method == "POST":
        form = Search(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            gw = gwInit()
            if cd['userid'] == '*':
                gw = gwInit()
                addressFormats = gw.addrFormats()
                polist = gw.getPolist()
                userlist = gw.pageUsers(0)
                firstset = False
                for user in userlist['userList']:
                    ldap = checkLdap(user['postOfficeName'], polist)
                    if ldap == True:
                        user['ldap'] = True
                if int(userlist['nextId']) > 1:
                    firstset = True
                    return render(request, 'helpdesk/userlist.html',
                                  {'users': userlist['userList'], 'nextid': userlist['nextId'], 'firstset': firstset})
                else:
                    return render(request, 'helpdesk/userlist.html',
                                  {'users': userlist['userList'], 'firstset': firstset})

            users = gw.userSearch(cd['userid'])
            request.session['searchid'] = cd['userid']
            log(request,'Perform search on %s' %request.session['searchid'])
            if int(len(users)) == int(0):
                messages.add_message(request, messages.WARNING,
                                     "No users matching: %s  found.  Try searching again." % cd['userid'])
            else:
                return render(request, 'helpdesk/searchresults.html', {'users': users, 'searchstring': cd['userid']})
        else:
            form = Search()
        return render(request, 'helpdesk/search.html', {'form': form})

def updatedata(formdata, uid, allowed):
    addressFormats = ['HOST','USER','FIRST_LAST','LAST_FIRST','FLAST']
    gwkeys= [
        'givenName',
        'surname',
        'middleInitial',
        'suffix',
        'title',
        'company',
        'department',
        'location',
        'description',
        'telephoneNumber',
        'mobilePhoneNumber',
        'homePhoneNumber',
        'otherPhoneNumber',
        'faxNumber',
        'pagerNumber',
        'streetAddress',
        'postOfficeBox',
        'city',
        'stateProvince',
        'postalZipCode',
        'visibility',
        'loginDisabled',
        'forceInactive',
        #u'internetDomainName',
        #u'allowedAddressFormats',
        #u'preferredAddressFormat',

    ]

    gw = gwInit()
    user = gw.getObject(uid)
    userAllowedValues = user['allowedAddressFormats']['value']

    changedData = {}
    for key in gwkeys:
        changedData[key] = formdata[key]
    allowedAddressFormats = {}
    internetDomainName = {}
    preferredAddressFormat = {}
    values = []

    if formdata['allowedOverride'] == True:
        allowedAddressFormats['inherited'] = False
        for format in addressFormats:
            if formdata[format] == True:
                values.append(format)

    else:
        allowedAddressFormats['inherited' ] = True
        values = userAllowedValues

    if formdata['preferredAddressFormatInherited'] == True:
        preferredAddressFormat['inherited'] = False
        if formdata['preferredAddressFormatValue'] not in allowed:
            allowedAddressFormats['inherited'] = False
            values.append(formdata['preferredAddressFormatValue'])
        else:
            allowedAddressFormats['inherited'] = False
            allowedAddressFormats['value'] = values

        preferredAddressFormat['value'] = formdata['preferredAddressFormatValue']
        if formdata['preferredEmailId'] == '':
            formdata.pop('preferredEmailId')
        else:
            changedData['preferredEmailId'] = formdata['preferredEmailId']

    elif formdata['preferredAddressFormatInherited'] == False:
        preferredAddressFormat['inherited'] = True
        changedData['preferredEmailId'] = ""
        if 'preferredAddressFormat' in user.keys():
            preferredAddressFormat['value'] = user['preferredAddressFormat']['value']

    allowedAddressFormats['value'] = values
    changedData['preferredAddressFormat'] = preferredAddressFormat
    changedData['allowedAddressFormats'] = allowedAddressFormats
    changedData['preferredAddressFormat'] = preferredAddressFormat

    if formdata['internetDomainNameOverride'] == True:
        internetDomainName['inherited'] = False
        internetDomainName['value'] = formdata['iDomainValue']
    elif formdata['internetDomainNameOverride'] == False:

        internetDomainName['inherited'] = True
        if 'internetDomainName' in user.keys():
            internetDomainName['value'] = user['internetDomainName']['value']

    internetDomainName['exclusive'] = formdata['iDomainExclusive']
    changedData['internetDomainName'] = internetDomainName

    return changedData

def userdata(request):
    gw = gwInit()
    idoms = gw.iDomains()
    idomChoices = []
    for idom in idoms:
        choice = (idom, idom)
        idomChoices.append(choice)

    groups = gw.getGroups()
    addressFormats = gw.addrFormats()
    if request.method == "POST":
        if 'edit' in request.POST:
            if 'id' in request.session.keys():
                del request.session['id']
            form = SearchResults(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                gwid = cd['id']
                request.session['id'] = cd['id']
                request.session['name'] = cd['name']
                userData = gw.getObject(gwid)
                emailAddrs = gw.userAddresses(userData['@url'])
                ldap = gw.checkPoLdap(userData['postOfficeName'])
                if (ldap == 1) and 'ldapDn' in userData.keys():
                    userData['ldap'] = 'true'
                else:
                    userData['ldap'] = 'false'
                form = UserDetails()
                return render(request, 'helpdesk/userdata.html',
                              {'form': form, 'user': userData, 'addressFormats': addressFormats,
                               'emailAddrs': emailAddrs, 'idomains': idomChoices})

        elif 'delete' in request.POST:

            request.session.header = "GroupWise User deleted"
            form = SearchResults(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                id = cd['id']
                request.session['id'] = id
                deluser = gw.delUser(id)
                if deluser != 0:
                    messages.add_message(request, messages.WARNING, "Delete Pending for %s" % id)
                else:
                    messages.add_message(request, messages.INFO, "User: %s deleted" % id)

                parts = id.split('.')
                log(request, 'GroupWise User %s deleted '% parts[3])
                return render(request, 'helpdesk/deluser.html')

        elif 'changepwd' in request.POST:
            request.session.header = 'Change GroupWise Password for %s' % request.POST['name']
            form = SearchResults(request.POST)
            if form.is_valid():
                if 'id' in request.session.keys():
                    del request.session['id']
                    request.session['name'] = request.POST['name']
                cd = form.cleaned_data
                id = cd['id']
                name = cd['name']
                request.session['id'] = id
                request.session['name'] = name
                pwdform = changePassword(request.POST)
                return render(request, 'helpdesk/changepassword.html', {'form': pwdform, 'name': name, 'id': id})

        elif 'update' in request.POST:
            uid = request.session['id']
            form = UserDetails(request.POST)
            if form.is_valid():
                userstuff = form.cleaned_data
                allowed = gw.userFormats(uid)
                userDict = updatedata(userstuff, uid, allowed)
                log(request, 'Updated GroupWise settings for user: %s' % request.POST['name'])
                newData = gw.updateUser(uid, userDict)
                emailAddrs = gw.userAddresses(newData['@url'])
                ldap = gw.checkPoLdap(newData['postOfficeName'])
                if (ldap == 1) and 'ldapDn' in newData.keys():
                    newData['ldap'] = 'true'
                else:
                    newData['ldap'] = 'false'
                form = UserDetails()
                return render(request, 'helpdesk/userdata.html',
                              {'form': form, 'user': newData, 'addressFormats': addressFormats,
                               'emailAddrs': emailAddrs,'idomains': idomChoices})
    else:
        form = u
    return render(request, 'helpdesk/userdata.html')

def userlist(request):
    request.session.header = 'GroupWise Users'
    gw = gwInit()
    addressFormats = gw.addrFormats()
    polist = gw.getPolist()
    usercount = gw.getUserCount()

    if request.method == "POST":
        if 'next' in request.POST:
            nextId = request.POST['nextid']
            userlist = gw.pageUsers(nextId)
            for user in userlist['userList']:

                ldap = checkLdap(user['postOfficeName'], polist)
                if ldap == True:
                    user['ldap'] = True
            if int(userlist['nextId']) > 1:
                firstset = False
                return render(request, 'helpdesk/userlist.html',
                              {'users': userlist['userList'], 'nextid': userlist['nextId'], 'firstset': firstset, 'usercount': usercount})
            else:
                firstset = True
                return render(request, 'helpdesk/userlist.html', {'users': userlist['userList'], 'firstset': firstset, 'usercount': usercount})
        elif 'userform' in request.POST:
            gw = gwInit()
            addressFormats = gw.addrFormats()
            id = request.POST['id']
            request.session['name'] = request.POST['name']
            request.session['id'] = id
            userData = gw.getObject(id)
            emailAddrs = gw.userAddresses(userData['@url'])
            ldap = gw.checkPoLdap(userData['postOfficeName'])

            if (ldap == 1) and 'ldapDn' in userData.keys():
                userData['ldap'] = 'true'
            else:
                userData['ldap'] = 'false'
            form = UserDetails()

            return render(request, 'helpdesk/userdata.html',
                          {'form': form, 'user': userData, 'addressFormats': addressFormats,
                           'emailAddrs': emailAddrs})
    else:
        userlist = gw.pageUsers(0)
        firstset = False
        for user in userlist['userList']:
            ldap = checkLdap(user['postOfficeName'], polist)
            if ldap == True:
                user['ldap'] = True
        if int(userlist['nextId']) > 1:
            firstset = True
            return render(request, 'helpdesk/userlist.html',
                          {'users': userlist['userList'], 'nextid': userlist['nextId'], 'firstset': firstset, 'usercount': usercount})
        else:
            return render(request, 'helpdesk/userlist.html', {'users': userlist['userList'], 'firstset': firstset, 'usercount': usercount})

def viewlog(request):
    request.session.header = 'Log File'
    with open(logfile, 'r') as f:
        log = f.read()
    return render(request, 'helpdesk/viewlog.html', {'log': log})