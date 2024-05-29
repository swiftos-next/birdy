import requests
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--fetch", help="Fetch a package")
parser.add_argument("--publish", help="Publish a package")
args = parser.parse_args()

if(args.publish):
    description = input("Description: ")
    version = input("Version: ")
    module_data = {
        'name': args.publish,
        'AuthorName': 'Natesworks',
        'description': description,
        'version': version,
    }

    data = {
        'json': json.dumps(module_data),
    }

    filename = input("File: ")

    try:
        with open(filename) as module:
            content = module.read()
    except FileNotFoundError:
        print(f"\033[31mFile {filename} not found!\033[0m")
        exit(1)

    files = {'file': (args.publish, content)}
    response = requests.post('http://localhost:5000/publish', files=files, data=data)

    print(response.text)

def download_file(url, destination):
    response = requests.get(url)
    if response.status_code == 200:
        with open(destination, 'wb') as f:
            f.write(response.content)
        print(f"File downloaded successfully to {destination}")
    else:
        print(f"Failed to download file from {url}")

if(args.fetch):
    output = input("Output: ")
    download_file(f"http://localhost:5000/modules/{args.fetch}", output)