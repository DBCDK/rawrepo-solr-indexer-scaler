#!/usr/bin/env python3

import json
import requests


def get_worker_count(namespace, workers):
    res = requests.get(
        'http://rawrepo-record-service.{0}.svc.cloud.dbc.dk/api/v1/queue/stats/workers'.format(namespace))
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
    res = requests.put(url, json=data, headers=headers, verify=False)
    print(res)


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
        if expected_level == levels.MID:
            do_scale = (current_queue_count <= levels.MID['scale_down_to'])
        elif expected_level == levels.LOW:
            do_scale = current_queue_count <= levels.LOW['scale_down_to']
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

workers = config['workers']
api_base_url = config['api_base_url']
namespace = config['namespace']
token = config['token']
levels = config['levels']

get_worker_count(namespace, workers)

for worker in workers:
    get_replica_count(api_base_url, namespace, worker, token)
    expected_level = handle_scale(levels, worker)

    if expected_level != None:
        print('Scaling %s to %s' % (worker['queueworker'], expected_level['replica_count']))
        set_replica_count(api_base_url, namespace, worker, token, expected_level['replica_count'])
