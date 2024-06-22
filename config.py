import re

# Prompt for new values
secretkey = input("Database secret key: ")
database_uri = input("Database URI: ")

# File path
backend_file = 'backend.py'

# Regular expressions to match the lines to be replaced
secret_key_pattern = r"(app\.config\['SECRET_KEY'\]\s*=\s*)'.*'"
database_uri_pattern = r"(app\.config\['SQLALCHEMY_DATABASE_URI'\]\s*=\s*)'.*'"

# Read the content of backend.py
with open(backend_file, 'r') as file:
    content = file.read()

# Replace the old values with the new ones
content = re.sub(secret_key_pattern, rf"\1'{secretkey}'", content)
content = re.sub(database_uri_pattern, rf"\1'{database_uri}'", content)

# Write the updated content back to backend.py
with open(backend_file, 'w') as file:
    file.write(content)

print(f"{backend_file} has been updated successfully.")
