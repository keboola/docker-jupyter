# Jupyter
Docker image with [Jupyter sandbox](https://help.keboola.com/manipulation/transformations/sandbox/) based on Keboola [Custom Python](https://github.com/keboola/docker-custom-python) which is shared between transformations and sandboxes. Public image is available on [Quay](https://quay.io/repository/keboola/docker-jupyter).

To run locally use the `.env.template` file to create an `.env` file. Create a python transformation configuration. Set the following variables:

- `KBC_CONFIG_ID` - Transformation configuration (bucket) ID.
- `KBC_ROW_ID` - Transformation configuration row ID.
- `KBC_CONFIG_VERSION` - Version of the configuration to use.
- `KBC_STORAGEAPI_URL` - Connection URL.
- `KBC_TOKEN` - Connection token with access to configuration and storage tables referenced there.
- `PACKAGES` - optional JSON array with packages to preinstall, use `[]` to install no packages

Run `docker-compose up`, the notebook will be avaiable at `http://localhost:8888`. Password is `test`, can be changed in `docker-compose.yml`.
