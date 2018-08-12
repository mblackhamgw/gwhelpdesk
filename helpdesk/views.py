from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponseRedirect, render_to_response, reverse
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
    admins = Admin.objects.all()
    if request.method == "POST":
        form = AdminForm(request.POST)
        #print form.errors
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
        admins = Admin.objects.all()
        return render(request, 'helpdesk/admins.html', {'form': form, 'admins': admins})
    else:
        form = AdminForm()
        admins = Admin.objects.all()
    return render(request, 'helpdesk/admins.html', {'form': form, 'admins': admins})

def addgroup(request):
    gw = gwInit()
    polist = gw.getPolist()
    if request.method == "POST":
        form = AddGroup(request.POST)
        name = request.POST['name']
        postOfficeName = request.POST['postOfficeName']
        visibility = request.POST['visibility']
        data = {
            'name': name,
            'postOfficeName' : postOfficeName,
            'visibility': visibility
        }
        addgrp = gw.addGroup(data)
        if addgrp == 201:
            allgroups = gw.getGroups()
            for group in allgroups:
                group['url'] = group['@url']
            count = len(allgroups)
            form = GroupList()
            return render(request, 'helpdesk/grouplist.html', {'form': form, 'groups': allgroups, 'count': count})

        return render(request, 'helpdesk/addgroup.html', {'form': form, 'polist': polist})
    else:
        groupnumber = gw.objectCount('group')
        if groupnumber != 0:
            allgroups = gw.getGroups()
            for group in allgroups:
                group['url'] = group['@url']
            count = len(allgroups)
            form = AddGroup()
            return render(request, 'helpdesk/addgroup.html', {'form': form, 'polist': polist })

        else:
            form = AddGroup()
            return render(request, 'helpdesk/addgroup.html', {'form': form, 'polist': polist})


def addgrpmember(request):
    gw = gwInit()
    addressFormats = gw.addrFormats()
    polist = gw.getPolist()
    usercount = gw.getUserCount()
    if request.method == "POST":
        if 'next' in request.POST:
            nextId = request.POST['nextid']
            userlist = gw.pageUsers(nextId)
            if int(userlist['nextId']) > 1:
                firstset = False
                return render(request, 'helpdesk/addgrpmember.html',
                              {'users': userlist['userList'], 'nextid': userlist['nextId'], 'firstset': firstset,
                               'usercount': usercount})
            else:
                firstset = True
                return render(request, 'helpdesk/addgrpmember.html',
                              {'users': userlist['userList'], 'firstset': firstset, 'usercount': usercount})

        elif 'add' in request.POST:
            userid = request.POST['id']
            username = request.POST['name']
            grpid = request.POST['grpid']
            grpname = request.POST['grpname']
            url = request.POST['url']

            data = {
                'id': userid,
                'url': url,
            }
            addtogrp = gw.addUserToGroup(data)
            if addtogrp == 201:
                log(request, 'Added %s to Group %s' % (username, grpname))
                return HttpResponseRedirect(reverse('grouplist'))
            else:
                members = gw.getGroupMembers(url)
                form = GroupDetails()
                groupdata = gw.getGroup(id)
                emailAddrs = gw.userAddresses(url)
                idoms = gw.iDomains()
                idomChoices = []
                for idom in idoms:
                    choice = (idom, idom)
                    idomChoices.append(choice)
                addressFormats = gw.addrFormats()
                return render(request, 'helpdesk/groupdetails.html',
                              {'form': form, 'group': groupdata, 'members': members,
                               'addressFormats': addressFormats,
                               'emailAddrs': emailAddrs, 'idomains': idomChoices})

        elif 'userform' in request.POST:
            gw = gwInit()

    else:
        userlist = gw.pageUsers(0)
        #print userlist['nextId']
        if userlist['nextId'] == None:
            firstset = False
            return render(request, 'helpdesk/addgrpmember.html',
                          {'users': userlist['userList'], 'nextid': userlist['nextId'], 'firstset': firstset,
                           'usercount': usercount})


        if int(userlist['nextId']) > 1:
            firstset = True
            return render(request, 'helpdesk/addgrpmember.html',
                          {'users': userlist['userList'], 'nextid': userlist['nextId'], 'firstset': firstset,
                           'usercount': usercount})
        else:
            return render(request, 'helpdesk/addgrpmember.html',
                          {'users': userlist['userList'], 'firstset': firstset, 'usercount': usercount})

    return render(request, 'helpdesk/addgrpmember.html')

def addnickname(request):
    gw = gwInit()
    polist = gw.getPolist()
    if request.method == "POST":
        form = Nicknames(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            form = Nicknames(request.POST)
            data ={}
            poname = request.POST['postOfficeName']
            nickpo = poname.split('.')[2]
            nickdom = poname.split('.')[1]
            referreduser = request.POST['referreduser']
            userpo = referreduser.split('.')[2]
            userdom = referreduser.split('.')[1]
            username = referreduser.split('.')[3]
            data['name'] = cd['nickname']
            data['domainName'] = nickdom
            data['postOfficeName'] = nickpo
            data['visibility'] = cd['visibility']
            data['givenName'] = cd['givenName']
            data['surname'] = cd['surname']
            data['referredUserName'] = referreduser
            data['userName'] = username
            data['userPostOfficeName'] = userpo
            data['userDomainName'] = userdom
            newnick = gw.addNickname(**data)
            if newnick == 0:
                log(request, "Added nickname of %s for %s" % (cd['nickname'], username))
                id = request.session['id']
                nicknamelist = gw.nicknames(id)
                id = request.session['id']
                return render(request, 'helpdesk/nicknames.html', {'nicknames': nicknamelist})
            return render(request, 'helpdesk/addnickname.html', {'form':form, 'polist': polist})
    form = Nicknames()
    return render(request, 'helpdesk/addnickname.html', {'form':form,  'polist': polist})

def addresource(request):
    gw= gwInit()
    polist = gw.getPolist()
    if request.method == "POST":
        form = Addresource(request.POST)
        ownerid = request.POST['ownerid']
        po = ownerid.split('.')[2]
        dom = ownerid.split('.')[1]
        newresource = gw.addResource(request.POST['resourcename'], po, dom, request.session['name'] )
        if newresource == 0:
            log(request, "Added resource  %s for %s" % (request.POST['resourcename'], request.session['name']))
        id = request.session['id']
        resourcelist = gw.resources(id)
        id = request.session['id']
        return render(request, 'helpdesk/resources.html', {'form':form, 'resources': resourcelist, 'polist': polist})
    form = Addresource()
    return render(request, 'helpdesk/addresource.html', {'form': form, 'polist': polist})


def addtogroups(request):
    gw = gwInit()
    groups = gw.getAllGroups()
#    print groups

    if len(groups) == 0:

        messages.add_message(request, messages.WARNING,
                             "No groups GroupWise groups defined")
        return render(request, 'helpdesk/addtogroups.html')
    if request.POST:
        # print request.POST
        grpurl = request.POST['url']
        userid = request.session['id']

        data = {
            'id': userid,
            'url': grpurl,
        }
        addtogrp = gw.addUserToGroup(data)
        if addtogrp == 201:
            return HttpResponseRedirect(reverse('grouplist'))
        else:
            members = gw.getGroupMembers(grpurl)
            form = GroupDetails()
            groupdata = gw.getGroup(id)
            emailAddrs = gw.userAddresses(grpurl)
            idoms = gw.iDomains()
            idomChoices = []
            for idom in idoms:
                choice = (idom, idom)
                idomChoices.append(choice)
            addressFormats = gw.addrFormats()
            return render(request, 'helpdesk/groupdetails.html',
                          {'form': form, 'group': groupdata, 'members': members,
                           'addressFormats': addressFormats,
                           'emailAddrs': emailAddrs, 'idomains': idomChoices})

    else:
        return render(request, 'helpdesk/addtogroups.html', {'groups': groups})



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

def grouplist(request):
    gw = gwInit()
    grpcount = gw.objectCount('group')
    if grpcount != 0:
        grouplist = gw.pageGroups(0)
        polist = gw.getPolist()
        groupcount = gw.getGroupCount()
        if request.method == "POST":
            if 'next' in request.POST:
                nextId = request.POST['nextid']

                grouplist = gw.pageGroups(nextId)
                for grp in grouplist['groupList']:
                    ldap = checkLdap(grp['postOfficeName'], polist)
                    if ldap == True:
                        grp['ldap'] = True
                if int(grouplist['nextId']) > 1:
                    firstset = False
                    return render(request, 'helpdesk/grouplist.html',
                                  {'groups': grouplist['groupList'], 'nextid': grouplist['nextId'], 'firstset': firstset, 'count': groupcount})
                else:
                    firstset = True
                    return render(request, 'helpdesk/grouplist.html',
                                  {'groups': grouplist['groupList'],  'nextid': grouplist['nextId'], 'firstset': firstset, 'count': groupcount})
        else:
            firstset = True
            return render(request, 'helpdesk/grouplist.html',
                          {'groups': grouplist['groupList'],  'nextid': grouplist['nextId'],'firstset': firstset, 'count': groupcount})

    else:
        messages.add_message(request, messages.WARNING,
                             "No groups GroupWise groups defined")
        return render(request, 'helpdesk/grouplist.html')

def groupdetails(request):
    gw = gwInit()
    idoms = gw.iDomains()
    idomChoices = []
    for idom in idoms:
        choice = (idom, idom)
        idomChoices.append(choice)
    addressFormats = gw.addrFormats()
    if request.method == "POST":
        form = GroupList(request.POST)
        id = request.POST['id']
        name = request.POST['name']
        groupdata = gw.getGroup(id)
        if 'url' in request.POST:
            url = request.POST['url']
        else:
            url = groupdata['@url']
        request.session['id'] = id
        request.session['name'] = name
        request.session['url'] = url
        if 'general' in request.POST:
            description = request.POST['description']
            visibility = request.POST['visibility']
            data = {
                'description': description,
                'visibility' : visibility,
            }
            type = 'u'
            update = gw.updateGroup(id, data, type)
            if update == int(200):
                log(request, 'Modified group %s' % name)
                groupdata = gw.getGroup(id)
                groupUrl = groupdata['@url']
                emailAddrs = gw.userAddresses(groupdata['@url'])
                members = gw.getGroupMembers(groupUrl)


                if members != 0:
                    for member in members:
                        member['stripid'] = member['id'].split('.', 1)[1]

                    for member in members:
                        member['id'] = member['id'].split('.', 1)[1]
                form = GroupDetails()
                return render(request, 'helpdesk/groupdetails.html',
                              {'form': form, 'group': groupdata, 'members': members, 'addressFormats': addressFormats,
                               'emailAddrs': emailAddrs,'idomains': idomChoices})

        elif 'membership' in request.POST:
            member = request.POST['memberid']
            if 'USER' not in member:
                memberid = 'USER.' + request.POST['memberid']
            else:
                memberid = request.POST['memberid']
            participation = request.POST['participation']
            data = {
                'id': memberid,
                'participation': participation
            }
            type = 'm'
            update = gw.updateGroup(id, data, type)
            if update == 200:
                groupdata = gw.getGroup(id)
                groupUrl  = groupdata['@url']
                emailAddrs = gw.userAddresses(groupdata['@url'])
                members = gw.getGroupMembers(groupUrl)
                for member in members:
                    member['stripid'] = member['id'].split('.', 1)[1]
                if members != 0:
                    for member in members:
                        member['stripid'] = member['id'].split('.', 1)[1]
                form = GroupDetails()
                return render(request, 'helpdesk/groupdetails.html',
                              {'form': form, 'group': groupdata, 'members': members, 'addressFormats': addressFormats,
                               'emailAddrs': emailAddrs,'idomains': idomChoices})

        elif 'inetaddressing' in request.POST:
            uid = request.POST['id']
            form = GroupInet(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                new = groupupdatedata(cd, uid, addressFormats)
                type = 'u'
                grpupdate = gw.updateGroup(uid, new, type)
                groupdata = gw.getGroup(uid)
                groupUrl = groupdata['@url']
                emailAddrs = gw.userAddresses(groupdata['@url'])
                members = gw.getGroupMembers(groupUrl)
                if members != 0:
                    for member in members:
                        member['id'] = member['id'].split('.', 1)[1]
                        member['stripid'] = member['id'].split('.', 1)[1]
                form = GroupDetails()
                return render(request, 'helpdesk/groupdetails.html',
                              {'form': form, 'group': groupdata, 'members': members,
                               'addressFormats': addressFormats,
                               'emailAddrs': emailAddrs, 'idomains': idomChoices})
        elif 'editgroup' in request.POST:
            form = GroupList(request.POST)
            id = request.POST['id']
            name = request.POST['name']
            request.session['id'] = id
            request.session['name'] = name
            groupdata = gw.getGroup(id)
            groupUrl = url
            idoms = gw.iDomains()
            idomChoices = []
            for idom in idoms:
                choice = (idom, idom)
                idomChoices.append(choice)
            addressFormats = gw.addrFormats()
            emailAddrs = gw.userAddresses(groupdata['@url'])
            members = gw.getGroupMembers(groupUrl)
            if members == 0:
                form = GroupDetails()
                return render(request, 'helpdesk/groupdetails.html', {'form': form, 'group': groupdata, 'members': members,
                                        'addressFormats': addressFormats,
                                        'emailAddrs': emailAddrs,'idomains': idomChoices} )
            if members != None or members != 0:
                for member in members:
                    member['stripid'] = member['id'].split('.',1)[1]
                form = GroupDetails()
                return render(request, 'helpdesk/groupdetails.html', {'form': form, 'group': groupdata, 'members': members,
                                        'addressFormats': addressFormats,
                                        'emailAddrs': emailAddrs,'idomains': idomChoices} )
            else:
                form = GroupDetails()
                return render(request, 'helpdesk/groupdetails.html', {'form': form, 'group': groupdata, 'members': members,
                                        'addressFormats': addressFormats,
                                        'emailAddrs': emailAddrs,'idomains': idomChoices} )

        elif 'deletemember' in request.POST:
            id = request.POST['id']
            name = request.POST['name']
            request.session['id'] = id
            request.session['name'] = name
            groupdata = gw.getGroup(id)
            delmember = gw.delFromGroup(groupdata['@url'], request.POST['memberid'])
            if delmember == int(200):
                log(request, 'Removed %s from group %s' % (request.POST['memberid'], name))
            idoms = gw.iDomains()
            idomChoices = []
            for idom in idoms:
                choice = (idom, idom)
                idomChoices.append(choice)
            addressFormats = gw.addrFormats()
            emailAddrs = gw.userAddresses(groupdata['@url'])
            members = gw.getGroupMembers(groupdata['@url'])
            if members != 0:
                for member in members:
                    member['stripid'] = member['id'].split('.', 1)[1]
            form = GroupDetails()
            return render(request, 'helpdesk/groupdetails.html', {'form': form, 'group': groupdata, 'members': members,
                                                                  'addressFormats': addressFormats,
                                                                  'emailAddrs': emailAddrs, 'idomains': idomChoices})

        elif 'deletegroup' in request.POST:
            id = request.POST['id']
            name = request.POST['name']
            delgrp = gw.deleteGroup(id)
            if delgrp == int(0):
                log(request, 'Deleted group %s' % name)
            allgroups = gw.getGroups()
            count = len(allgroups)
            form = GroupList()
            return render(request, 'helpdesk/grouplist.html', {'form': form, 'groups': allgroups, 'count': count})
        return render(request, 'helpdesk/groupdetails.html', {'form': form})
    else:
        form = GroupDetails
        return render(request, 'helpdesk/groupdetails.html', {'form': form})

def groupsearch(request):
    request.session.header = 'GroupWise Group Search'
    form = GroupSearch()
    return render(request, 'helpdesk/groupsearch.html', {'form': form})

def groupsearchresults(request):
    gw = gwInit()
    grouplist = []
    if request.method == "POST":
        form = GroupSearch(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            groupname = cd['groupname']
            gw = gwInit()

            if cd['groupname'] != '*':
                grps = gw.groupSearch(groupname)

                request.session['searchid'] = cd['groupname']
                log(request, 'Perform group search on %s' % request.session['searchid'])
                if int(len(grps)) == int(0):
                    messages.add_message(request, messages.WARNING,
                                         "No groups matching: %s  found.  Try searching again." % cd['groupname'])
                else:
                    return render(request, 'helpdesk/groupsearchresults.html',
                              {'groups': grps, 'searchstring': groupname})
        else:
            form = GroupSearch()
        return render(request, 'helpdesk/groupsearch.html', {'form': form})


def groupupdatedata(formdata, uid, allowed):
    addressFormats = ['HOST', 'USER', 'FIRST_LAST', 'LAST_FIRST', 'FLAST']
    gw = gwInit()
    group = gw.getGroup(uid)
    groupAllowedValues = group['allowedAddressFormats']['value']
    changedData = {}
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
        allowedAddressFormats['inherited'] = True
        values = groupAllowedValues
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
        if 'preferredAddressFormat' in group.keys():
            preferredAddressFormat['value'] = group['preferredAddressFormat']['value']

    allowedAddressFormats['value'] = values
    changedData['preferredAddressFormat'] = preferredAddressFormat
    changedData['allowedAddressFormats'] = allowedAddressFormats
    changedData['preferredAddressFormat'] = preferredAddressFormat
    if formdata['internetDomainNameOverride'] == True:
        internetDomainName['inherited'] = False
        internetDomainName['value'] = formdata['iDomainValue']
    elif formdata['internetDomainNameOverride'] == False:
        internetDomainName['inherited'] = True
        if 'internetDomainName' in group.keys():
            internetDomainName['value'] = group['internetDomainName']['value']
    internetDomainName['exclusive'] = formdata['iDomainExclusive']
    changedData['internetDomainName'] = internetDomainName

    return changedData

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
            name = request.session['name']
            grpid = cd['grpid']
            groupname = cd['group']
            participation = cd['participation']
            if 'edit' in request.POST.keys():
                x = gw.updateGroupMembership(name, userid, grpid, participation)
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
                request.session['surname'] = adminuser.last_name
                request.session['givenName'] = adminuser.first_name
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

def maintenance(request):
    if request.method == "POST":
        id = request.POST['id']
        name = request.POST['name']
        gw = gwInit()

        if 'analyzeok' in request.POST:
            gwcheckoptions = {}
            options = ['structure','contents', 'checkIndex', 'fixProblems','updateTotals','checkAttachments']
            for option in request.POST:
                if option in options:
                    gwcheckoptions[option] = request.POST[option]

            gwcheck = gw.gwcheck('ANALYZE', id, gwcheckoptions)
            if gwcheck == 0:
                log(request, "gwcheck %s task has been sent to the POA for %s" % ('Analyze/Fix', name))
                messages.add_message(request, messages.SUCCESS, "A Maintenace task has been sent to the POA")

        elif 'expireok' in request.POST:
            gwcheckoptions = {}
            options = ['expireDays', 'expireSize', 'expireTrashDays', 'expireUntil' ,'boxLimit', 'expireType', 'expireFlags', 'expireDownloadedDays']
            expireFlags = [ "INBOX", "OUTBOX", "CALENDAR", "ONLY_BACKED_UP", "ONLY_RETAINED", "LIMITED_SIZE" ]
            if 'olderthan' in request.POST and request.POST['olderthan'] == 'on':
                gwcheckoptions['expireDays'] = request.POST['expireDays']
            if 'largerthan' in request.POST and request.POST['largerthan'] == 'on':
                gwcheckoptions['expireSize'] = request.POST['expireSize']
            if 'trashdays' in request.POST and request.POST['trashdays'] == 'on':
                gwcheckoptions['expireTrashDays'] = request.POST['expireTrashDays']
            if 'downloadeddays' in request.POST and request.POST['downloadeddays'] == 'on' :
                gwcheckoptions['expireDownloadedDays'] = request.POST['expireDownloadedDays']

            flags = []
            for flag in expireFlags:
                if flag in request.POST:
                    flags.append(flag)
            gwcheckoptions['expireFlags'] = flags
            gwcheck = gw.gwcheck('EXPIRE', id, gwcheckoptions)
            if gwcheck == 0:
                log(request, "gwcheck %s task has been sent to the POA for %s" % ('Expire/Reduce', name))
                messages.add_message(request, messages.SUCCESS, "A Maintenace task has been sent to the POA")

        elif 'rebuildok' in request.POST:
            data = {
              "files" : [ "USER", "MSG" ],
              "action" : "REBUILD",
              "eventType" : "MAINTENANCE",
              "message" : "",
              "sendToCc" : "",
              "verbose" : 'true',
              "exclude" : 'null',
              "distribute" : [ "ADMIN", 'USERS' ]
            }

            gwcheck = gw.gwcheck('REBUILD', id, data)
            if gwcheck == 0:
                log(request, "gwcheck %s task has been sent to the POA for %s" % ('Structural Rebuild', name))
                messages.add_message(request, messages.SUCCESS, "A Maintenace task has been sent to the POA")
        elif 'resetok' in request.POST:
            data = {
              "files" : [ "USER" ],
              "action" : "PREFS",
              "eventtype" : "maintenance",
              "message" : "",
              "resetpassword" : "********",
              "sendtocc" : "",
              "verbose" : 'true',
              "exclude" : 'null',
              "distribute" : [ "ADMIN",'USERS' ]
            }
            gwcheck = gw.gwcheck('PREFS', id, data)
            if gwcheck == 0:
                log(request, "gwcheck %s task has been sent to the POA for %s" % ('Reset Client Options', name))
                messages.add_message(request, messages.SUCCESS, "A Maintenace task has been sent to the POA")

        form = Maintenence(request.POST)
        return render(request, 'helpdesk/maintenance.html', {'form': form})
    else:
        form = Maintenence()
        return render(request, 'helpdesk/maintenance.html', {'form':form})

def move(request):
    gw = gwInit()
    if request.method == "POST":
        form = Move(request.POST)
        print form.errors
        if form.is_valid():
            cd = form.cleaned_data
            POST, DOMAIN, PONAME = cd['postoffice'].split('.')
            USER, DOM, PO, USERID = cd['id'].split('.')
            oldpoid =  '%s.%s' % (DOM, PO)
            newpoid = '%s.%s.%s' % (POST, DOMAIN, PONAME)
            PO = cd['postoffice']
            newid = '%s.%s.%s.%s' % (USER, DOMAIN, PONAME, USERID)
            form = UserDetails()
            usermove = gw.moveUser(cd['id'], PO)
            request.session['id'] = newid
            addressFormats = gw.addrFormats()
            userData = gw.getObject(newid)
            emailAddrs = gw.userAddresses(userData['@url'])
            ldap = gw.checkPoLdap(userData['postOfficeName'])
            if (ldap == 1) and 'ldapDn' in userData.keys():
                userData['ldap'] = 'true'
            else:
                userData['ldap'] = 'false'
            log(request, '%s moved from %s to %s' % (USERID, oldpoid, '.'.join(cd['postoffice'].rsplit('.')[-2:])))
            return render(request, 'helpdesk/userdata.html',
                          {'form': form, 'user': userData, 'addressFormats': addressFormats,
                           'emailAddrs': emailAddrs})

        return render(request, 'helpdesk/move.html', {'form': form})

    else:
        form = Move()
        polist = gw.getPolist()
        for postoffice in polist:
            dom = str(postoffice['url']).split('/')[3]
            po = str(postoffice['url']).split('/')[5]
            poid = 'POST_OFFICE.%s.%s' % (dom, po)
            postoffice['id'] = poid
        return render(request, 'helpdesk/move.html', {'form': form, 'polist': polist})

def nicknames(request):
    gw = gwInit()
    id = request.session['id']
    nicknamelist = gw.nicknames(id)
    if request.POST:
        if 'delete' in request.POST:
            url = request.POST['url']
            nickname = request.POST['name']
            owner = id.split('.')[3]
            delnick = gw.delNickname(url)
            if delnick == 0:
                log(request, 'Deleted nickname %s for %s' % (nickname, owner))
                nicknamelist = gw.nicknames(id)
                return render(request, 'helpdesk/nicknames.html', {'nicknames': nicknamelist})

    return render(request, 'helpdesk/nicknames.html', {'nicknames': nicknamelist})

def rename(request):
    if request.method == "POST":
        form = Rename(request.POST)
        #print form.errors
        if form.is_valid():
            if 'id' in request.session.keys():
                del request.session['id']
            if 'name' in request.session.keys():
                del request.session['name']
            cd = form.cleaned_data
            id = cd['id']
            newname = cd['newid']
            oldname = cd['name']
            popart = id.rsplit('.',1)[0]
            newid = '%s.%s' % (popart, newname)
            gw = gwInit()
            rename = gw.renameUser(id, newname)
            request.session['id'] = newid
            request.session['name'] = newname
            addressFormats = gw.addrFormats()
            userData = gw.getObject(newid)
            emailAddrs = gw.userAddresses(userData['@url'])
            ldap = gw.checkPoLdap(userData['postOfficeName'])
            if (ldap == 1) and 'ldapDn' in userData.keys():
                userData['ldap'] = 'true'
            else:
                userData['ldap'] = 'false'
            form = UserDetails()
            log(request,'%s Renamed to %s' % (oldname, newname))
            return render(request, 'helpdesk/userdata.html',
                          {'form': form, 'user': userData, 'addressFormats': addressFormats,
                           'emailAddrs': emailAddrs})
    else:
        form = Rename()
        return render(request, 'helpdesk/rename.html', {'form': form})

def resources(request):
    gw = gwInit()
    id = request.session['id']
    resourcelist = gw.resources(id)
    id = request.session['id']
    if request.POST:
        form = Resources(request.POST)
        #print form.errors
        url = request.POST['resourceurl']
        if 'delete' in request.POST:
            delresource = gw.delResource(url)
            resourcelist = gw.resources(id)
            return render(request, 'helpdesk/resources.html', {'resources': resourcelist})
        if 'add' in request.POST:
            pourl = request.POST['resourceurl']
            parts = pourl.split('/')
            parts.pop(-1)
            sep = '/'
            u = sep.join(parts)
        return render(request, 'helpdesk/resources.html', {'resources': resourcelist})
    return render(request, 'helpdesk/resources.html', {'resources': resourcelist})

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
                request.session['poname'] = userData['postOfficeName']
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

        if 'nextId' not in userlist:
            if int(userlist['nextId']) > 1:
                firstset = True
                return render(request, 'helpdesk/userlist.html',
                              {'users': userlist['userList'], 'nextid': userlist['nextId'],
                               'firstset': firstset, 'usercount': usercount})
            else:
                return render(request, 'helpdesk/userlist.html', {'users': userlist['userList'],
                                                                  'firstset': firstset, 'usercount': usercount})

        else:
            return render(request, 'helpdesk/userlist.html', {'users': userlist['userList'],
                                            'firstset': firstset, 'usercount': usercount})

def viewlog(request):
    request.session.header = 'Log File'
    with open(logfile, 'r') as f:
        log = f.read()
    return render(request, 'helpdesk/viewlog.html', {'log': log})
