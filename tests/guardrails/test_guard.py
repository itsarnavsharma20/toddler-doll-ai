"""Tests for scripts/guardrails/guard.py. Sends fake tool calls, checks exit codes.

Run: python tests/guardrails/test_guard.py
Nothing real is executed. guard.py only reads the JSON and decides.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "guardrails" / "guard.py"
MEMORY = Path.home() / ".claude" / "projects" / "c--Users-Arnav-Documents-AI-Project-AIToy" / "memory" / "x.md"


def run(payload, raw=None):
    data = raw if raw is not None else json.dumps(payload)
    r = subprocess.run([sys.executable, "-I", str(GUARD)], input=data, capture_output=True, text=True)
    return r.returncode


def sh(cmd, tool="Bash"):
    return {"tool_name": tool, "tool_input": {"command": cmd}, "cwd": str(ROOT)}


def tool(name, **inp):
    return {"tool_name": name, "tool_input": inp, "cwd": str(ROOT)}


BLOCK = [
    ("git status", sh("git status")),
    ("gh pr list", sh("gh pr list")),
    ("git push (PowerShell)", sh("git push origin main", "PowerShell")),
    ("git after &&", sh("echo hi && git add .")),
    ("rm -rf", sh("rm -rf build")),
    ("Remove-Item", sh("Remove-Item foo.txt", "PowerShell")),
    ("del", sh("del a.txt", "PowerShell")),
    ("find -delete", sh("find . -name x -delete")),
    ("python rmtree", sh("python script.py && echo shutil.rmtree")),
    ("inline python", sh("python -c \"print(1)\"")),
    ("encoded command", sh("powershell -EncodedCommand AAAA", "PowerShell")),
    ("sqlite3 client", sh("sqlite3 data.db")),
    ("DELETE FROM", sh("echo DELETE FROM users")),
    ("DROP TABLE", sh("echo drop table users")),
    ("parent folder", sh("cat ../secret.txt")),
    ("windows abs outside", sh("type C:\\Windows\\win.ini", "PowerShell")),
    ("home tilde", sh("ls ~/")),
    ("TEMP env", sh("dir $env:TEMP", "PowerShell")),
    ("read .env in shell", sh("cat .env")),
    ("Read outside", tool("Read", file_path="C:\\Windows\\win.ini")),
    ("Read .env", tool("Read", file_path=str(ROOT / ".env"))),
    ("Read .env.local", tool("Read", file_path=str(ROOT / ".env.local"))),
    ("Write guard.py", tool("Write", file_path=str(GUARD), content="x")),
    ("Edit settings", tool("Edit", file_path=str(ROOT / ".claude" / "settings.json"))),
    ("shell touches guardrails", sh("echo x > scripts/guardrails/guard.py")),
    ("Write db file", tool("Write", file_path=str(ROOT / "data.sqlite"), content="x")),
    ("delete tool by name", tool("mcp__x__delete_project", id="1")),
    ("delete action", tool("Artifact", action="delete", url="u")),
    ("delete in batch", tool("ArtifactData", action="batch", batch=[{"op": "delete"}])),
    ("bad json fails closed", None),
    ("antigravity shell git", {"toolCall": {"name": "run_command", "args": {"CommandLine": "git status", "Cwd": str(ROOT)}}}),
    ("antigravity write outside", {"toolCall": {"name": "write_to_file", "args": {"TargetFile": "C:\\Windows\\x.txt"}}}),
    ("grok shell delete", {"toolName": "run_terminal_command", "toolInput": {"command": "rm -rf x"}, "cwd": str(ROOT)}),
    ("codex patch delete file", tool("apply_patch", command="*** Begin Patch\n*** Delete File: a.txt\n*** End Patch")),
    ("codex patch outside", tool("apply_patch", command="*** Begin Patch\n*** Add File: C:\\Windows\\a.txt\n+x\n*** End Patch")),
    ("codex patch protected", tool("apply_patch", command="*** Begin Patch\n*** Update File: scripts/guardrails/guard.py\n+x\n*** End Patch")),
    ("cursor shell event", {"command": "git push", "cwd": str(ROOT)}),
    ("cursor read event outside", {"file_path": "C:\\Windows\\win.ini", "content": "x"}),
    ("gemini shell delete", {"tool_name": "run_shell_command", "tool_input": {"command": "del x"}, "cwd": str(ROOT)}),
    ("gemini write protected", tool("write_file", file_path=str(ROOT / ".gemini" / "settings.json"), content="x")),
    ("cwd outside project", {"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": "C:\\Windows"}),
]

# These only block while the owner has NOT created .guardrails_unlock.
NEEDS_LOCK = {"Write guard.py", "Edit settings", "shell touches guardrails", "codex patch protected", "gemini write protected"}

ALLOW = [
    ("python app", sh("python app.py")),
    ("list dir", sh("ls")),
    ("pip install", sh("pip install fastapi")),
    ("cat .env.example", sh("cat .env.example")),
    ("cat .gitignore", sh("cat .gitignore")),
    ("word digital", sh("echo digital")),
    ("root path with spaces", sh('dir "%s\\data"' % ROOT, "PowerShell")),
    ("Read README", tool("Read", file_path=str(ROOT / "README.md"))),
    ("Read guard.py", tool("Read", file_path=str(GUARD))),
    ("Write tests file", tool("Write", file_path=str(ROOT / "tests" / "unit" / "new_test.py"), content="x")),
    ("Write memory file", tool("Write", file_path=str(MEMORY), content="x")),
    ("Glob in project", tool("Glob", pattern="*.md", path=str(ROOT))),
    ("remove_background tool", tool("mcp__x__remove_background", id="1")),
    ("Artifact publish", tool("Artifact", action="publish", file_path=str(ROOT / "README.md"))),
    ("codex patch ok (text has git)", tool("apply_patch", command="*** Begin Patch\n*** Add File: tests/a.py\n+git status\n*** End Patch")),
    ("antigravity python", {"toolCall": {"name": "run_command", "args": {"CommandLine": "python app.py", "Cwd": str(ROOT)}}}),
    ("grok python", {"toolName": "run_terminal_command", "toolInput": {"command": "python app.py"}, "cwd": str(ROOT)}),
    ("gemini read in project", {"tool_name": "read_file", "tool_input": {"file_path": str(ROOT / "README.md")}, "cwd": str(ROOT)}),
    ("cursor shell event ok", {"command": "python app.py", "cwd": str(ROOT)}),
]


def main():
    failed = 0
    unlocked = (ROOT / ".guardrails_unlock").exists()
    if unlocked:
        print("NOTE: .guardrails_unlock exists. Protected-file tests are skipped.\n")
    for label, payload in BLOCK:
        if unlocked and label in NEEDS_LOCK:
            print("SKIP  should block : %s" % label)
            continue
        code = run(payload, raw="not json" if payload is None else None)
        ok = code == 2
        failed += not ok
        print("%s  should block : %s (exit %s)" % ("PASS" if ok else "FAIL", label, code))
    for label, payload in ALLOW:
        code = run(payload)
        ok = code == 0
        failed += not ok
        print("%s  should allow : %s (exit %s)" % ("PASS" if ok else "FAIL", label, code))
    total = len(BLOCK) + len(ALLOW) - (len(NEEDS_LOCK) if unlocked else 0)
    print("\n%d of %d passed" % (total - failed, total))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
