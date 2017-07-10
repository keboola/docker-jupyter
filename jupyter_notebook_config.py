# Copyright (c) Jupyter Development Team.
from jupyter_core.paths import jupyter_data_dir
import subprocess
import os
import errno
import stat
import json
from kbc_transformation import transformation
from keboola import docker

PEM_FILE = os.path.join(jupyter_data_dir(), 'notebook.pem')

c = get_config()
c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False

# Set a certificate if USE_HTTPS is set to any value
if 'USE_HTTPS' in os.environ:
    if not os.path.isfile(PEM_FILE):
        # Ensure PEM_FILE directory exists
        dir_name = os.path.dirname(PEM_FILE)
        try:
            os.makedirs(dir_name)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
                pass
            else: raise
        # Generate a certificate if one doesn't exist on disk
        subprocess.check_call(['openssl', 'req', '-new', 
            '-newkey', 'rsa:2048', '-days', '365', '-nodes', '-x509',
            '-subj', '/C=XX/ST=XX/L=XX/O=generated/CN=generated',
            '-keyout', PEM_FILE, '-out', PEM_FILE])
        # Restrict access to PEM_FILE
        os.chmod(PEM_FILE, stat.S_IRUSR | stat.S_IWUSR)
    c.NotebookApp.certfile = PEM_FILE

# Set a password if PASSWORD is set
if 'PASSWORD' in os.environ:
    from IPython.lib import passwd
    c.NotebookApp.password = passwd(os.environ['PASSWORD'])
    del os.environ['PASSWORD']

# Fake Script
print("Creating notebook")
with open(os.path.join('/home/', os.environ['NB_USER'], 'work/notebook.ipynb'), 'r') as notebook_file:
    data = json.load(notebook_file)
    if 'SCRIPT' in os.environ:
        print('Loading script into notebook');
        data['cells'][0]['source'] = os.environ['SCRIPT']    
with open('/data/notebook.ipynb', 'w') as notebook_file:
    json.dump(data, notebook_file)

# Install packages
app = transformation.App()
try:
    if 'PACKAGES' in os.environ:
        print('Loading packages "' + os.environ['PACKAGES'] + '"')
        packages = json.loads(os.environ['PACKAGES'])
        if isinstance(packages, list):
            app.install_packages(packages)
        else:
            print('Packages are not array.')
except ValueError as err:
    print('Tags is not JSON array.')

try:
    if 'TAGS' in os.environ:
        print('Loading tagged files from "' + os.environ['TAGS'] + '"')
        tags = json.loads(os.environ['TAGS'])
        if isinstance(tags, list):
            # create fake config file
            with open(os.path.join('/data/', 'config.json'), 'w') as config_file:
                json.dump({'parameters': []}, config_file)
            cfg = docker.Config('/data/')
            app.prepare_tagged_files(cfg, tags)
            os.remove('/data/config.json')
        else:
            print('Tags are not an array.')
except ValueError as err:
    print('Tags is not JSON array.')
