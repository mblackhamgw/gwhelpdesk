import requests, json, time
from requests import ConnectionError
requests.packages.urllib3.disable_warnings()
from gwhelp import settings

class gw:
    def __init__(self, gwHost, gwPort, gwAdmin, gwPass):
        self.session = requests.Session()
        self.session.auth = (gwAdmin, gwPass)
        self.session.verify = False
        self.session.headers = {
            'Content-Type':'application/json',
            'Accept':'application/json'
        }

        self.baseUrl = 'https://%s:%s' % (gwHost, gwPort)
        self.gwAdmin = gwAdmin

    def checkResponse(self, response):
        if response.text:
            dict = json.loads(response.text)
            if 'object' in dict.keys():
                objects = dict['object']
                return objects
            else:
                return dict
        else:
            return None

    def whoami(self):
        url = '%s/gwadmin-service/system/whoami' % self.baseUrl
        try:
            response = self.session.get(url, timeout=10)
        except:
            return 1
        if response.text:
            dict = json.loads(response.text)
            return dict
        else:
            return response

    def pageUsers(self, nextId):
        retvalue = {}
        self.userList = []
        if nextId > 1:
            url = '%s/gwadmin-service/list/user?count=8&nextID=%s' % (self.baseUrl, nextId)
        else:
            url = '%s/gwadmin-service/list/user?count=8' % (self.baseUrl)
        nextId = self.getUsers(url)
        if nextId != 1:
            retvalue['nextId'] = nextId
        else:
            retvalue['nextId'] = 1
        retvalue['userList'] = self.userList

        return retvalue

    def allUsers(self):
        self.userList = []
        url = '%s/gwadmin-service/list/user?count=1000' % self.baseUrl
        nextId = self.getUsers(url)

        while nextId != 1:

            nextUrl = '%s&nextId=%s' % (url, nextId)
            nextId = self.getUsers(nextUrl)
        return self.userList

    def pageGroups(self, nextId):
        retvalue = {}
        self.groupList = []
        if nextId > 1:
            url = '%s/gwadmin-service/list/group?count=8&nextID=%s' % (self.baseUrl, nextId)
        else:
            url = '%s/gwadmin-service/list/group?count=8' % (self.baseUrl)
        nextId = self.getGroupList(url)
        if nextId != 1:
            retvalue['nextId'] = nextId
        else:
            retvalue['nextId'] = 1

        retvalue['groupList'] = self.groupList

        return retvalue

    def getGroups(self):
        glist = []
        url = '%s/gwadmin-service/list/group' % self.baseUrl
        try:
            response = self.session.get(url)
            g = self.checkResponse(response)
            for grp in g:
                data = [grp['name'], grp['id']]
                glist.append(data)

            return glist
        except:
            pass

    def addUserToGroups(self, groups, userid):
        user = self.getObject(userid)
        url = '%s%s/groupmemberships' % (self.baseUrl, user['@url'])

        for group in groups:
            data = {'add': {'id': group}}
            results = self.session.put(url, data=json.dumps(data))

    def getUserCount(self):
        url = '%s/gwadmin-service/system/info' % self.baseUrl
        response = self.session.get(url)
        info = self.checkResponse(response)
        #
        if info:
            total = info['userCount'] + info['externalUserCount']
            return total

    def getUsers(self, url):
        #self.session.auth = (self.gwAdmin, self.gwPass)
        response = self.session.get(url)

        if response.text:
            sj = json.loads(response.text)
            if 'object' in sj.keys():
                for user in sj['object']:
                    self.userList.append(user)

            if 'resultInfo' in sj.keys():
                if 'nextId' in sj['resultInfo']:
                    nextId = sj['resultInfo']['nextId']
                    return nextId
            else:
                return 1

    def userSearch(self, userid):
        url = '%s/gwadmin-service/system/search?text=%s' % (self.baseUrl, userid)
        response = self.session.get(url)
        gwusers = []
        if response.text:
            dict = json.loads(response.text)
            if dict['resultInfo']['outOf'] == 0:
                return gwusers
            elif 'object' in dict.keys():
                objects = dict['object']
            else:
                return gwusers

        for obj in objects:
            userUrl = "%s%s" % (self.baseUrl, obj['@url'])
            resp = self.session.get(userUrl)
            user = self.checkResponse(resp)

            if 'USER' in user['id']:
                details = self.getObject(user['id'])
                details['pendingOp'] = 'false'
                if 'pendingOp' in user.keys():
                    details['pendingOp'] = 'true'
                details['ldap'] = 'false'
                ldap = self.checkPoLdap(user['postOfficeName'])
                if ldap == 1:
                    if 'ldapDn' in user.keys():
                        details['ldap'] = 'true'
                gwusers.append(details)

        return gwusers

    def getObject(self, id):
        url = '%s/gwadmin-service/object/%s' % (self.baseUrl, id)
        response = self.session.get(url, timeout=5)
        object = self.checkResponse(response)
        user = object['name']
        userurl = object['@url']
        return object

    def getObjectByUrl(self, userurl):
        response = self.session.get(userurl, timeout=5)
        object = self.checkResponse(response)
        return object

    def checkPoLdap(self, postoffice):
        url = '%s/gwadmin-service/list/post_office?name=%s' % (self.baseUrl, postoffice)
        response = self.session.get(url,timeout=5)
        podata = self.checkResponse(response)[0]
        if podata['securitySettings']:
            if 'LDAP' in podata['securitySettings']:
                return 1
            else:
                return 0

    def addrFormats(self):
        addressFormats = []
        addressFormats.append('HOST')
        addressFormats.append('USER')
        addressFormats.append('LAST_FIRST')
        addressFormats.append('FIRST_LAST')
        addressFormats.append('FLAST')
        return addressFormats

    def userFormats(self, id):
        obj = self.getObject(id)
        formats = obj['allowedAddressFormats']
        return formats

    def userAddresses(self, userurl):
        url = "%s%s/emailaddresses" % (self.baseUrl, userurl)
        response = self.session.get(url, timeout=5)
        emailAddrs = self.checkResponse(response)
        addresses = "\n".join(emailAddrs['allowed'])
        return addresses

    def updateUser(self, id, data):
        obj = self.getObject(id)
        url = '%s%s' % (self.baseUrl, obj['@url'])
        response = self.session.put(url, data=json.dumps(data) , timeout=10)
        response2 = self.session.get(url)
        newdata = self.checkResponse(response2)
        return newdata

    def iDomains(self):
        idomains = []

        url = '%s/gwadmin-service/system/internetdomains' % self.baseUrl
        try:
            response = self.session.get(url, timeout=5)
        except ConnectionError as e:
            return e
        objects = json.loads(response.text)['object']
        for idom in objects:
            idomains.append(idom['name'])
        return idomains

    def defIdom(self):
        url = '%s/gwadmin-service/system' % self.baseUrl
        response = self.session.get(url, timeout=5)
        sysdata = self.checkResponse(response)
        return sysdata['internetDomainName']

    def changePass(self, id, password):
        obj = self.getObject(id)
        url = '%s%s/clientoptions' % (self.baseUrl, obj['@url'])
        data = {"userPassword":{"value": password}}
        response = self.session.put(url, data=json.dumps(data))

    def delUser(self, id):
        obj = self.getObject(id)
        url = '%s%s' % (self.baseUrl, obj['@url'])
        response = self.session.delete(url)
        pending = 1
        for i in range(1,10):
            response2 = self.session.get(url)
            data = self.checkResponse(response2)
            if 'pendingOp' in data.keys():
                time.sleep(2)
            else:
                pending = 0
                return pending
        return pending

    def getPolist(self):
        poList = []
        url = '%s/gwadmin-service/list/post_office' % self.baseUrl
        response = self.session.get(url, timeout=5)
        objects = self.checkResponse(response)

        for object in objects:
            podict = {}
            podict['name'] = object['name']
            podict['url'] = object['@url']
            if 'LDAP' in object['securitySettings']:
                podict['ldap'] = True
            else:
                podict['ldap'] = False
            if 'externalRecord' in object.keys():
                podict['external'] = True
            else:
                podict['external'] = False
            poList.append(podict)

        return poList


    #def getPoIds(self, polist):



    def addUser(self, pourl, data):
        url = '%s%s/users' % (self.baseUrl, pourl)
        name = data['name']
        response = self.session.post(url, data=json.dumps(data), timeout=5)
        if response.text:
            return json.loads(response.text)
        else:
            return response.headers

    def dissociate(self, id):
        user = self.getObject(id)
        userurl = user['@url']
        url = '%s%s/directorylink' % (self.baseUrl, userurl)
        dis = self.session.delete(url)
        return dis.text

    def userInfo(self,id):
        url = '%s/gwadmin-service/object/%s' % (self.baseUrl, id)
        response = self.session.get(url, timeout=5)
        object = self.checkResponse(response)
        newurl = '%s%s/info' % (self.baseUrl,object['@url'])
        resp = self.session.get(newurl)
        if resp.text:
            doc = json.loads(resp.text)

        return doc

    def userGroupMembership(self, id):
        membership = []
        url = '%s/gwadmin-service/object/%s' % (self.baseUrl, id)
        response = self.session.get(url, timeout=5)
        object = self.checkResponse(response)
        newurl = '%s%s/groupmemberships' % (self.baseUrl, object['@url'])
        response = self.session.get(newurl)

        if response.text:
            dict = json.loads(response.text)
            if 'object' in dict.keys():
                objects = dict['object']
                for grp in objects:
                    data = []
                    data.append(grp['name'])
                    data.append(grp['participation'])
                    data.append(grp['id'])
                    membership.append(data)

                return membership

            elif 'resultInfo' in dict.keys():
                return None

    def updateGroupMembership(self, userid, groupid, particpation ):
        user = self.getObject(userid)
        url = '%s%s/groupmemberships' %(self.baseUrl, user['@url'])
        data = {'update':{
                    'id':groupid,
                    'participation': particpation
                    }
                }
        results = self.session.put(url,data=json.dumps(data))

    def removeFromGroup(self, userid, grpid):
        user = self.getObject(userid)
        url = '%s%s/groupmemberships/%s' % (self.baseUrl, user['@url'], grpid)
        results = self.session.delete(url)


    def renameUser(self, id, newid):
        user = self.getObject(id)
        pourl = '%s%s/rename' % (self.baseUrl, user['links'][1]['@href'])
        print pourl
        data = {'objectId': id,
                'newObjectId': newid,
                'createNickname':'false'
                }
        response = self.session.post(pourl,data=json.dumps(data))

    def moveUser(self, userid, poid):
        url = '%s/gwadmin-service/system/moverequests' % self.baseUrl
        data = {
              "sources" : [ {
                "id" : userid
              } ],
              "postOfficeId" : poid,
              "directoryUser" : 'false'
            }

        response = self.session.post(url, data=json.dumps(data))
        statusurl = '%s?name=%s' % (url, userid.split('.')[3])
        status = self.session.get(statusurl)
        if status.text:
            dict = json.loads(status.text)
            if 'succeeded' in dict.keys():
                return 'Succeeded'
            else:
                if 'lastAction' in dict.keys():
                    lastaction = dict['object']['moveStatus']['lastAction']
                    return lastaction
