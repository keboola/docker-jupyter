#!/bin/bash
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

set -e

# Environment variables must be provided
if [ -z ${PASSWORD+x} ] ; then
    echo "PASSWORD must be provided"
    exit 2
fi

/usr/local/bin/wait-for-it.sh -t 0 data-loader:80 -- echo "Data loader is up"
#jupyter trust /notebooks/notebook.ipynb

# Handle special flags if we're root
if [ $UID == 0 ] ; then
    # Change UID of NB_USER to NB_UID if it does not match
    if [ "$NB_UID" != $(id -u $NB_USER) ] ; then
        echo "Set user UID to: $NB_UID"
        usermod -u $NB_UID $NB_USER
        # Careful: $HOME might resolve to /root depending on how the
        # container is started. Use the $NB_USER home path explicitly.
        for d in "/data" "/home/$NB_USER"; do
            if [[ ! -z "$d" && -d "$d" ]]; then
                echo "Set ownership to uid $NB_UID: $d"
                chown -R $NB_UID:$NB_GID "$d"
            fi
        done
    fi

    # Change GID of NB_USER to NB_GID if NB_GID is passed as a parameter
    if [ "$NB_GID" ] ; then
        echo "Change GID to $NB_GID"
        groupmod -g $NB_GID -o $(id -g -n $NB_USER)
    fi

    # Enable sudo if requested
    if [ ! -z "$GRANT_SUDO" ]; then
        echo "$NB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/notebook
    fi

    # Exec the command as NB_USER
    echo "Execute the command as $NB_USER"
    exec su $NB_USER -c "env PATH=$PATH $*"
else
    # Exec the command
    echo "Execute the command"
    exec $*
fi
