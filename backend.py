import os
import json
import re
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

modules_database = {}
allowed_package_names = re.compile(r'^[A-Za-z0-9]*$')

def save_module_info(module_info):
    global modules_database
    modules_database[module_info['name']] = module_info

def get_module_info(module_name):
    global modules_database
    return modules_database.get(module_name)

def update_module_info(module_name, module_info):
    global modules_database
    modules_database[module_name] = module_info

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
        file.save(f"{os.path.join("db/modules/")}{secure_filename(file.filename)}-{module_info['version']}")

        save_module_info(module_info)

        return 'Module published successfully!', 200
    return 'Invalid package name', 400

@app.route('/install/<module_name>', methods=['GET'])
def install_module(module_name):
    module_info = get_module_info(module_name)

    if module_info is None:
        return 'Module not found.', 404

    module_info['downloads'] += 1

    update_module_info(module_name, module_info)

    return send_from_directory('db/modules', module_info['file']), 200

@app.route('/versions/<module_name>', methods=['GET'])
def get_versions(module_name):
    module_info = get_module_info(module_name)
    if module_info is None:
        return 'Module not found.', 404
    versions = [info['version'] for info in modules_database.values() if info['name'] == module_name]
    return jsonify(versions)

if __name__ == '__main__':
    app.run(debug=True)
