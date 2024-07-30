import os
import re
from collections import Counter


CONFIGS = {
    'python': {
        'base_image': 'python:3.11-alpine',
        'ignore': ['__pycache__', '.venv']
    },
    'python-cuda': {
        'base_image': 'nvidia/cuda:12.5.1-cudnn-runtime-ubuntu20.04',
        'run': ['apt-get update', 'apt-get install -y python3.11 python-is-python3 pip', 'rm -rf /var/lib/apt/lists/*'],
        'ignore': ['__pycache__', '.venv']
    },
    'node': {
        'base_image': 'node:16-alpine',
        'ignore': ['node_modules']
    },
    'bash': {
        'base_image': 'bash:5.1-alpine'
    },
    'java': {
        'base_image': 'openjdk:17-alpine',
        'ignore': ['*.class', '*.jar', 'bin']
    },
    'cpp': {
        'base_image': 'gcc:latest',
        'ignore': ['*.exe', '*.dll', '*.o', '*.out', '*.a', '*.so', 'build']
    },
    'ignore': ['.DS Store', '.git', '.gitignore', '.vscode', 'LICENSE', 'README.md', 'Dockerfile', '.dockerinore', 'data', 'test*' 'tests*', 'venv', 'env', '.env', '.github', '.gitea', '.gitlab']
}

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

def detect_volumes():
    common_volume_dirs = ['data', 'logs', 'config', 'uploads', 'media', 'static', 'db']
    existing_volume_dirs = [f"/app/{dir}" for dir in common_volume_dirs if os.path.exists(dir)]
    return existing_volume_dirs if len(existing_volume_dirs) > 0 else False
            

def check_python_imports():
    standard_libs = set([
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'concurrent', 'contextlib',
        'copy', 'csv', 'datetime', 'enum', 'functools', 'glob', 'gzip', 'hashlib', 'http',
        'importlib', 'io', 'itertools', 'json', 'logging', 'math', 'multiprocessing', 'operator',
        'os', 'pathlib', 'pickle', 'random', 're', 'shutil', 'signal', 'socket', 'sqlite3',
        'statistics', 'string', 'subprocess', 'sys', 'tempfile', 'threading', 'time', 'typing',
        'unittest', 'urllib', 'uuid', 'warnings', 'weakref', 'xml', 'zipfile'
    ])

    imports = set()
    import_pattern = re.compile(r'^(?:from|import)\s+(\w+)')

    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        match = import_pattern.match(line.strip())
                        if match:
                            imports.add(match.group(1))

    third_party_imports = imports - standard_libs
    return sorted(third_party_imports)

def create_dockerfile(project_type):
    if project_type not in CONFIGS:
        print(f"Unsupported project type: {project_type}")
        return
    volumes = detect_volumes()
    config = CONFIGS[project_type]
    dockerfile_content = f"FROM {config['base_image']}\n\n"
    dockerfile_content += "WORKDIR /app\n\n"
    dockerfile_content += "COPY . .\n\n"
    if volumes:
        dockerfile_content += "RUN mkdir -p "+' '.join(volumes)+"\n\n"
    # env_file = ''
    # if os.path.exists('.env'):
    #     env_file = '.env'
    # if os.path.exists('env'):
    #     env_file = 'env'

    if project_type == 'python':
        third_party_imports = check_python_imports()
        if third_party_imports and not os.path.exists('requirements.txt'):
            with open('requirements.txt', 'w') as f:
                for module in third_party_imports:
                    f.write(f"{module}\n")
            print("requirements.txt created.")
        if 'torch' in third_party_imports or 'tensorflow' in third_party_imports:
            dockerfile_content = dockerfile_content.replace(CONFIGS['python']['base_image'], CONFIGS['python-cuda']['base_image'])
            run_commands = ' && '.join(CONFIGS['python-cuda']['run'])
            dockerfile_content += f"RUN {run_commands}\n\n"
        if os.path.exists('requirements.txt'):
            dockerfile_content += "RUN pip install --no-cache-dir -r requirements.txt\n\n"
        if 'gradio' in third_party_imports:
            if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
            dockerfile_content += 'EXPOSE 7860\n\n'
        if 'streamlit' in third_party_imports:
            if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
            dockerfile_content += 'EXPOSE 8501\n\n'
            dockerfile_content += 'CMD ["streamlit", "run", "app.py"]'
        if 'flask' in third_party_imports:
            if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
            dockerfile_content += 'EXPOSE 8080\n\n'
            dockerfile_content += 'CMD ["flask", "--app", "main", "run", "--host=0.0.0.0", "--port=8080"]'
        else:
            dockerfile_content += 'CMD ["python", "app.py"]'
    elif project_type == 'node':
        dockerfile_content += "RUN npm install\n\n"
        if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
        dockerfile_content += 'EXPOSE 3000\n\n'
        dockerfile_content += 'CMD ["node", "app.js"]'
    elif project_type == 'java':
        dockerfile_content += "RUN javac *.java\n\n"
        if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
        dockerfile_content += 'CMD ["java", "Main"]'
    elif project_type == 'cpp':
        dockerfile_content += "RUN g++ -o myapp *.cpp\n\n"
        if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
        dockerfile_content += 'CMD ["./myapp"]'
    elif project_type == 'bash':
        if volumes: dockerfile_content += f"VOLUME {volumes}\n\n"
        dockerfile_content += 'CMD ["bash", "script.sh"]'

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)


def create_dockerignore(project_type):
    ignore_list = CONFIGS['ignore']
    if project_type in CONFIGS and 'ignore' in CONFIGS[project_type]:
        ignore_list.extend(CONFIGS[project_type]['ignore'])

    with open('.dockerignore', 'w') as f:
        f.write('\n'.join(ignore_list))

def main():
    project_type = determine_project_type()
    if project_type:
        print(f"Detected project type: {project_type}")
        create_dockerfile(project_type)
        create_dockerignore(project_type)
        print("Dockerfile and .dockerignore created successfully.")
    else:
        print("Unable to determine project type.")

if __name__ == "__main__":
    main()
