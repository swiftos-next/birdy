import os
import json
import re
from flask import Flask, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///packages.db'
# Change this by running config.py
app.config['SECRET_KEY'] = 'changeme'
allow_registration = False
allow_publishing = True

# Compile regex for allowed package names
allowed_package_names = re.compile(r'^[A-Za-z0-9]*$')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Package model
class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), nullable=False)
    file = db.Column(db.String(120), nullable=False)
    dependencies = db.Column(db.JSON, nullable=False, default=[])

    __table_args__ = (db.UniqueConstraint(
        'name', 'version', name='_name_version_uc'),)

# Load user by ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if allow_registration:
    # User registration route
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        username = data['username']
        password = generate_password_hash(data['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return 'User registered successfully', 201
else:
    @app.route('/register', methods=['POST'])
    def register():
        return "Registration is disabled on this server."

# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return 'Logged in successfully', 200
    return 'Invalid credentials', 401

# User logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out successfully', 200

# Save package information
def save_package_info(package_info):
    package = Package(
        name=package_info['name'],
        author=package_info['author'],
        description=package_info['description'],
        version=package_info['version'],
        file=package_info['file'],
        dependencies=package_info['dependencies']
    )
    db.session.add(package)
    db.session.commit()

# Get package information
def get_package_info(package_name, package_version=None):
    if package_version:
        return Package.query.filter_by(name=package_name, version=package_version).first()
    else:
        return Package.query.filter_by(name=package_name).all()

# Update package information
def update_package_info(package_name, package_version, package_info):
    package = Package.query.filter_by(
        name=package_name, version=package_version).first()
    if package:
        package.author = package_info['author']
        package.description = package_info['description']
        package.file = package_info['file']
        package.dependencies = package_info['dependencies']
        db.session.commit()

if allow_publishing:
    # Publish a package
    @app.route('/publish', methods=['POST'])
    @login_required
    def publish_package():
        data = json.loads(request.form.get('json'))
        if allowed_package_names.match(data['name']):
            # Check if the current user is the original owner of the package or if the package doesn't exist
            package_info_list = get_package_info(data['name'])
            if not package_info_list:
                # No existing package with this name
                package_info = None
            else:
                # Check if the current user is the author of the package
                package_info = next((pkg for pkg in package_info_list if pkg.author == current_user.username), None)
            
            if not package_info:
                new_version = data['version']
                # Check if the new version is greater than the existing ones
                if not package_info_list or new_version > max([pkg.version for pkg in package_info_list]):
                    package_data = {
                        'name': data['name'],
                        'author': current_user.username,
                        'description': data['description'],
                        'version': new_version,
                        'file': secure_filename(request.files['file'].filename),
                        'dependencies': data.get('dependencies', [])
                    }
                    # Save the uploaded file
                    file = request.files['file']
                    file_path = os.path.join('packages', secure_filename(f"{data['name']}/{new_version}"))
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    package_data['file'] = file_path
                    save_package_info(package_data)
                    return 'Package published successfully!', 200
                else:
                    return f'Version {new_version} already exists for {data["name"]}.', 400
            else:
                return f'You are not the original owner of {data["name"]}.', 401
        else:
            return 'Invalid package name', 400
else:
    @app.route('/publish', methods=['POST'])
    def publish_package():
        return "Publishing is disabled on this server."

# Install a package
@app.route('/packages/<package_name>-<package_version>.tar.xz', methods=['GET'])
def install_package(package_name, package_version):
    package_info = get_package_info(package_name, package_version)

    if package_info is None:
        return 'Package not found.', 404

    package_file_path = package_info.file
    return send_from_directory(app.root_path, package_file_path), 200

# Function to fetch the latest version of a package
def fetch_latest_version(name):
    latest_version = Package.query.filter_by(name=name).order_by(Package.version.desc()).first()
    if latest_version:
        return latest_version.version
    return None

# Get package info as JSON
@app.route('/packages/<package_name>/<package_version>.json', methods=['GET'])
@app.route('/packages/<package_name>.json', methods=['GET'])
def get_package_info_json(package_name, package_version=None):
    if package_version is None:
        package_version = fetch_latest_version(package_name)
    package_info = get_package_info(package_name, package_version)
    if not package_info:
        return jsonify({'error': 'Package not found.'}), 404
    
    package_data = {
        'name': package_info.name,
        'author': package_info.author,
        'description': package_info.description,
        'version': package_info.version,
        'file': package_info.file,
        'dependencies': package_info.dependencies
    }
    return jsonify(package_data), 200

# Create all tables
with app.app_context():
    db.create_all()

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
