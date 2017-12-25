from django.conf.urls import url
from django.conf import settings

from helpdesk import views



urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^index/$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^gwconfig/$', views.gwconfig, name='gwconfig'),
    #url(r'^configerror/$', views.configerror, name='configerror'),
    url(r'^admins/$', views.admins, name='admins'),
    url(r'^changepassword/$', views.changepassword, name='changepassword'),
    url(r'^changeadminpassword/$', views.changeadminpassword, name='changeadminpassword'),
    url(r'^addadmin/$', views.addadmin, name='addadmin'),
    url(r'^search/$', views.search, name='search'),
    url(r'^searchresults/$', views.searchresults, name='searchresults'),
    url(r'^userdata/$', views.userdata, name='userdata'),
    url(r'^groups/$', views.groups, name='groups'),
    url(r'^groupdetails/$', views.groupdetails, name='groupdetails'),
    #url(r'^groupsearch/$', views.groupsearch, name='groupsearch'),
    url(r'^grouplist/$', views.grouplist, name='grouplist'),
    url(r'^move/$', views.move, name='move'),
    url(r'^maintenance/$', views.maintenance, name='maintenance'),
    url(r'^addtogroups/$', views.addtogroups, name='addtogroups'),
    url(r'^adduser/$', views.adduser, name='adduser'),
    url(r'^deluser/$', views.deluser, name='deluser'),
    url(r'^userlist/$', views.userlist, name='userlist'),
    url(r'^rename/$', views.rename, name='rename'),
    url(r'^dissociate/$', views.dissociate, name='dissociate'),
    url(r'^viewlog/$', views.viewlog, name='viewlog'),
    url(r'^nicknames/$', views.nicknames, name='nicknames'),
    url(r'^addnickname/$', views.addnickname, name='addnickname'),
    url(r'^resources/$', views.resources, name='resources'),
    url(r'^addresource/$', views.addresource, name='addresource'),


]