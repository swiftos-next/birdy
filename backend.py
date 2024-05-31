import os
import json
import re
from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///packages.db'
allowed_package_names = re.compile(r'^[A-Za-z0-9]*$')
modules_databse = {}
db = SQLAlchemy(app)

def save_package_info(package_info):
    package = Package(
        name=package_info['name'],
        author=package_info['author'],
        description=package_info['description'],
        version=package_info['version'],
        file=package_info['file'],
        downloads=package_info['downloads'],
        verified=package_info['verified']
    )
    db.session.add(package)
    db.session.commit()


def get_package_info(package_name, package_version=None):
    if package_version:
        return Package.query.filter_by(name=package_name, version=package_version).first()
    else:
        return Package.query.filter_by(name=package_name).all()


def update_package_info(package_name, package_version, package_info):
    package = Package.query.filter_by(
        name=package_name, version=package_version).first()
    if package:
        package.author = package_info['author']
        package.description = package_info['description']
        package.file = package_info['file']
        package.downloads = package_info['downloads']
        package.verified = package_info['verified']
        db.session.commit()


@app.route('/publish', methods=['POST'])
def publish_package():
    data = json.loads(request.form.get('json'))
    if allowed_package_names.match(data['name']):
        package_info = {
            'name': data['name'],
            'author': data['AuthorName'],
            'description': data['description'],
            'version': data['version'],
            'file': secure_filename(request.files['file'].filename),
            'downloads': 0,
            'verified': False
        }

        file = request.files['file']
        file_path = f"{os.path.join(
            'db/packages')}/{secure_filename(file.filename)}-{package_info['version']}"
        file.save(file_path)
        package_info['file'] = file_path

        save_package_info(package_info)

        return 'Package published successfully!', 200
    return 'Invalid package name', 400


@app.route('/packages/<package_name>-<package_version>', methods=['GET'])
def install_package(package_name, package_version):
    package_info = get_package_info(package_name, package_version)

    if package_info is None:
        return 'Package not found.', 404

    package_info.downloads += 1
    db.session.commit()

    return send_from_directory('db/packages', os.path.basename(package_info.file)), 200


@app.route('/versions/<package_name>', methods=['GET'])
def get_versions(package_name):
    package_infos = get_package_info(package_name)
    if not package_infos:
        return 'Package not found.', 404
    versions = [info.version for info in package_infos]
    return jsonify(versions)


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), nullable=False)
    file = db.Column(db.String(120), nullable=False)
    downloads = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint(
        'name', 'version', name='_name_version_uc'),)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
