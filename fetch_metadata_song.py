import requests
import json
import os
import argparse
import re

def fetch_song_data(service, song_id, save=False, save_dir=None, verbose=False):
    data = None

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
        if response.status_code == 404:
            return None

        plain_text = response.text
        # if verbose: print("RESPONSE:\n", plain_text)
        plain_text = plain_text[plain_text.find('"clip"'):]
        # if verbose: print("FIND:\n", plain_text)
        plain_text = plain_text[7:].split(',"persona"')[0]
        # if verbose: print("SPLIT:\n", plain_text)
        data = json.loads(plain_text)

    elif service == 'udio':
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
        if response.status_code == 404:
            return None

        plain_text = response.text
        # return response.text
        # if verbose: print("RESPONSE:\n", plain_text)
        plain_text = plain_text[plain_text.find('"track"'):]
        plain_text = plain_text[8:].split('}]}]}]')[0]
        # if verbose: print("SPLIT:\n", plain_text)
        data = json.loads(plain_text)

        # udio will put long lyrics in a separate field
        # the http response text will contain the label for the full lyrics under lyrics in data
        if data['lyrics'].startswith('$'):
            data_label = data['lyrics'][1:]
            # find datalabel index in the response text using re
            pattern = rf"(?<=\n){re.escape(data_label)}:(?P<suffix>[a-zA-Z0-9]{{4}}),"
            match = re.search(pattern, response.text)
            lyrics_start = match.end()
            lyrics_end = response.text.find('2:[', lyrics_start)
            full_lyrics =  response.text[lyrics_start:lyrics_end]
            # print(response.text.find(f"{data_label}:"))
            data['lyrics'] = full_lyrics.strip()

    else:
        print(f"Service '{service}' not recognized.")
        return

    # Print the retrieved data
    if verbose: print(f"DATA:\n{data}")

    # Save the data if the --save flag is used
    if save and data:
        save_data(service, data['id'], data, save_dir, verbose)

def save_data(service, song_id, data, save_dir=None, verbose=False):
    # Determine the base directory: provided save_dir or current working directory
    base_dir = save_dir if save_dir else ''
    
    # Create the directory structure {base_dir}/{service}/metadata/
    directory = os.path.join(base_dir, service, 'metadata')
    os.makedirs(directory, exist_ok=True)

    # Save the data to {base_dir}/{service}/metadata/{song_id}.json
    file_path = os.path.join(directory, f'{song_id}.json')
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    if verbose: print(f'Data saved to {file_path}')
    


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch song data from a service. E.g. python fetch_metadata_song.py suno 18cc37ed-391d-4160-923d-a6e652533df5')
    parser.add_argument('service', type=str, help="Service to use ('suno' or 'udio')")
    parser.add_argument('song_id', type=str, help='ID of the song to fetch')
    parser.add_argument('--save', action='store_true', help='Save the fetched data to a file')
    parser.add_argument('--dir', type=str, default=None, help='Directory where data will be saved')
    # add verbose flag
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    # Parse the arguments
    args = parser.parse_args()

    # Fetch the song data
    fetch_song_data(args.service, args.song_id, args.save, args.dir, args.verbose)

if __name__ == "__main__":
    main()
