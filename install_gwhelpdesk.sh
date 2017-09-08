#!/bin/bash

echo "Checking OS Version"
VER=`head -1 /etc/SuSE-release | awk '{print $1;}'`
if [ "$VER" == "openSUSE" ]; then
        echo "OS is openSUSE"
elif [ "$VER" == "SUSE" ]; then
        echo "OS is SLES"
        echo "Adding repository for nginx..."
        zypper addrepo -G -t yum -c 'http://nginx.org/packages/sles/12' nginx
fi

echo "Installing some needed packages.."

declare -a rpms=(python-pip nginx git)
for rpm in "${rpms[@]}"
    do
    echo "Installing"  $rpm
    zypper -n install $rpm
    done

PY=`rpm -qa | grep python-2.7`
if [[ $PY == *"python-2.7"* ]]; then
  echo "Python 2.7 is installed"
else
    echo "Installing Python 2.7"
    zypper -n  in python
fi

echo "Installing some Python modules..."
yes | pip install django gunicorn requests django-baseurl django-ipware

echo "Getting the gwhelpdesk app from git.."
mkdir -p /var/gwhelpdesk

GIT_SSL_NO_VERIFY=true git clone https://github.com/mblackhamgw/gwhelpdesk.git /var/gwhelpdesk
