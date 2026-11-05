#!/usr/bin/env python3
"""Shared guardrail for AI coding tools.

Reads one tool call as JSON on stdin. Exit 0 = allow. Exit 2 = block
(reason on stderr and as JSON on stdout). Any error blocks the call (fail closed).

Usage: python guard.py [--format claude|cursor|codex|gemini|antigravity|grok]
The format only changes what is printed on allow. Input shapes are auto detected.

Rules enforced (see AGENTS.md, Hard Rules):
  - no git or gh commands
  - no delete of files or folders
  - no database clients, no destructive SQL, no database files
  - nothing outside the project folder
  - no secrets files (.env, keys)
  - guardrail files are protected unless the owner creates .guardrails_unlock
  - no inline code (python -c, node -e, encoded commands, iex) because it hides intent
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNLOCK_FILE = ROOT / ".guardrails_unlock"
LOG_FILE = ROOT / "logs" / "guardrails.log"

# Extra places agents may touch, outside the project. Keep this list tiny.
EXTRA_ALLOWED = [
    Path.home() / ".claude" / "projects" / "c--Users-Arnav-Documents-AI-Project-AIToy" / "memory",
]

PROTECTED = [
    "scripts/guardrails",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".cursor/hooks.json",
    ".cursor/hooks",
    ".codex",
    ".gemini",
    ".agents/hooks.json",
    ".grok",
    ".guardrails_unlock",
]

PATH_KEYS = (
    "file_path", "path", "notebook_path", "filePath", "target_file", "target_notebook",
    "TargetFile", "AbsolutePath", "SearchPath", "dir_path", "working_directory", "Cwd",
)
WRITE_WORDS = ("write", "edit", "create", "replace", "patch", "notebook", "move", "rename")
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
SECRET_NAMES = ("id_rsa", "id_ed25519")
DB_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".mdb")
PATCH_FILE = re.compile(
    r"^\*\*\* (Add|Update|Delete) File:\s*(.+?)\s*$|^\*\*\* Move to:\s*(.+?)\s*$", re.M
)

FORMAT = "claude"
if "--format" in sys.argv:
    try:
        FORMAT = sys.argv[sys.argv.index("--format") + 1]
    except IndexError:
        pass

# ---------- command patterns ----------

NB = r"(?<![\w.\-])"   # not part of a longer word, path piece, or flag
NA = r"(?![\w\-])"

COMMAND_RULES = [
    (NB + r"(git|gh)(?:\.exe)?" + NA,
     "Rule 2: git and gh commands are not allowed. The owner runs them."),
    (NB + r"(rm|rmdir|rd|del|erase|unlink|shred|trash|trash-put|remove-item|ri|truncate)" + NA,
     "Rule 4: deleting is not allowed."),
    (r"\s-delete\b|\brmtree\b|os\.(remove|unlink|rmdir|removedirs)|\.unlink\(|\.rmdir\(|"
     r"\[io\.(file|directory)\]::delete|send2trash|robocopy[^\n]*(/mir|/purge)",
     "Rule 4: deleting is not allowed."),
    (NB + r"(sqlite3?|psql|mysql|mysqldump|mariadb|mongosh?|redis-cli|sqlcmd|pg_dump|pg_restore|"
     r"duckdb|cqlsh|supabase|prisma|alembic)" + NA,
     "Rule 3: database tools are not allowed without the owner's instruction."),
    (r"\b(delete\s+from|drop\s+(table|database|schema|index)|truncate)\b",
     "Rule 3: destructive SQL is not allowed."),
    (NB + r"(python[\d.]*|py|node|ruby|perl|php)(?:\.exe)?\s+(-c|-e)\b|"
     r"-encodedcommand|-enc\s|\biex\b|invoke-expression|(bash|sh|zsh|cmd)(?:\.exe)?\s+(-c|/c)\b|"
     r"powershell(?:\.exe)?\s+(-c|-command)\b",
     "Inline code is hidden from the guardrails. Put it in a script file and ask the owner first."),
    (r"(?<![\w])\.env(?!\.example)(?![\w\-])",
     "Secrets: .env files must not be touched."),
]

OUTSIDE_RULES = [
    (r"(?<![\w.])\.\.(?:[\\/]|$|\s|[\"'])", "Rule 5: parent folder (..) is outside the project."),
    (r"(?<![\w])~(?:[\\/]|\s|$)|\$\{?HOME\b|%(USERPROFILE|APPDATA|LOCALAPPDATA|TEMP|TMP|HOMEPATH)%|"
     r"\$env:(USERPROFILE|APPDATA|LOCALAPPDATA|TEMP|TMP|HOME|HOMEPATH|SYSTEMROOT)",
     "Rule 5: home, temp, or system folders are outside the project."),
]

WIN_ABS = re.compile(r"[A-Za-z]:[\\/][^\s\"'<>|;&)]*")
GITBASH_ABS = re.compile(r"(?<![\w.:])/([a-zA-Z])/[^\s\"'<>|;&)]*")
POSIX_ABS = re.compile(
    r"(?<![\w.:\-/])/(?:etc|usr|home|tmp|var|root|bin|opt|mnt|proc|sys|users)(?:/[^\s\"'<>|;&)]*)?",
    re.I,
)


def log(reason, tool, detail):
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("%s | %s | %s | %s\n" % (
                time.strftime("%Y-%m-%d %H:%M:%S"), tool, reason, detail[:200].replace("\n", " ")))
    except Exception:
        pass


def block(reason, tool="", detail=""):
    log(reason, tool, detail)
    msg = "BLOCKED by guardrails: %s Do not work around this. Tell the owner and ask." % reason
    out = {
        "decision": "deny",
        "reason": msg,
        "permission": "deny",
        "user_message": msg,
        "agent_message": msg,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg,
        },
    }
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def allow():
    if FORMAT == "cursor":
        sys.stdout.write('{"permission":"allow"}')
    elif FORMAT == "antigravity":
        sys.stdout.write('{"decision":"allow"}')
    sys.exit(0)


def norm(p):
    return os.path.normcase(os.path.abspath(str(p)))


def inside(path, base):
    a, b = norm(path), norm(base)
    try:
        return os.path.commonpath([a, b]) == b
    except ValueError:
        return False


def resolve(path_str, cwd):
    p = Path(os.path.expandvars(os.path.expanduser(path_str)))
    if not p.is_absolute():
        p = Path(cwd) / p
    return Path(os.path.realpath(p))


def allowed_location(p):
    return inside(p, ROOT) or any(inside(p, extra) for extra in EXTRA_ALLOWED)


def check_path(path_str, cwd, writing, tool):
    p = resolve(path_str, cwd)
    if not allowed_location(p):
        block("Rule 5: path is outside the project folder: %s" % path_str, tool, path_str)
    name = p.name.lower()
    if (name.startswith(".env") and not name.endswith((".example", ".sample"))) \
            or name.endswith(SECRET_SUFFIXES) or name in SECRET_NAMES:
        block("Secrets: this file must not be touched: %s" % p.name, tool, path_str)
    if name.endswith(DB_SUFFIXES):
        block("Rule 3: database files must not be touched: %s" % p.name, tool, path_str)
    if writing and not UNLOCK_FILE.exists() and inside(p, ROOT):
        rel = norm(p)[len(norm(ROOT)):].replace("\\", "/").lstrip("/")
        for prot in PROTECTED:
            prot = prot.lower()
            if rel == prot or rel.startswith(prot + "/"):
                block("Protected guardrail file. Only the owner can unlock it (.guardrails_unlock): %s" % rel,
                      tool, path_str)


def strip_root(cmd):
    """Remove the project path from the command so spaces in it do not confuse checks."""
    root_win = str(ROOT)
    forms = {root_win, root_win.replace("\\", "/")}
    drive = root_win[0].lower()
    forms.add("/" + drive + root_win[2:].replace("\\", "/"))
    for form in sorted(forms, key=len, reverse=True):
        cmd = re.sub(re.escape(form), "<ROOT>", cmd, flags=re.I)
    return cmd


def check_command(cmd, cwd, tool):
    scrubbed = strip_root(cmd)
    for pattern, reason in COMMAND_RULES:
        if re.search(pattern, scrubbed, re.I):
            block(reason, tool, cmd)
    for pattern, reason in OUTSIDE_RULES:
        if re.search(pattern, scrubbed, re.I):
            block(reason, tool, cmd)
    candidates = []
    for m in WIN_ABS.finditer(scrubbed):
        candidates.append(m.group(0))
    for m in GITBASH_ABS.finditer(scrubbed):
        candidates.append(m.group(1) + ":/" + m.group(0)[3:])
    for m in POSIX_ABS.finditer(scrubbed):
        candidates.append(m.group(0))
    for c in candidates:
        c = c.rstrip(".,:;")
        if c.lower() == "/dev/null":
            continue
        if not allowed_location(resolve(c, cwd)):
            block("Rule 5: command touches a path outside the project: %s" % c, tool, cmd)
    low = cmd.lower().replace("\\", "/")
    if not UNLOCK_FILE.exists():
        for prot in PROTECTED:
            if prot.lower() in low:
                block("Protected guardrail file mentioned in a command: %s" % prot, tool, cmd)


def check_patch(patch_text, cwd, tool):
    """Codex apply_patch: the patch text lists the files it touches."""
    for m in PATCH_FILE.finditer(patch_text):
        if m.group(1) == "Delete":
            block("Rules 3 and 4: deleting a file through a patch is not allowed.", tool, m.group(2))
        check_path(m.group(2) or m.group(3), cwd, True, tool)


def collect_strings(value, out):
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            collect_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            collect_strings(v, out)


def read_call(data):
    """Normalize the payload of any supported tool into (tool name, input dict, cwd)."""
    tc = data.get("toolCall") if isinstance(data.get("toolCall"), dict) else {}
    tool = str(data.get("tool_name") or data.get("toolName") or tc.get("name") or data.get("tool") or "")
    ti = (data.get("tool_input") or data.get("toolInput") or tc.get("args")
          or data.get("input") or data.get("arguments") or {})
    if isinstance(ti, str):
        try:
            ti = json.loads(ti)
        except Exception:
            ti = {"command": ti}
    if not isinstance(ti, dict):
        ti = {}
    ti = dict(ti)
    if "command" not in ti:
        if isinstance(ti.get("CommandLine"), str):
            ti["command"] = ti["CommandLine"]
        elif "command" in data:
            ti["command"] = data["command"]
    for key in PATH_KEYS:  # Cursor sends some paths at the top level
        if key not in ti and isinstance(data.get(key), str):
            ti[key] = data[key]
    cwd = (data.get("cwd") or ti.get("Cwd") or ti.get("working_directory")
           or data.get("workspaceRoot") or str(ROOT))
    return tool, ti, cwd


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("input is not an object")
    except Exception as exc:
        block("Could not read hook input (%s). Failing closed." % exc)

    tool, ti, cwd = read_call(data)
    name = tool.lower()

    if isinstance(cwd, str) and os.path.isabs(cwd) and not allowed_location(resolve(cwd, ROOT)):
        block("Rule 5: working folder is outside the project: %s" % cwd, tool, cwd)

    # Rules 3 and 4: delete style tools or actions.
    if re.search(r"(delete|remove(?!_background))", name):
        block("Rules 3 and 4: delete tools are not allowed (%s)." % tool, tool)
    for key in ("action", "operation", "op", "method"):
        val = ti.get(key)
        if isinstance(val, str) and "delete" in val.lower():
            block("Rules 3 and 4: delete actions are not allowed (%s=%s)." % (key, val), tool)
    ops = ti.get("batch")
    if isinstance(ops, list):
        flat = []
        collect_strings(ops, flat)
        if any(s.lower() in ("delete", "remove") for s in flat):
            block("Rules 3 and 4: delete inside a batch is not allowed.", tool)

    # Shell commands and patches.
    cmd = ti.get("command")
    if isinstance(cmd, list):
        cmd = " ".join(str(x) for x in cmd)
    if isinstance(cmd, str):
        if name == "apply_patch" or cmd.lstrip().startswith("*** Begin Patch"):
            check_patch(cmd, cwd, tool)
        else:
            check_command(cmd, cwd, tool)

    # File paths.
    writing = any(w in name for w in WRITE_WORDS)
    for key in PATH_KEYS:
        val = ti.get(key)
        if isinstance(val, str) and val.strip():
            check_path(val, cwd, writing, tool)
    if isinstance(ti.get("paths"), list):
        for val in ti["paths"]:
            if isinstance(val, str) and val.strip():
                check_path(val, cwd, writing, tool)

    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        block("Guardrail script error (%s). Failing closed." % exc)
