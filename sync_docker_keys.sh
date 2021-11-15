#!/bin/bash

# sync in things you need for certs
rsync -a /etc/apt/ apt/
rsync -a /usr/share/keyrings/ keyrings/
rsync -a /etc/ssl/ ssl/

# Remove the hosts local repos that doesn't exist in the container
grep -H -o file: apt/sources.list.d/* | cut -d: -f1 | xargs rm -f
