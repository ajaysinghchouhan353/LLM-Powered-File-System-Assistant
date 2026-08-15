import os
import re
from typing import List, Dict, Any

from fs_tools import list_files, read_file, search_in_file, write_file

try:
    from dotenv import load_dotenv, find_dotenv, set_key
    _have_dotenv = True
except Exception:
    _have_dotenv = False
    def load_dotenv():
        return False
    def find_dotenv(create=False):
        # return project .env path
        return ".env"
    def set_key(path, key, value):
        # simple fallback: append or replace in .env
        try:
            lines = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as fh:
                    lines = fh.read().splitlines()
            found = False
            for i, ln in enumerate(lines):
                if ln.startswith(key + "="):
                    lines[i] = f"{key}={value}"
                    found = True
                    break
            if not found:
                lines.append(f"{key}={value}")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            return True
        except Exception:
            return False

# Load .env if present
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
_have_openai = False
try:
    if OPENAI_API_KEY:
        import openai
        openai.api_key = OPENAI_API_KEY
        _have_openai = True
except Exception:
    _have_openai = False


def set_openai_key(key: str, persist: bool = False) -> dict:
    """Set OpenAI API key in the environment. If persist=True, write to a .env file."""
    os.environ["OPENAI_API_KEY"] = key
    result = {"status": "ok", "in_memory": True}
    if persist:
        env_path = find_dotenv(create=True)
        try:
            set_key(env_path, "OPENAI_API_KEY", key)
            result["persisted_to"] = env_path
        except Exception as e:
            result = {"status": "error", "error": str(e)}
    return result


def _summarize_with_openai(text: str) -> str:
    if not _have_openai:
        return "(OpenAI not configured)"
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Summarize the following resume in 3 bullet points:\n\n" + text}],
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return "(failed to call OpenAI: {})".format(e)


def _simple_summarize(text: str) -> str:
    # fallback summarizer: take first 3 non-empty lines or first 400 chars
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 3:
        return "\n".join(["- " + lines[i] for i in range(min(3, len(lines)))])
    return text[:400]


class LLMFileAssistant:
    def __init__(self):
        self.use_openai = _have_openai

    def summarize(self, text: str) -> str:
        if self.use_openai:
            return _summarize_with_openai(text)
        return _simple_summarize(text)

    def handle_query(self, query: str) -> Dict[str, Any]:
        q = query.strip().lower()
        # Read all resumes in a folder
        m = re.search(r"read all resumes in the (.+) folder", q)
        if m:
            folder = m.group(1)
            folder = folder.strip()
            files = list_files(folder)
            results = []
            for f in files:
                # only consider common resume extensions
                if f["name"].lower().endswith(('.pdf', '.docx', '.txt')):
                    r = read_file(f["path"])
                    results.append({"file": f, "read": r})
            return {"action": "read_all", "results": results}

        # Find resumes mentioning X
        m2 = re.search(r"find resumes mentioning ([\w+#+\- ]+)", q)
        if m2:
            keyword = m2.group(1).strip()
            # default to 'resumes' folder
            folder = "resumes"
            files = list_files(folder)
            found = []
            for f in files:
                if f["name"].lower().endswith(('.pdf', '.docx', '.txt')):
                    s = search_in_file(f["path"], keyword)
                    if s.get("count", 0) > 0:
                        found.append({"file": f, "matches": s})
            return {"action": "search", "keyword": keyword, "results": found}

        # Create a summary file for a given resume
        m3 = re.search(r"create a summary file for (.+)", q)
        if m3:
            filename = m3.group(1).strip()
            # accept either path or name
            if not os.path.exists(filename):
                # try in resumes folder
                candidate = os.path.join("resumes", filename)
            else:
                candidate = filename

            if not os.path.exists(candidate):
                return {"status": "error", "error": f"file not found: {candidate}"}

            r = read_file(candidate)
            if r.get("status") != "success":
                return {"status": "error", "error": "failed to read file", "detail": r}

            summary = self.summarize(r.get("content", ""))
            base = os.path.basename(candidate)
            out_name = f"summary_{os.path.splitext(base)[0]}.txt"
            out_path = os.path.join(os.path.dirname(candidate), out_name)
            w = write_file(out_path, summary)
            return {"action": "create_summary", "summary_path": out_path, "write_result": w}

        return {"status": "error", "error": "unrecognized query", "query": query}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # accept the remainder so users don't need to quote multi-word queries
    parser.add_argument("query", nargs=argparse.REMAINDER, help="User query for the assistant")
    parser.add_argument("--set-key", help="Set OpenAI API key (in-memory)")
    parser.add_argument("--persist-key", action="store_true", help="Persist the key to .env")
    parser.add_argument("--test-openai", action="store_true", help="Run a quick OpenAI summary test (requires key)")
    args = parser.parse_args()

    # join remainder tokens into a single query string when provided
    raw_query = None
    if args.query:
        if isinstance(args.query, list):
            raw_query = " ".join(args.query).strip()
        else:
            raw_query = args.query

    if args.set_key:
        res = set_openai_key(args.set_key, persist=args.persist_key)
        print(res)
        if args.test_openai:
            # refresh module-level state
            if args.set_key:
                try:
                    import openai
                    openai.api_key = os.environ.get("OPENAI_API_KEY")
                except Exception:
                    pass
            assistant = LLMFileAssistant()
            print(assistant.summarize("Experienced Python developer with data science and web backend experience."))
        exit(0)

    if raw_query:
        assistant = LLMFileAssistant()
        resp = assistant.handle_query(raw_query)
        print(resp)
    else:
        parser.print_help()
