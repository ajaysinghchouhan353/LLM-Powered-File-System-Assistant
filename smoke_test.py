import json
import shutil
from pathlib import Path

from fs_tools import list_files, read_file, search_in_file, write_file


def run():
    root = Path("resumes_test")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()

    # write a sample resume
    sample = """
John Doe
Experienced Python developer with 5 years of experience.
Skills: Python, Django, Flask, SQL
"""
    path = root / "resume_john_doe.txt"
    w = write_file(str(path), sample)

    listed = list_files(str(root))
    r = read_file(str(path))
    s = search_in_file(str(path), "python")

    out = {"write": w, "listed": listed, "read": r, "search": s}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    run()
