#!/bin/bash

if [ -z "$GITREPO_TEMPLATES" ]
then
	cd /opt/cnaas/www/templates
	git pull
else
	cd /opt/cnaas/www
	rm -rf /opt/cnaas/www/templates
        BRANCH=""
        [ -n "$GITBRANCH_TEMPLATES" ] && BRANCH="-b $GITBRANCH_TEMPLATES"
	git clone $BRANCH $GITREPO_TEMPLATES templates
fi

set -e

nginx -g "daemon off;"
