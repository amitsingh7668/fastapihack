GITLAB_TOKEN = ""
GITLAB_PROJECT_ID = "71395662"  # e.g., "java"

# GITLAB_PROJECT_ID = "71395662"  # e.g., "12345678" python

GITLAB_API_BASE = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}"
HEADERS = {"PRIVATE-TOKEN": GITLAB_TOKEN}
BRANCH = 'master'
AI_TOKEN = ""


import requests
import ast
import os
import re
import xml.etree.ElementTree as ET
import json
from urllib.parse import quote
from collections import Counter


def get_repo_tree():
    url = f"{GITLAB_API_BASE}/repository/tree?recursive=true&per_page=1000"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


def get_file_content(file_path):
    url = f"{GITLAB_API_BASE}/repository/files/{quote(file_path, safe='')}/raw?ref=master"
    res = requests.get(url, headers=HEADERS)
    return res.text if res.status_code == 200 else None


def detect_main_language(files):
    ext_count = Counter(os.path.splitext(f["path"])[1] for f in files if f["type"] == "blob")
    if ext_count[".py"] >= ext_count[".java"]:
        return "python"
    elif ext_count[".java"] > ext_count[".py"]:
        return "java"
    return "unknown"


def extract_python_info(code):
    try:
        tree = ast.parse(code)
        classes, functions, variables, imports = [], [], [], []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in getattr(node, 'names', []):
                    imports.append(alias.name)

        return {
            "classes": classes,
            "functions": functions,
            "variables": variables,
            "imports": list(set(imports))
        }
    except Exception as e:
        return {"error": str(e)}


def extract_java_info(code):
    classes = re.findall(r'\bclass\s+(\w+)', code)
    functions = re.findall(r'(?:public|private|protected)?\s+\w+\s+(\w+)\s*\(.*?\)\s*{', code)
    variables = re.findall(r'\b(?:int|String|float|double|boolean|char)\s+(\w+)\s*[=;]', code)
    imports = re.findall(r'import\s+([\w.]+);', code)

    return {
        "classes": classes,
        "functions": functions,
        "variables": variables,
        "imports": list(set(imports))
    }


def extract_python_dependencies(content):
    return [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]


import xml.etree.ElementTree as ET

def extract_maven_dependencies(content):
    try:
        root = ET.fromstring(content)
        # Extract namespace from root tag (e.g. "{namespace}project")
        ns = {'mvn': root.tag.split('}')[0].strip('{')}
        deps = []
        # Use namespace prefix in XPath
        for dep in root.findall(".//mvn:dependency", namespaces=ns):
            group = dep.find("mvn:groupId", namespaces=ns)
            artifact = dep.find("mvn:artifactId", namespaces=ns)
            version = dep.find("mvn:version", namespaces=ns)
            
            group_text = group.text if group is not None else ""
            artifact_text = artifact.text if artifact is not None else ""
            version_text = version.text if version is not None else ""

            deps.append(f"{group_text}:{artifact_text}:{version_text}")
        
        return deps

    except Exception as e:
        return [f"Error parsing pom.xml: {e}"]



def extract_gradle_dependencies(content):
    return re.findall(r"implementation\s+['\"]([\w\-.:]+)['\"]", content)


def find_file(files, filename):
    for f in files:
        if f["path"].endswith(filename):
            return f["path"]
    return None


def is_test_file(path):
    """Check if file is in a test folder"""
    return any(part.lower() in ["test", "tests", "__tests__"] for part in path.split("/"))


def main():
    files = get_repo_tree()
    language = detect_main_language(files)

    repo_model = {
        "project_metadata": {
            "language": language,
            "dependencies": []
        },
        "files": []
    }

    # Filter source files only (skip test folders)
    source_files = [
        f for f in files
        if f["type"] == "blob" and not is_test_file(f["path"])
    ]

    for f in source_files:
        path = f["path"]
        print(f"Processing file: {path}")
        content = get_file_content(path)
        if content is None:
            print(f"❌ Failed to fetch content for {path}")
            continue
        if not content:
            continue

        file_data = {
            "file_path": path,
            "language": language,
            "classes": [],
            "functions": [],
            "variables": [],
            "imports": []
        }

        if language == "python" and path.endswith(".py"):
            info = extract_python_info(content)
            file_data.update(info)
            repo_model["files"].append(file_data)

        elif language == "java" and path.endswith(".java"):
            # extension = path.split(".")[-1]
            file_data["file_path"] = path.split("/")[-1]
            info = extract_java_info(content)
            file_data.update(info)
            repo_model["files"].append(file_data)

    # Extract dependency list
    if language == "python":
        req_path = find_file(files, "requirements.txt")
        if req_path:
            content = get_file_content(req_path)
            if content:
                repo_model["project_metadata"]["dependencies"] = extract_python_dependencies(content)

    elif language == "java":
        pom_path = find_file(files, "pom.xml")
        gradle_path = find_file(files, "build.gradle")

        if pom_path:
            content = get_file_content(pom_path)
            if content:
                repo_model["project_metadata"]["dependencies"] = extract_maven_dependencies(content)

        elif gradle_path:
            content = get_file_content(gradle_path)
            if content:
                repo_model["project_metadata"]["dependencies"] = extract_gradle_dependencies(content)

    # Save results
    with open("repo_metadata.json", "w") as f:
        json.dump(repo_model, f, indent=2)
    print("✅ Metadata extraction complete! Saved to repo_metadata.json")
    return repo_model
    

def setup_handler(GITLAB_TOKEN1,GITLAB_PROJECT_ID1):
    global GITLAB_TOKEN, GITLAB_PROJECT_ID, GITLAB_API_BASE, HEADERS, BRANCH, AI_TOKEN
    GITLAB_TOKEN = GITLAB_TOKEN1
    GITLAB_PROJECT_ID = GITLAB_PROJECT_ID1
    GITLAB_API_BASE = f"https://gitlab.com/api/v4/projects/{GITLAB_PROJECT_ID}"
    HEADERS = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    BRANCH = 'master'
    AI_TOKEN = ""
    return main()



if __name__ == "__main__":
    main()
