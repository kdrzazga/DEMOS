import os

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "resources")


def load_text(name):
    with open(os.path.join(RESOURCES_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def build_lines(text, max_chars=62):
    words = text.split()
    lines = []
    line = ""
    for w in words:
        if not line:
            line = w
        elif len(line) + 1 + len(w) <= max_chars:
            line += " " + w
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines
