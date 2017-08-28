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
#c.FileContentsManager.root_dir = '/data'

print("Initializing Jupyter", file=sys.stderr)

# Generate a self-signed certificate
if 'GEN_CERT' in os.environ:
    dir_name = jupyter_data_dir()
    pem_file = os.path.join(dir_name, 'notebook.pem')
    try:
        os.makedirs(dir_name)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
            pass
        else:
            raise
    # Generate a certificate if one doesn't exist on disk
    subprocess.check_call(['openssl', 'req', '-new',
                           '-newkey', 'rsa:2048',
                           '-days', '365',
                           '-nodes', '-x509',
                           '-subj', '/C=XX/ST=XX/L=XX/O=generated/CN=generated',
                           '-keyout', pem_file,
                           '-out', pem_file])
    # Restrict access to the file
    os.chmod(pem_file, stat.S_IRUSR | stat.S_IWUSR)
    c.NotebookApp.certfile = pem_file

# Set a password if PASSWORD is set
if 'PASSWORD' in os.environ:
    from IPython.lib import passwd
    c.NotebookApp.password = passwd(os.environ['PASSWORD'])
    del os.environ['PASSWORD']

# jupyter trust /path/to/notebook.ipynb
# Fake Script
print('Loading script into notebook', file=sys.stderr);
with open(os.path.join('/tmp/notebook.ipynb'), 'r') as notebook_file:
    data = json.load(notebook_file)
    if 'SCRIPT' in os.environ:
        data['cells'][0]['source'] = os.environ['SCRIPT']
with open(os.path.join('/data/notebook.ipynb'), 'w') as notebook_file:
    json.dump(data, notebook_file)

# Install packages
app = transformation.App()
try:
    if 'PACKAGES' in os.environ:
        print('Loading packages "' + os.environ['PACKAGES'] + '"', file=sys.stderr)
        packages = json.loads(os.environ['PACKAGES'])
        if isinstance(packages, list):
            app.install_packages(packages)
        else:
            print('Packages are not array.', file=sys.stderr)
except ValueError as err:
    print('Packages is not JSON array.', file=sys.stderr)

try:
    if 'TAGS' in os.environ:
        print('Loading tagged files from "' + os.environ['TAGS'] + '"', file=sys.stderr)
        tags = json.loads(os.environ['TAGS'])
        if isinstance(tags, list):
            # create fake config file
            with open(os.path.join('/data/', 'config.json'), 'w') as config_file:
                json.dump({'parameters': []}, config_file)
            cfg = docker.Config('/data/')
            app.prepare_tagged_files(cfg, tags)
            os.remove('/data/config.json')
        else:
            print('Tags are not an array.', file=sys.stderr)
except ValueError as err:
    print('Tags is not JSON array.', file=sys.stderr)
