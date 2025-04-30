import pandas as pd
from tqdm import tqdm
# tqdm.pandas()
import requests
import argparse

argsParser = argparse.ArgumentParser(description='Check the status of a song on a service. E.g. python check_link.py suno 0 100')
argsParser.add_argument('service', type=str, help="Service to use ('suno' or 'udio')")
argsParser.add_argument('--start_idx', type=int, default=0, help='Start index of the song to check', required=False)
argsParser.add_argument('--end_idx', type=int, default=-1, help='End index of the song to check', required=False)
args = argsParser.parse_args()

def check_status(service, song_id, verbose=False):
    
    if service == 'suno':
        url = f'https://suno.com/song/{song_id}'
        if verbose: print(f'Fetching data from {url}')
        headers = {
            'accept': '*/*',
            'accept-language': 'en,es-ES;q=0.9,es;q=0.8,ca;q=0.7,sv;q=0.6',
            'next-url': f'/song/{song_id}',
            'priority': 'u=1, i',
            'referer': 'https://suno.com/create',
            'rsc': '1',
        }

        response = requests.get(url, headers=headers)
        if verbose: print(f'Status code: {response.status_code}')
        # if verbose: print(f'RESPONSE: {response.text}')
        page_not_found = response.text.find('This page could not be found')
        string_404 = response.text.find('404')
        clipid_in_page = response.text.find(f'{{"clip":{{"id":"{song_id}"')
        if verbose: print(f'Page not found: {page_not_found}; String 404: {string_404}; Clip ID in page: {clipid_in_page}')
        if clipid_in_page == -1:
            return 'NOT_FOUND'
        if response.status_code != 200:
            return response.status_code
        return 'FOUND'

    if service == 'udio':
        url = f'https://www.udio.com/songs/{song_id}'
        if verbose: print(f'Fetching data from {url}')
        headers = {
            'accept': '*/*',
            'accept-language': 'en,es-ES;q=0.9,es;q=0.8,ca;q=0.7,sv;q=0.6',
            'priority': 'u=1, i',
            'rsc': '1',
        }

        response = requests.get(url, headers=headers)
        if verbose: print(f'Status code: {response.status_code}')
        # if verbose: print(f'RESPONSE: {response.text}')
        track_not_found = response.text.find('Track not found')
        if verbose: print(f'Track not found: {track_not_found}')
        # return response.status_code
        if track_not_found != -1:
            return 'NOT_FOUND'
        if response.status_code != 200:
            return str(response.status_code)
        return 'FOUND'
        
if args.service == 'udio':
    udio_df = pd.read_pickle("../../udio_metadata.pkl")[args.start_idx:args.end_idx]
    if args.start_idx == 0:
        print('check links for udio')
        print('---')

    NOT_FOUND_COUNT = 0

    pbar = tqdm(udio_df.iterrows(), total=udio_df.shape[0])
    for idx, row in pbar:    
        status = check_status('udio', row['id'], verbose=False)
        pbar.set_description_str(desc=f"{idx}: {status}", refresh=True)
        udio_df.at[idx, 'status'] = status
        if status != 'FOUND':
            NOT_FOUND_COUNT += 1
            # print(f"{idx} - {status}: https://www.udio.com/songs/" + row['id'])
            pbar.write(f"{idx} - {status}: https://www.udio.com/songs/" + row['id'])
            if NOT_FOUND_COUNT > 10:
                print('>>> ALERT: errors >= 10 maybe we are blocked?')
        else:
            NOT_FOUND_COUNT = 0
    if args.start_idx == 0:
        udio_df[['id', 'status']].to_csv('udio_status.csv', index=True)
        print('---DONE---')
    else:
        # append to csv
        udio_df[['id', 'status']].to_csv('udio_status.csv', index=True, mode='a', header=False)

if args.service == 'suno':
    suno_df = pd.read_pickle("../../suno_metadata.pkl")[args.start_idx:args.end_idx]
    if args.start_idx == 0:
        print('check links for suno')
        print('---')

    NOT_FOUND_COUNT = 0

    pbar = tqdm(suno_df.iterrows(), total=suno_df.shape[0])
    for idx, row in pbar:    
        status = check_status('suno', row['id'], verbose=False)
        pbar.set_description_str(desc=f"{idx}: {status}", refresh=True)
        suno_df.at[idx, 'status'] = status
        if status != 'FOUND':
            NOT_FOUND_COUNT += 1
            # print(f"{idx} - {status}: https://suno.com/song/" + row['id'])
            pbar.write(f"{idx} - {status}: https://suno.com/song/" + row['id'])
            if NOT_FOUND_COUNT > 10:
                print('>>> ALERT: errors >= 10 maybe we are blocked?')
        else:
            NOT_FOUND_COUNT = 0
    if args.start_idx == 0:
        suno_df[['id', 'status']].to_csv('suno_status.csv', index=True)
        print('---DONE---')
    else:
        # append to csv
        suno_df[['id', 'status']].to_csv('suno_status.csv', index=True, mode='a', header=False)

import urllib3
import time

if args.service == 'suno_loop':
    DONE = False
    suno_status_csv = pd.read_csv('suno_status.csv', index_col=0, header=0).astype('str')
    START_IDX = suno_status_csv.shape[0]
    print(f"Starting from index {START_IDX}")
    suno_df = pd.read_pickle("../../suno_metadata.pkl")
    print(suno_status_csv.shape)
    WAIT_TIME = 1
    
    
    print(suno_status_csv.iloc[-1]['id'], suno_df.iloc[START_IDX-1]['id'])
    assert suno_status_csv.iloc[-1]['id'] == suno_df.iloc[START_IDX-1]['id']
    
    pbar = tqdm(suno_df.iterrows(), total=suno_df.shape[0], initial=START_IDX)

    while not DONE:
        try:
            status = check_status('suno', suno_df.iloc[START_IDX]['id'], verbose=False)
            WAIT_TIME = min(1, max(0, WAIT_TIME-1))
        except Exception as e:
            print(f"Exception: {e}")
            # wait for WAIT_TIME seconds
            pbar.set_description_str(desc=f"WAITING FOR {WAIT_TIME}s", refresh=True)
            time.sleep(WAIT_TIME)
            WAIT_TIME *= 2
            continue
        print(f"Status: {status}")

        pbar.set_description_str(desc=f"{START_IDX}: {status}", refresh=True)
        IDX = suno_df.iloc[START_IDX].name
        print(IDX)
        suno_df.at[IDX, 'url_status'] = str(status)
        print(suno_df.iloc[START_IDX:START_IDX+1][['id', 'url_status']])
        # append idx, id and status to csv
        suno_df.iloc[START_IDX:START_IDX+1][['id', 'url_status']].to_csv('suno_status.csv', index=True, mode='a', header=False)
        
        if status != 'FOUND':
            # print(f"{idx} - {status}: https://suno.com/song/" + row['id'])
            pbar.write(f"{START_IDX} - {status}: https://suno.com/song/" + suno_df.iloc[START_IDX]['id'])
        
        START_IDX += 1
        # update pbar position to START_IDX
        pbar.n = START_IDX
        pbar.refresh()

        if START_IDX >= suno_df.shape[0]:
            DONE = True
            print('---DONE---')
        


    