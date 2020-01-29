FROM quay.io/keboola/docker-custom-python:1.6.0

ARG NB_USER="jupyter"
ARG NB_UID="1000"
ARG NB_GID="100"

USER root

# Taken from https://github.com/jupyter/docker-stacks/blob/master/minimal-notebook/Dockerfile

# Install all OS dependencies for fully functional notebook server
# ffmpeg for matplotlib anim
RUN apt-get update && apt-get install -yq --no-install-recommends \
    build-essential \
    emacs \
    git \
    inkscape \
    jed \
    ffmpeg \
    libsm6 \
    libxext-dev \
    libxrender1 \
    lmodern \
    pandoc \
    python-dev \
    texlive-fonts-extra \
    texlive-fonts-recommended \
    texlive-generic-recommended \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-xetex \
    vim \
    unzip \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Taken from https://github.com/jupyter/docker-stacks/tree/master/base-notebook

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    wget \
    bzip2 \
    ca-certificates \
    sudo \
    locales \
    fonts-liberation \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Configure environment
ENV SHELL /bin/bash
ENV NB_USER $NB_USER
ENV NB_UID $NB_UID
ENV NB_GID $NB_GID
ENV HOME /home/$NB_USER
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Add a script that we will use to correct permissions after running certain commands
ADD fix-permissions /usr/local/bin/fix-permissions

# Create NB_USER with NB_UID and in the NB_GID group
# and make sure these dirs are writable by the NB_GID group.
RUN echo "auth requisite pam_deny.so" >> /etc/pam.d/su && \
    sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers && \
    sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers && \
    useradd -m -s /bin/bash -N -u $NB_UID -g $NB_GID $NB_USER && \
    chmod g+w /etc/passwd && \
    fix-permissions $HOME

# Install Tini
RUN wget --quiet https://github.com/krallin/tini/releases/download/v0.10.0/tini && \
    echo "1361527f39190a7338a0b434bd8c88ff7233ce7b9a4876f3315c22fce7eca1b0 *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini && \
    fix-permissions /home/$NB_USER

USER $NB_UID
WORKDIR $HOME

# Setup work directory for backward-compatibility
RUN mkdir /home/$NB_USER/work && \
    fix-permissions /home/$NB_USER

# Taken from https://github.com/jupyter/docker-stacks/blob/master/scipy-notebook/Dockerfile
# run the pip installations as root
USER root

# Install Python 3 packages
# Remove pyqt and qt pulled in for matplotlib since we're only ever going to
# use notebook-friendly backends in these images
RUN pip3 install --no-cache-dir \
    notebook \
    jupyterhub \
    jupyterlab \
    ipywidgets \
    pandas \
    numexpr \
    matplotlib \
    scipy \
    seaborn \
    scikit-learn \
    scikit-image \
    sympy \
    cython \
    patsy \
    statsmodels \
    cloudpickle \
    dill \
    numba \
    bokeh \
    sqlalchemy \
    h5py \
    vincent \
    beautifulsoup4 \
    xlrd \
    qgrid

# Activate ipywidgets extension in the environment that runs the notebook server
RUN jupyter nbextension enable --py widgetsnbextension --sys-prefix \
 && jupyter nbextension enable --py --sys-prefix qgrid

# Import matplotlib the first time to build the font cache.
ENV XDG_CACHE_HOME /home/$NB_USER/.cache/
RUN MPLBACKEND=Agg python -c "import matplotlib.pyplot"

### Custom stuff
# Install KBC Transformation package
RUN pip3 install --no-cache-dir --upgrade git+git://github.com/keboola/python-transformation.git@1.2.4

EXPOSE 8888
WORKDIR /data/
RUN fix-permissions /data

# the datadir should now be owned by NB_UID
USER $NB_UID
CMD chmod -R 777 /data
CMD chmod -R g+s /data

# add users local bin dir to PATH
ENV PATH=/home/$NB_USER/.local/bin:$PATH

# Configure container startup
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.sh"]

# Add local files as late as possible to avoid cache busting
COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/
COPY jupyter_notebook_config.py /etc/jupyter/
COPY wait-for-it.sh /usr/local/bin/

USER root
RUN fix-permissions /home/$NB_USER
RUN chown -R $NB_USER:$NB_GID /etc/jupyter/

USER $NB_UID
