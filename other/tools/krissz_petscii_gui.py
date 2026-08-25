import os
import tkinter as tk
from tkinter import filedialog, messagebox

from krissz_petscii_converter import Converter, grid_to_text, to_file_name

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_TOOLS_DIR, "..", ".."))
_DEFAULT_OUTPUT_DIR = os.path.join(_REPO_ROOT, "demos", "petscii", "files", "petscii")


def _make_text(parent, height):
    frame = tk.Frame(parent)
    text = tk.Text(frame, height=height, wrap="none", undo=True)
    y_scroll = tk.Scrollbar(frame, orient="vertical", command=text.yview)
    x_scroll = tk.Scrollbar(frame, orient="horizontal", command=text.xview)
    text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
    text.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, text


class ConverterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("krissz.hu PETSCII Converter")
        self.desired_class = None
        self._build_top_bar()
        self._build_body()

    def _build_top_bar(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top, text="Destination CLASS NAME").pack(side="left")
        self.class_name_entry = tk.Entry(top, width=24)
        self.class_name_entry.insert(0, "Klazz")
        self.class_name_entry.pack(side="left", padx=(6, 12))
        tk.Label(top, text="Last row").pack(side="left")
        self.last_row_entry = tk.Entry(top, width=5)
        self.last_row_entry.insert(0, "25")
        self.last_row_entry.pack(side="left", padx=(6, 12))
        tk.Label(top, text="Last column").pack(side="left")
        self.last_column_entry = tk.Entry(top, width=5)
        self.last_column_entry.insert(0, "40")
        self.last_column_entry.pack(side="left", padx=(6, 12))
        tk.Button(top, text="Convert", command=self._on_convert).pack(side="left")
        tk.Button(top, text="Save…", command=self._on_save).pack(side="left", padx=(6, 0))

    def _build_body(self):
        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = tk.LabelFrame(body, text="Converter inputs")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        left.rowconfigure(3, weight=1)
        tk.Label(left, text="Input Char Data").grid(row=0, column=0, sticky="w")
        char_frame, self.char_input = _make_text(left, 10)
        char_frame.grid(row=1, column=0, sticky="nsew")
        tk.Label(left, text="Input Color Data").grid(row=2, column=0, sticky="w", pady=(6, 0))
        color_frame, self.color_input = _make_text(left, 10)
        color_frame.grid(row=3, column=0, sticky="nsew")

        right = tk.LabelFrame(body, text="DesiredClass output")
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)
        right.rowconfigure(5, weight=1)
        tk.Label(right, text="chars").grid(row=0, column=0, sticky="w")
        chars_frame, self.chars_output = _make_text(right, 7)
        chars_frame.grid(row=1, column=0, sticky="nsew")
        tk.Label(right, text="reversed").grid(row=2, column=0, sticky="w", pady=(6, 0))
        reversed_frame, self.reversed_output = _make_text(right, 7)
        reversed_frame.grid(row=3, column=0, sticky="nsew")
        tk.Label(right, text="colors").grid(row=4, column=0, sticky="w", pady=(6, 0))
        colors_frame, self.colors_output = _make_text(right, 7)
        colors_frame.grid(row=5, column=0, sticky="nsew")

    def _on_convert(self):
        if not self.class_name_entry.get().strip():
            messagebox.showerror("Conversion failed", "Enter a destination class name.")
            return
        try:
            last_row, last_column = self._read_trim()
        except ValueError as error:
            messagebox.showerror("Conversion failed", str(error))
            return
        converter = Converter(
            self.char_input.get("1.0", "end"),
            self.color_input.get("1.0", "end"),
            self.class_name_entry.get(),
        )
        try:
            desired_class = converter.convert()
        except ValueError as error:
            messagebox.showerror("Conversion failed", str(error))
            return
        self.desired_class = desired_class
        self.class_name_entry.delete(0, "end")
        self.class_name_entry.insert(0, desired_class.name)
        preview = desired_class.trimmed(last_row, last_column)
        self._show_grid(self.chars_output, preview.chars)
        self._show_grid(self.reversed_output, preview.reversed)
        self._show_grid(self.colors_output, preview.colors)

    def _on_save(self):
        if self.desired_class is None:
            messagebox.showinfo("Nothing to save", "Convert first, then save.")
            return
        try:
            last_row, last_column = self._read_trim()
        except ValueError as error:
            messagebox.showerror("Save failed", str(error))
            return
        target_dir = _DEFAULT_OUTPUT_DIR if os.path.isdir(_DEFAULT_OUTPUT_DIR) else _TOOLS_DIR
        path = filedialog.asksaveasfilename(
            title="Save PETSCII class",
            defaultextension=".py",
            initialdir=target_dir,
            initialfile=to_file_name(self.desired_class.name),
            filetypes=[("Python", "*.py"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.desired_class.trimmed(last_row, last_column).create_class(path)
        except OSError as error:
            messagebox.showerror("Save failed", str(error))
            return
        messagebox.showinfo("Saved", f"Wrote {path}")

    def _read_trim(self):
        last_row = self._parse_dimension(self.last_row_entry.get(), "Last row")
        last_column = self._parse_dimension(self.last_column_entry.get(), "Last column")
        return last_row, last_column

    @staticmethod
    def _parse_dimension(text, label):
        value = text.strip()
        if not value.isdigit() or int(value) <= 0:
            raise ValueError(f"{label} must be a positive whole number.")
        return int(value)

    def _show_grid(self, widget, grid):
        widget.delete("1.0", "end")
        widget.insert("1.0", grid_to_text(grid))


def main():
    root = tk.Tk()
    root.geometry("1100x700")
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
