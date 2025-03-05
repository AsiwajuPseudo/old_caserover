import os
import shutil

def create_dir(directory):
    try:
        # Check if the directory already exists
        if not os.path.exists(directory):
            # Create the directory
            os.makedirs(directory)
            return {"message":"Directory created successfully"}
        else:
            return {"message":"exist"}
    except Exception as e:
        return {"message":"error"}

def delete_dir(directory):
    try:
        # Check if the directory exists
        if os.path.exists(directory):
            # Delete the directory and all its contents
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(directory)
            return "Temporary folder deleted successifully"
        else:
            return "does not exist"
    except Exception as e:
        return "error"

def generate_tree(path):
    tree = []
    for root, dirs, files in os.walk(path):
        node = {
            'title': os.path.basename(root),
            'key': root,
            'children': []
        }
        # Add files
        file_nodes = [{'title': f, 'key': os.path.join(root, f)} for f in files]
        node['children'].extend(file_nodes)
        # Add subdirectories
        dir_nodes = [generate_tree(os.path.join(root, d)) for d in dirs]
        node['children'].extend(dir_nodes)
        tree.append(node)
    return tree

def get_dir(path):
    directories_with_files = []
    for root, dirs, files in os.walk(path):
        if files:
            d=root.replace('\\','/')
            directories_with_files.append({'normal':root,'new':d})
    return directories_with_files

def process_path(path):
    # Split the path by directory separator '/'
    components = path.split('/')
    
    # Extract the table name (second-to-last element) and category (last element)
    table = components[-2]
    category = components[-1]
    
    return table, category

def move_files(source, destination):
    files = os.listdir(source)

    # Move each file to the destination directory
    for file_name in files:
        source_path = os.path.join(source, file_name)
        destination_path = os.path.join(destination, file_name)
        shutil.move(source_path, destination_path)

def deli_file(file_path):
    directory_path, file_name = os.path.split(file_path)
    file_path = os.path.join(directory_path, file_name)
    _, table = os.path.split(directory_path)
    # Check if file exists
    if os.path.exists(file_path):
        os.remove(file_path)
        fil = os.path.splitext(file_name)[0]
        return table,fil
    else:
        fil = os.path.splitext(file_name)[0]
        return table,fil

def search_file(directory, filename):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith(filename):
                return os.path.join(root, file)

    return None