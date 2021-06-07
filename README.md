# rawrepo-solr-indexer-scaler

## Introduction
This project contains a small python script which can scale the solr indexers up or down

## Getting started

- You need python 3 with the 'requests' dependency installed (preferably in a virtualenv)
- Copy config.example.json to config.json and make relevant changes  
- Then you need to obtain the token for the serviceaccount which is used to call the kubernetes API. That is done with this command:
```shell
echo $(kubectl -n <namespace> get secret $(kubectl get serviceaccount -n <namespace> rawrepo-solr-scaler -o jsonpath='{.secrets[0].name}') -o jsonpath='{.data.token}' | base64 --decode )
```
Replace namespace (both places) with the with the correct value and the put the returned value as the `token` value in config.json

You can now run the script.