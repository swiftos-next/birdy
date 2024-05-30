import requests
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--fetch", nargs=2, help="Fetch a package")
parser.add_argument("--publish", nargs=4, help="Publish a package")

args = parser.parse_args()

def publish():
    filename = args.publish[0]
    name = args.publish[1]
    version = args.publish[2]
    description = args.publish[3]

    module_data = {
        'name': name,
        # placeholder will later use authentication
        'AuthorName': 'Natesworks',
        'version': version,
        'description': description
    }

    data = {
        'json': json.dumps(module_data),
    }

    try:
        with open(filename) as module:
            content = module.read()
    except FileNotFoundError:
        print(f"\033[31mFile {filename} not found!\033[0m")
        exit(1)

    files = {'file': (name, content)}
    response = requests.post(
        'http://localhost:5000/publish', files=files, data=data)

    print(response.text)


if (args.publish):
    publish()


def download_file(url, destination):
    response = requests.get(url)
    if response.status_code == 200:
        with open(destination, 'wb') as f:
            f.write(response.content)
        print(f"File downloaded successfully to {destination}")
    else:
        print(f"\033[31mFailed to download file from {url}")


def fetch_latest_version(name):
    try:
        response = requests.get(f"http://localhost:5000/versions/{name}")
        response.raise_for_status()
        versions = response.json()
        if versions:
            latest_version = max(versions)
            return latest_version
    except requests.RequestException as e:
        print(f"\033[31mError fetching latest version for {name}: {e}")
    return None


if (args.fetch):
    name = args.fetch[0]
    output = args.fetch[1]
    if ("-" not in name):
        name = f"{name}-{fetch_latest_version(name)}"
    download_file(f"http://localhost:5000/modules/{name}", output)
