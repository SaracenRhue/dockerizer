import type_checks
import create_files


project_type = type_checks.determine_project_type()
if project_type:
    print(f"Detected project type: {project_type}")
    create_files.create_dockerfile(project_type)
    create_files.create_dockerignore(project_type)
    print("Dockerfile and .dockerignore created successfully.")
else:
    print("Unable to determine project type.")

