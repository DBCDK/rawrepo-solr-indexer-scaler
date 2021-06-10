# rawrepo-solr-indexer-scaler

## Introduction
This project contains a small python script which can scale the solr indexers up or down

## Getting started

- You need python 3 with the 'requests' dependency installed (preferably in a virtualenv)
- Copy config.example.json to config.json and make relevant changes  
- Then you need to obtain the token for the serviceaccount which is used to call the kubernetes API. That is done with this command:
```shell
echo $(kubectl -n $namespace get secret $(kubectl get serviceaccount -n $namespace rawrepo-solr-scaler -o jsonpath='{.secrets[0].name}') -o jsonpath='{.data.token}' | base64 --decode )
```
Replace $namespace with the correct value and put the returned value as the `token` value in config.json

You can now run the script: ```python3 scripts/run.py ```

## Docker
There is a docker image with the script which can be used by either building the image or downloading it and then running it with a volume mounted config.json.

To build locally:
```shell
docker build -t docker-io.dbc.dk/rawrepo-solr-indexer-scaler:dev .
```

And the run
```shell
docker run -t -v path/to/config.json:/home/python/config.json docker-io.dbc.dk/rawrepo-solr-indexer-scaler:version bash -c "python scripts/run.py"
```

## How to create the serviceaccount and token
```shell
kubectl -n $namespace create rolebinding rawrepo-solr-scaler-binding --clusterrole=edit --serviceaccount=$namespace:rawrepo-solr-scaler
```
```shell
kubectl -n $namespace create serviceaccount rawrepo-solr-scaler
```