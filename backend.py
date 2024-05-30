import os
import json
import re
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

modules_database = {}
allowed_package_names = re.compile(r'^[A-Za-z0-9]*$')
db_file_path = 'db/modules_database.json'

def load_modules_database():
    global modules_database
    if os.path.exists(db_file_path):
        with open(db_file_path, 'r') as db_file:
            modules_database = json.load(db_file)

def save_modules_database():
    global modules_database
    with open(db_file_path, 'w') as db_file:
        json.dump(modules_database, db_file, indent=4)

def save_module_info(module_info):
    global modules_database
    key = f"{module_info['name']}-{module_info['version']}"
    modules_database[key] = module_info
    save_modules_database()

def get_module_info(module_name, module_version=None):
    global modules_database
    if module_version:
        key = f"{module_name}-{module_version}"
        return modules_database.get(key)
    else:
        return [info for key, info in modules_database.items() if key.startswith(f"{module_name}-")]

def update_module_info(module_name, module_version, module_info):
    global modules_database
    key = f"{module_name}-{module_version}"
    modules_database[key] = module_info
    save_modules_database()

@app.route('/modules/<filename>')
def module_file(filename):
    return send_from_directory('db/modules', filename)

@app.route('/publish', methods=['POST'])
def publish_module():
    data = json.loads(request.form.get('json'))
    if allowed_package_names.match(data['name']):
        module_info = {
            'name': data['name'],
            'author': data['AuthorName'],
            'description': data['description'],
            'version': data['version'],
            'file': secure_filename(request.files['file'].filename),
            'downloads': 0,
            'verified': False
        }

        file = request.files['file']
        file_path = f"{os.path.join('db/modules')}/{secure_filename(file.filename)}-{module_info['version']}"
        file.save(file_path)
        module_info['file'] = file_path

        save_module_info(module_info)

        return 'Module published successfully!', 200
    return 'Invalid package name', 400

@app.route('/install/<module_name>/<module_version>', methods=['GET'])
def install_module(module_name, module_version):
    module_info = get_module_info(module_name, module_version)

    if module_info is None:
        return 'Module not found.', 404

    module_info['downloads'] += 1

    update_module_info(module_name, module_version, module_info)

    return send_from_directory('db/modules', os.path.basename(module_info['file'])), 200

@app.route('/versions/<module_name>', methods=['GET'])
def get_versions(module_name):
    module_infos = get_module_info(module_name)
    if not module_infos:
        return 'Module not found.', 404
    versions = [info['version'] for info in module_infos]
    return jsonify(versions)

if __name__ == '__main__':
    load_modules_database()
    app.run(debug=True)
