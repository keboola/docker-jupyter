# Copyright (c) Jupyter Development Team.
from jupyter_core.paths import jupyter_data_dir
import subprocess
import io
import os
import errno
import stat
import json
import requests
import sys
from notebook.utils import to_api_path
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
            app.install_packages(packages, True)
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

def saveFile(file_path, token):
    """
    Construct a requests POST call with args and kwargs and process the
    results.
    Args:
        file_path: The relative path to the file from the datadir, including filename and extension
        token: keboola storage api token
    Returns:
        body: Response body parsed from json.
    Raises:
        requests.HTTPError: If the API request fails.
    """

    url = 'http://data-loader-api/data-loader-api/save'
    headers = {'X-StorageApi-Token': token, 'User-Agent': 'Keboola Sandbox Autosave Request'}
    payload = {}
    payload['file'] = {'source': file_path, 'tags': ['autosave']}

    r = requests.post(url, json=payload, headers=headers, timeout=240)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        # Handle different error codes
        raise
    else:
        return r.json()

def script_post_save(model, os_path, contents_manager, **kwargs):
    """
    saves the ipynb file to keboola storage on every save within the notebook
    """
    if model['type'] != 'notebook':
        return
    log = contents_manager.log

    # get the token from env
    token = None
    if 'KBC_TOKEN' in os.environ:
        token = os.environ['KBC_TOKEN']
    else:
        log.error("Could not find the keboola api token.")
    response = saveFile(os.path.relpath(os_path), token)
    log.info("Successfully saved to keboola")

c.FileContentsManager.post_save_hook = script_post_save
