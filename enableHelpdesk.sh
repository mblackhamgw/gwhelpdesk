#!/bin/bash

systemctl enable gwhelpdesk
chkconfig gwhelpdesk on
chkconfig nginx on

chmod +x /var/gwhelpdesk/update_gwhelpdesk.sh
chmod +x /var/gwhelpdesk/install_gwhelpdesk.sh

read -p "Start gwhelpdesk application now?  (y/n) : " choice
case "$choice" in
    y|Y )
        rcgwhelpdesk start
        rcnginx start
    ;;
    n|N )
        echo "To manually start services"
        echo "Run rcgwhelpdesk start and rcnginx start"
    ;;
esac
