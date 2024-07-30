import os
from collections import Counter

def check_gitignore():
    project_type = False
    if os.path.isfile(".gitignore"):
        with open(".gitignore", "r") as f:
            file = f.read()
        if '__pycache__' in file:
            project_type = 'python'
        elif 'node_modules' in file:
            project_type = 'node'
        elif '*.sh~' in file:
            project_type = 'bash'
        elif '*.class' in file:
            project_type = 'java'
        elif '*.exe' in file:
            project_type = 'cpp'
    return project_type

def check_file_extensions():
    extension_map = {
        '.py': 'python',
        '.js': 'node',
        '.sh': 'bash',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'cpp',
        '.h': 'cpp',
        '.hpp': 'cpp'
    }
    
    file_extensions = Counter()
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in extension_map:
                file_extensions[extension_map[ext]] += 1
    
    if file_extensions:
        return file_extensions.most_common(1)[0][0]
    else:
        return False
    
def determine_project_type():
    project_type = check_gitignore()
    if not project_type:
        project_type = check_file_extensions()
    return project_type