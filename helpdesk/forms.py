
from django.forms import ModelForm, Form
from .models import GWSettings,  Admin
from helpdesk.lib import gwlib

from django import forms

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


class AddUser(forms.Form):
    try:
        gw = gwInit()
        pos = gw.getPolist()
        pochoices = []
        for po  in pos:
            choice = (po['name'],po['name'])
            pochoices.append(choice)

        name = forms.CharField(max_length=64)
        postOfficeName = forms.ChoiceField(choices=pochoices,required=True)
        givenName = forms.CharField(max_length=64, required=False)
        surname = forms.CharField(max_length=64, required=False)

        password = forms.CharField(max_length=64, required=False)
        password2 = forms.CharField(max_length=64, required=False)

        def clean(self):
            data = self.cleaned_data
            if "password" in data and "password2" in data:
                if data['password'] != data['password2']:
                    password2 = data['password2']
                    #self.errors['No Match'] = self.error_class(['Passwords do not match'])
                    self.add_error('password2','Passwords do not match')
    except:
        print 'init failed'

class AdminForm(ModelForm):
    class Meta:
        model = Admin
        fields = '__all__'

    def clean(self):
        data = self.cleaned_data
        if "password" in data and "password2" in data:
            if data['password'] != data['password2']:
                password2 = data['password2']
                #self.errors['No Match'] = self.error_class(['Passwords do not match'])
                self.add_error('password2','Passwords do not match')

        return data

class changePassword(Form):
    #userid = forms.CharField(max_length=64)
    password = forms.CharField(max_length=64, required=True)
    password2 = forms.CharField(max_length=64, required=True)
    id = forms.CharField(max_length=128)
    name = forms.CharField(max_length=64)

class GWConfig(ModelForm):
    class Meta:
        model = GWSettings
        fields = '__all__'





class Groups(forms.Form):
    gw = gwInit()
    grps = gw.getGroups2()
    choices = []
    for g in grps:
        #print g
        choice = (g[1], g[0])
        choices.append(choice)
    #print choices
    #groups = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,label="",choices=choices, required=False)
    #groups = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,label="",choices=choices, required=False)

    groups = forms.ChoiceField(choices=choices, widget=forms.SelectMultiple, required=False)
    participation = forms.CharField(max_length=64, required=False)
    #groups = forms.ChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple)
#    groups = forms.ChoiceField()
    #groups = forms.SelectMultiple()



class LoginForm(Form):
    username = forms.CharField(max_length=128)
    password = forms.CharField(max_length=128)

class Search(forms.Form):
    userid = forms.CharField(max_length=64)

class SearchResults(forms.Form):
    id = forms.CharField(max_length=128)
    name = forms.CharField(max_length=64)

class UserDetails(forms.Form):
    gw = gwInit()

    try:
        idoms = gw.iDomains()
        idomChoices = []
        for idom in idoms:
            choice = (idom, idom)
            idomChoices.append(choice)
    except:
        idomChoices = []

    visChoices = [
        ('SYSTEM', 'System'),
        ('DOMAIN', 'Domain'),
        ('POST_OFFICE','Post Office'),
        ('NONE', 'None')
    ]
    addrFormats = [
        ('HOST', 'Username.PostOffice@InternetDomain'),
        ('USER', ' Username@InternetDomain'),
        ('FIRST_LAST', 'First.Last@InternetDomain'),
        ('LAST_FIRST','Last.First@InternetDomain'),
        ('FLAST', 'FirstInitialLastName@InternetDomain')
    ]

    name = forms.CharField(max_length=64)
    givenName = forms.CharField(max_length=64, required=False)
    surname = forms.CharField(max_length=64, required=False)
    middleInitial = forms.CharField(max_length=12, required=False)
    suffix = forms.CharField(max_length=64, required=False)
    title = forms.CharField(max_length=64, required=False)
    company = forms.CharField(max_length=61, required=False)
    department = forms.CharField(max_length=64, required=False)
    fileId = forms.CharField(max_length=3, required=False)
    description = forms.CharField(max_length=256, required=False)
    telephoneNumber = forms.CharField(max_length=24, required=False)
    mobilePhoneNumber = forms.CharField(max_length=24, required=False)
    homePhoneNumber = forms.CharField(max_length=24, required=False)
    otherPhoneNumber = forms.CharField(max_length=24, required=False)
    faxNumber = forms.CharField(max_length=24, required=False)
    pagerNumber = forms.CharField(max_length=24, required=False)
    streetAddress = forms.CharField(max_length=128, required=False)
    postOfficeBox = forms.CharField(max_length=24, required=False)
    city = forms.CharField(max_length=64, required=False)
    stateProvince = forms.CharField(max_length=64, required=False)
    postalZipCode = forms.CharField(max_length=16, required=False)
    visibility = forms.ChoiceField(choices=visChoices)
    location = forms.CharField(max_length=64, required=False)
    loginDisabled = forms.BooleanField(required=False)
    forceInactive = forms.BooleanField(required=False)
    allowedOverride = forms.BooleanField(required=False)
    HOST = forms.BooleanField(required=False)
    USER = forms.BooleanField(required=False)
    FIRST_LAST = forms.BooleanField(required=False)
    LAST_FIRST = forms.BooleanField(required=False)
    FLAST = forms.BooleanField(required=False)
    preferredAddressFormatValue = forms.ChoiceField(choices=addrFormats, required=False)
    preferredAddressFormatInherited = forms.BooleanField(required=False)
    preferredEmailId = forms.CharField(max_length=128, required=False)
    internetDomainNameOverride = forms.BooleanField(required=False)
    iDomainValue = forms.ChoiceField(choices=idomChoices, required=False)

    iDomainExclusive = forms.BooleanField(required=False)

    #groups = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,label="Add user to following Groups")

class UserGroups(forms.Form):
    #gw = gwInit()
    #grps = gw.getGroups()
    #choices = []
    #pchoices = [
    #    ('PRIMARY', 'PRIMARY'),
    #    ('CC', 'CARBON_COPY'),
    #    ['BC', 'BLIND_COPY']
    #]
    #for g in grps:
    #    choice = (g, g)
    #    choices.append(choice)
        #    groups = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,label="",choices=choices, required=False)
    group = forms.CharField(max_length=64, required=False)
    participation = forms.CharField(max_length=64, required=False)
    grpid = forms.CharField(max_length=256, required=False)



class UserList(forms.Form):
    name = forms.CharField(max_length=64)
    id = forms.CharField(max_length=128)
    givenName = forms.CharField(max_length=64)
    surname = forms.CharField(max_length=64)
    postOfficeName = forms.CharField(max_length=64)

