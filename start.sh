#!/bin/bash
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

set -e

# Environment variables must be provided
if [ -z ${PASSWORD+x} ] ; then
    echo "PASSWORD must be provided"
    exit 2
fi

chmod a+rw -R /data/ 
cd /data/
/tmp/wait-for-it.sh -t 0 data-loader:80 -- echo "Data loader is up"

# Handle special flags if we're root
if [ $UID == 0 ] ; then
    # Change UID of NB_USER to NB_UID if it does not match
    if [ "$NB_UID" != $(id -u $NB_USER) ] ; then
        usermod -u $NB_UID $NB_USER
        chown -R $NB_UID $CONDA_DIR .
    fi

    # Enable sudo if requested
    if [ ! -z "$GRANT_SUDO" ]; then
        echo "$NB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/notebook
    fi

    # Exec the command as NB_USER
    exec su $NB_USER -c "env PATH=$PATH $*"
else
    # Exec the command
    exec $*
fi
