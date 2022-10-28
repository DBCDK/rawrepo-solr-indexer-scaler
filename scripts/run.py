#!/usr/bin/env python3

import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_worker_count(url, workers):
    res = requests.get(url + '/api/v1/queue/stats/workers')
    j = res.json()

    for found_worker in j['queueStats']:
        for worker in workers:
            if found_worker['text'] == worker['queueworker']:
                worker['queue_count'] = found_worker['count']
                break

    for worker in workers:
        if 'queue_count' not in worker:
            worker['queue_count'] = 0


def get_replica_count(base_url, namespace, worker, token):
    url = base_url + '/apis/apps/v1/namespaces/{0}/deployments/{1}/scale'.format(namespace, worker['deployment_name'])
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.get(url, headers=headers, verify=False)
    j = res.json()
    worker['replicas'] = j['status']['replicas']


def set_replica_count(base_url, namespace, worker, token, replica_count):
    # Get replica json
    url = base_url + '/apis/apps/v1/namespaces/{0}/deployments/{1}/scale'.format(namespace, worker['deployment_name'])
    headers = {'Authorization': 'Bearer ' + token, 'Content-type': 'application/json'}
    res = requests.get(url, headers=headers, verify=False)
    data = res.json()

    data['spec']['replicas'] = replica_count

    # Set replica count
    requests.put(url, json=data, headers=headers, verify=False)


def get_actual_level(levels, current_replicas):
    if current_replicas >= levels['HIGH']['replica_count']:
        return levels['HIGH']
    elif current_replicas >= levels['MID']['replica_count']:
        return levels['MID']
    else:
        return levels['LOW']


def get_expected_level(levels, current_queue_count):
    if current_queue_count >= levels['HIGH']['scale_up_to']:
        return levels['HIGH']
    elif current_queue_count >= levels['MID']['scale_up_to']:
        return levels['MID']
    else:
        return levels['LOW']


def handle_scale(levels, worker):
    current_replicas = worker['replicas']
    current_queue_count = worker['queue_count']

    do_scale = False

    actual_level = get_actual_level(levels, current_replicas)
    expected_level = get_expected_level(levels, current_queue_count)

    # Check for scale down threshold
    if expected_level['value'] < actual_level['value']:
        if expected_level == levels['MID']:
            do_scale = (current_queue_count <= levels['MID']['scale_down_to'])
        elif expected_level == levels['LOW']:
            do_scale = current_queue_count <= levels['LOW']['scale_down_to']
    elif expected_level['value'] > actual_level['value']:
        do_scale = True

    print('Worker: %s - current replica level: %s - expected replica level: %s - should scale? %s' % (
        worker['worker'], actual_level['name'], expected_level['name'], do_scale))

    if do_scale:
        return expected_level
    else:
        return None


with open('config.json') as json_file:
    config = json.load(json_file)

with open('/var/run/secrets/kubernetes.io/serviceaccount/token') as file:
    token = file.read()

workers = config['workers']
api_base_url = config['api_base_url']
namespace = config['namespace']
levels = config['levels']

# Hack because the rawrepo-record-service service name in metascrum-staging differs from other namespaces
if 'rawrepo_record_service_url' in config:
    rawrepo_record_service_url = config['rawrepo_record_service_url']
    if rawrepo_record_service_url[-1] == '/': # Remove trailing '/' just in case
        rawrepo_record_service_url = rawrepo_record_service_url[0:-1]
else:
    rawrepo_record_service_url = 'http://rawrepo-record-service.{0}.svc.cloud.dbc.dk'.format(namespace)

get_worker_count(rawrepo_record_service_url, workers)

for worker in workers:
    get_replica_count(api_base_url, namespace, worker, token)
    expected_level = handle_scale(levels, worker)

    if expected_level != None:
        print('Scaling %s to %s' % (worker['queueworker'], expected_level['replica_count']))
        set_replica_count(api_base_url, namespace, worker, token, expected_level['replica_count'])
