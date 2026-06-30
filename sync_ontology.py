import yaml
import subprocess
import os

with open("cortex-ontology.yaml", "r") as f:
    data = yaml.safe_load(f)

for repo in data.get("repositories", []):
    name = repo["name"]
    desc = repo.get("description", "")
    has_issues = str(repo.get("has_issues", True)).lower()
    
    cmd = [
        "gh", "repo", "edit", f"borjamoskv/{name}",
        "-d", desc,
        "--enable-issues=" + has_issues
    ]
    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[C5-REAL] Successfully synced metadata for {name}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to sync {name}: {e}")
