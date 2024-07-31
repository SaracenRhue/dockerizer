import os
import re
import json

with open('config.json', 'r') as f:
    CONFIGS = json.load(f)


def detect_volumes():
    common_volume_dirs = ['data', 'logs', 'config', 'uploads', 'media', 'static', 'db']
    existing_volume_dirs = [f"/project/{dir}" for dir in common_volume_dirs if os.path.exists(dir)]
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

    for root, _, files in os.walk('/project/'):
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

    if project_type == 'python':
        third_party_imports = check_python_imports()
        if third_party_imports and not os.path.exists('/project/requirements.txt'):
            with open('/project/requirements.txt', 'w') as f:
                for module in third_party_imports:
                    f.write(f"{module}\n")
            print("requirements.txt created.")
        if 'torch' in third_party_imports or 'tensorflow' in third_party_imports:
            project_type == 'python-cuda'
        elif 'flask' in third_party_imports:
            project_type = 'python-flask'
        elif 'streamlit' in third_party_imports:
            project_type = 'python-streamlit'
        elif 'gradio' in third_party_imports:
            project_type = 'python-gradio'

        dockerfile_content = dockerfile_content.replace(CONFIGS['python']['base_image'], CONFIGS[project_type]['base_image'])
        if 'run' in CONFIGS[project_type]:
            "RUN "+' && '.join(CONFIGS[project_type]['run'])+'\n\n'

        if os.path.exists('requirements.txt'):
            dockerfile_content += "RUN pip install --no-cache-dir -r requirements.txt\n\n"
        if volumes:
            dockerfile_content += "VOLUME "+str(volumes).replace("'", '"')+"\n\n"
        if 'port' in CONFIGS[project_type]:
           dockerfile_content += f"EXPOSE {CONFIGS[project_type]['port']}\n\n" 
        if 'cmd' in CONFIGS[project_type]:
            dockerfile_content += "CMD "+str(CONFIGS[project_type]['cmd']).replace("'", '"')
        
    if 'python' not in project_type:
        if volumes:
            dockerfile_content += "VOLUME "+str(volumes).replace("'", '"')+"\n\n"
        if 'run' in CONFIGS[project_type]:
            dockerfile_content += "RUN "+' && '.join(CONFIGS[project_type]['run'])+'\n\n'
        if 'port' in CONFIGS[project_type]:
           dockerfile_content += f"EXPOSE {CONFIGS[project_type]['port']}\n\n" 
        if 'cmd' in CONFIGS[project_type]:
            dockerfile_content += "CMD "+str(CONFIGS[project_type]['cmd']).replace("'", '"')

    with open('/project/Dockerfile', 'w') as f:
        f.write(dockerfile_content)


def create_dockerignore(project_type):
    ignore_list = CONFIGS['ignore']
    if project_type in CONFIGS and 'ignore' in CONFIGS[project_type]:
        ignore_list.extend(CONFIGS[project_type]['ignore'])

    with open('/project/.dockerignore', 'w') as f:
        f.write('\n'.join(ignore_list))
