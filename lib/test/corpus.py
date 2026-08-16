import os

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "resources")


def load_text(name):
    with open(os.path.join(RESOURCES_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def build_lines(text, max_chars=62):
    lines = []
    line = ""
    for source in text.split("\n"):
        if not source.strip():
            if line:
                lines.append(line)
                line = ""
            lines.append("")
            continue
        for word in source.split():
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= max_chars:
                line += " " + word
            else:
                lines.append(line)
                line = word
    if line:
        lines.append(line)
    return lines
