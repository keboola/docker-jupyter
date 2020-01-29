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

# setup hook on autosave
_script_exporter = None

def script_post_save(model, os_path, contents_manager, **kwargs):
    """convert notebooks to Python script after save with nbconvert

    replaces `jupyter notebook --script`
    """
    if model['type'] != 'notebook':
        return

    Client(, )
    global _script_exporter

    if _script_exporter is None:
        _script_exporter = ScriptExporter(parent=contents_manager)

    log = contents_manager.log

    base, ext = os.path.splitext(os_path)
    script, resources = _script_exporter.from_filename(os_path)
    script_fname = base + resources.get('output_extension', '.txt')
    log.info("Saving script /%s", to_api_path(script_fname, contents_manager.root_dir))

    with io.open(script_fname, 'w', encoding='utf-8') as f:
        f.write(script)

def saveFile():
        """
        Construct a requests POST call with args and kwargs and process the
        results.
        Args:
            *args: Positional arguments to pass to the post request.
            **kwargs: Key word arguments to pass to the post request.
        Returns:
            body: Response body parsed from json.
        Raises:
            requests.HTTPError: If the API request fails.
        """
        headers = {'X-StorageApi-Token': token,
                   'User-Agent': 'Keboola Sandbox Autosave Request'}
        headers.update(self._auth_header)
        r = requests.post(headers=headers, *args, **kwargs)
        try:
            r.raise_for_status()
        except requests.HTTPError:
            # Handle different error codes
            raise
        else:
            return r.json()

c.FileContentsManager.post_save_hook = script_post_save
