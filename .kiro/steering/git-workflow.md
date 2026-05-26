# Git Workflow Rules

## Testing Before Commits

**NEVER commit before tests pass.** Before creating any git commit, you MUST:

1. Run the full test suite: `source venv/bin/activate && arch -arm64 python3 -m pytest tests/ -q --ignore=tests/test_admin_dashboard.py --ignore=tests/test_chat_improvements.py --ignore=tests/test_pdn_agent_refactored.py --ignore=tests/test_voice_recording.py`
2. Verify 0 failures (or at most the known pre-existing failure threshold of 6)
3. If tests fail, fix them BEFORE committing
4. Only after all tests pass, proceed with `git add` and `git commit`

This is a hard rule — no exceptions, no `--no-verify`, no "commit now fix later".
