import os
import json
import re
from flask import Flask, request, send_from_directory, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///packages.db'
app.config['SECRET_KEY'] = 'changeme'
allowed_package_names = re.compile(r'^[A-Za-z0-9]*$')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = generate_password_hash(data['password'])
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return 'User registered successfully', 201

@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return 'Logged in successfully', 200
    return 'Invalid credentials', 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out successfully', 200

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
@login_required
def publish_package():
    data = json.loads(request.form.get('json'))
    if allowed_package_names.match(data['name']):
        package_info = get_package_info(data['name'])
        if package_info:
            original_owner = package_info[0].author
            if original_owner == current_user.username:
                new_version = data['version']
                existing_versions = [package.version for package in package_info]
                if new_version not in existing_versions:
                    package_data = {
                        'name': data['name'],
                        'author': current_user.username,
                        'description': data['description'],
                        'version': new_version,
                        'file': secure_filename(request.files['file'].filename),
                        'downloads': 0,
                        'verified': False
                    }
                    file = request.files['file']
                    file_path = os.path.join('db/packages', secure_filename(f"{data['name']}-{new_version}"))
                    file.save(file_path)
                    package_data['file'] = file_path
                    save_package_info(package_data)
                    return 'Package published successfully!', 200
                else:
                    return f'Version {new_version} already exists for {data["name"]}.', 400
            else:
                return f'You are not the original owner of {data["name"]}.', 401
        else:
            return f'Package {data["name"]} does not exist.', 404
    else:
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

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
