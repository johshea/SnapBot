# -*- coding:utf-8 -*-
#!/usr/bin/python
import requests
import re
import json
import ciscosparkapi
import datetime
import time




now = datetime.datetime.now()



network_id = ('<Variable>')
access_token = ('<Variable>')
teams_room = ("<Variable>")
api_key = ('<Variable>')

#to do, grab a device list and pull all serials for device type MV

spark = ciscosparkapi.CiscoSparkAPI(access_token=access_token)
base_url = 'https://api.meraki.com/api/v0'


def meraki_snapshots( api_key, network_id, time=None,  filters=None):
    # Get devices of network and filter for MV cameras
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        #'Content-Type': 'application/json'  # issue where this is only needed if timestamp specified
    }
    response = requests.request("GET",f'https://api.meraki.com/api/v0/networks/{network_id}/devices', headers=headers)
    devices = response.json()
    cameras = [device for device in devices if device['model'][:2] == 'MV']

    snapshoturl = []
    for camera in cameras:
        #Remove any cameras not matching filtered names
        name = camera['name'] if 'name' in camera else camera['mac']
        tags = camera['tags'] if 'tags' in camera else ''
        tags = tags.split()
        if filters and name not in filters and not set(filters).intersection(tags):
            continue

        # Get video link
        if time:
            response = requests.get(
                    f'https://api.meraki.com/api/v0/networks/{network_id}/cameras/{camera["serial"]}/videoLink?timestamp={time}',
                    headers=headers)
        else:
            response = requests.get(
                f'https://api.meraki.com/api/v0/networks/{network_id}/cameras/{camera["serial"]}/videoLink',
                headers=headers)
        video_link = response.json()['url']

        if time:
            headers['Content-Type'] = 'application/json'
            response = requests.request("POST",
                f'https://api.meraki.com/api/v0/networks/{network_id}/cameras/{camera["serial"]}/snapshot',
                headers=headers,
                #data=json.dumps({'timestamp': time})
                                        )
        else:
            response = requests.request("POST",
                f'https://api.meraki.com/api/v0/networks/{network_id}/cameras/{camera["serial"]}/snapshot',
                headers=headers)

        if response.ok:
            #snapshoturl.append((name, response.json()['url']))
            snapshoturl.append((name, response.json()['url']))
    return snapshoturl

# Determine whether to retrieve all cameras or just selected snapshots
def return_snapshots(session, headers, payload, api_key, net_id, message, cameras):
    try:
        # All cameras
        if message_contains(message, ['all', 'complete', 'entire', 'every', 'full']):
            post_message(headers, payload,
                         '📸 _Retrieving all cameras\' snapshots..._')
            snapshots = meraki_snapshots(api_key, net_id, None, None)

        # Or just specified/filtered ones
        else:
            post_message(headers, payload,
                         '📷 _Retrieving camera snapshots..._')
            snapshots = meraki_snapshots(session, api_key, net_id, None, cameras)

        # Wait a bit to ensure cameras to upload snapshots to links
        time.sleep(9)

        # Send cameras names with files (URLs)
        for (name, snapshot, video) in snapshots:
            post_file(headers, payload, f'[{name}]({video})', snapshot)
    except:
        post_message(session, headers, payload,
                     'Does your API key have access to the specified network ID.')


snapshoturl = meraki_snapshots(api_key, network_id)

#loop through cameras and post them to the webex teams room
i = 0
for i in range(len(snapshoturl)):
        #post to teams room
        spark.messages.create(
             teams_room,
             #text="Snapshot Captured: " + str(now),
             ##markdown = re.sub(expr, '',urlpath)
             text = str(now) + ', ' + '\n'.join(map(str, snapshoturl[i]))
           )
i += 1




