# LLM-Powered File System Assistant

Setup OpenAI API key (one of the options):

- Export env var in your shell (temporary):

```powershell
$env:OPENAI_API_KEY = "sk-..."
python llm_file_assistant.py --test-openai
```

- Or create a `.env` file in the project root with:

```
OPENAI_API_KEY=sk-...
```

Then you can call the assistant:

```powershell
python llm_file_assistant.py "Read all resumes in the resumes folder"
python llm_file_assistant.py "Find resumes mentioning Python"
python llm_file_assistant.py "Create a summary file for resume_john_doe.txt"
```

To persist a key into `.env` from CLI (writes .env):

```powershell
python llm_file_assistant.py --set-key sk-... --persist-key
```
# LLM-Powered-File-System-Assistant