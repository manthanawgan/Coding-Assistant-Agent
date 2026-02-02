from typing import List, Dict, Any
from difflib import unified_diff


def generate_diff(original: str, modified: str, filename: str = "file") -> str:
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = list(unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=''
    ))
    return ''.join(diff)


def parse_diff(diff_text: str) -> List[Dict[str, Any]]:
    files = []
    current_file = None
    current_hunks = []

    for line in diff_text.splitlines():
        if line.startswith('--- a/') or line.startswith('+++ b/'):
            if current_file and current_hunks:
                files.append(current_file)
            current_file = {"name": line.split('/')[-1].split('\t')[0], "hunks": []}
            current_hunks = []
        elif line.startswith('@@'):
            hunk = {
                "old_start": int(line.split('-')[1].split(',')[0]),
                "new_start": int(line.split('+')[1].split(',')[0]),
                "lines": []
            }
            current_hunks.append(hunk)
        elif line.startswith('+') and not line.startswith('+++'):
            if current_hunks:
                current_hunks[-1]["lines"].append({"type": "addition", "content": line[1:]})
        elif line.startswith('-') and not line.startswith('---'):
            if current_hunks:
                current_hunks[-1]["lines"].append({"type": "deletion", "content": line[1:]})
        elif line.startswith(' '):
            if current_hunks:
                current_hunks[-1]["lines"].append({"type": "context", "content": line[1:]})

    if current_file and current_hunks:
        current_file["hunks"] = current_hunks
        files.append(current_file)

    return files


def calculate_diff_stats(original: str, modified: str) -> Dict[str, int]:
    import difflib
    matcher = difflib.SequenceMatcher(None, original, modified)
    additions = sum(matcher.a_blocks - matcher.b_blocks for matcher in matcher.get_opcodes() if matcher[0] == 'insert')
    deletions = sum(matcher.b_blocks - matcher.a_blocks for matcher in matcher.get_opcodes() if matcher[0] == 'delete')

    return {
        "files_changed": 1,
        "additions": additions,
        "deletions": deletions
    }
