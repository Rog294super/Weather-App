# Module for handling file operations
# For use in file management tasks
# Finding type of file content
# Reading file content
# Writing file content
# creating a new file
# Error handling
# searching for specific content
# Able to add options to file operations


# variables
import os
import json

# variables config
config_json = "config.json"

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found"
    except Exception as err:
        print(f"There was an error {err}")

# This will delete the content of the file
def write_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
            return True
    except Exception as err:
        print(f"There was an error {err}")

def append_to_file(file_path, content):
    try:
        with open(file_path, 'a') as file:
            file.write(content)
            return True
    except Exception as err:
        print(f"There was an error {err}")

# creating a new file
# When returns true file is created
# If file already exists returns false
# If there is an error returns the error message
def create_file(file_path):
    try:
        with open(file_path, 'x') as file:
            file.write('')
            return True
    except FileExistsError:
        return False
    except Exception as err:
        print(f"There was an error {err}")

def get_file_type(file_path):
    content = read_file(file_path)
    if content.startswith('{') and content.endswith('}'):
        return 'JSON'
    elif content.startswith('<') and content.endswith('>'):
        return 'XML'
    elif content.startswith('[') and content.endswith(']'):
        return 'YAML'
    elif content.startswith('---') and content.endswith('---'):
        return 'MARKDOWN'
    elif content.startswith('```') and content.endswith('```'):
        return 'CODE'
    elif content.startswith('#') and content.endswith('#'):
        return 'HEADING'
    elif content.startswith('>') and content.endswith('<'):
        return 'BLOCKQUOTE'
    elif content.startswith('![') and content.endswith(']'):
        return 'IMAGE'
    elif content.startswith('[') and content.endswith(']'):
        return 'LINK'
    elif content.startswith('*') and content.endswith('*'):
        return 'BOLD'
    else:
        return 'TEXT'

def search_content(file_path, search_term):
    content = read_file(file_path)
    if search_term in content:
        return True
    return False


def config_load(config_json):
    if os.path.exists(config_json):
        try:
            with open(config_json, "r") as file:
                config = json.load(file)
                debug = config.get("debug", False)
                return debug
        except json.JSONDecodeError:
            print("⚠️ Ongeldig JSON-bestand gevonden. Herstellen naar standaardwaarden.")
    else:
        print("ℹ️ Geen config.json gevonden. Er wordt een nieuwe aangemaakt met standaardwaarden.")

    config = {
        "debug": False
        }
    
    with open(config_json, "w") as file:
        json.dump(config, file, indent=4)
    return False

def config_save(config_json, debug=False):
    config = {
        "debug": debug
    }
    with open(config_json, "w") as file:
        json.dump(config, file, indent=4)

def update_debug(config_json, debug_enabled):
    """Update debug setting"""
    config_loaded = config_load(config_json)
    config_save(config_json, debug_enabled)
