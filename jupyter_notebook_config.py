# Copyright (c) Jupyter Development Team.
from jupyter_core.paths import jupyter_data_dir
import subprocess
import os
import errno
import stat
import json
import sys
from kbc_transformation import transformation
from keboola import docker

# Jupyter config http://jupyter-notebook.readthedocs.io/en/latest/config.html
c = get_config()
if 'HOSTNAME' in os.environ:
    c.NotebookApp.ip = os.environ['HOSTNAME']
else:    
    c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
# This changes current working dir, so has to be set to /data/
c.NotebookApp.notebook_dir = '/data/'
c.Session.debug = False
# If not set, there is a permission problem with the /data/ directory
c.NotebookApp.allow_root = True
# Disabled because it breaks notebook_dir
# c.FileContentsManager.root_dir = '/data'

print("Initializing Jupyter.", file=sys.stderr)

# Set a password
if 'PASSWORD' in os.environ and os.environ['PASSWORD']:
    from IPython.lib import passwd
    c.NotebookApp.password = passwd(os.environ['PASSWORD'])
    del os.environ['PASSWORD']
else:
    print('Password must be provided.')
    sys.exit(150)

# jupyter trust /path/to/notebook.ipynb

# Install packages
app = transformation.App()
if 'PACKAGES' in os.environ:
    print('Loading packages "' + os.environ['PACKAGES'] + '"', file=sys.stderr)
    try:
        packages = json.loads(os.environ['PACKAGES'])
    except ValueError as err:
        print('Packages variable is not a JSON array.', file=sys.stderr)
        sys.exit(152)
    if isinstance(packages, list):
        try:
            app.install_packages(packages)
        except ValueError as err:
            print('Failed to install packages', err, file=sys.stderr)
            sys.exit(153)
    else:
        print('Packages variable is not an array.', file=sys.stderr)

if 'TAGS' in os.environ:
    print('Loading tagged files from "' + os.environ['TAGS'] + '"', file=sys.stderr)
    try:
        tags = json.loads(os.environ['TAGS'])
    except ValueError as err:
        print('Tags variable is not a JSON array.', file=sys.stderr)
        sys.exit(154)
    if isinstance(tags, list):
        # create fake config file
        try:
            with open(os.path.join('/data/', 'config.json'), 'w') as config_file:
                json.dump({'parameters': []}, config_file)
            cfg = docker.Config('/data/')
            app.prepare_tagged_files(cfg, tags)
            os.remove('/data/config.json')
        except ValueError as err:
            print('Failed to prepare files', err, file=sys.stderr)
            sys.exit(155)
    else:
        print('Tags variable is not an array.', file=sys.stderr)
