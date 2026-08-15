import json
from pathlib import Path
import os

from fs_tools import list_files, read_file, search_in_file, write_file
from llm_file_assistant import LLMFileAssistant


def run_demo(resumes_dir: str | None = None, keyword: str = "Python"):
    resumes_dir = resumes_dir or os.environ.get("RESUMES_DIR", "resumes")
    d = Path(resumes_dir)
    if not d.exists():
        print(f"Resumes folder not found: {resumes_dir}")
        return

    assistant = LLMFileAssistant()
    files = list_files(str(resumes_dir))
    resumes = [f for f in files if f["name"].lower().endswith((".pdf", ".docx", ".txt"))]
    print(f"Found {len(resumes)} resume(s) in {resumes_dir}: {[r['name'] for r in resumes]}")

    results = []
    for r in resumes:
        path = r["path"]
        print('\n---')
        print(f"Reading: {r['name']}")
        read = read_file(path)
        if read.get("status") != "success":
            print("Read failed:", read.get("error"))
            continue

        parsed = read.get("parsed", {})
        print("Parsed:", json.dumps(parsed, indent=2))
        print("Excerpt:\n", read.get("content", "")[0:400])

        print(f"Searching for keyword '{keyword}'...")
        s = search_in_file(path, keyword)
        print(f"Matches: {s.get('count',0)}")

        # Summarize and write summary file
        summary = assistant.summarize(read.get("content", ""))
        out_name = Path(path).with_name(f"summary_{Path(path).stem}.txt")
        w = write_file(str(out_name), summary)
        print(f"Wrote summary to: {out_name} (status: {w.get('status')})")

        results.append({"file": r, "parsed": parsed, "search": s, "summary_path": str(out_name)})

    print('\nDemo results:\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    run_demo()
