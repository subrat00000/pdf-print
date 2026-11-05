import os
import sys
import threading
import webbrowser
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import tkinter as tk
from tkinter import messagebox


def app_root():
    # PyInstaller extracts bundled data to _MEIPASS in one-file mode.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(app_root()), **kwargs)

    def log_message(self, format, *args):
        pass


def main():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        server.daemon_threads = True
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}/"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
    except Exception as exc:
        messagebox.showerror("PDF Scale & Print", f"Could not start the local application:\n{exc}")
        return

    root = tk.Tk()
    root.title("PDF Scale & Print")
    root.geometry("360x155")
    root.resizable(False, False)

    tk.Label(root, text="PDF Scale & Print", font=("Segoe UI", 15, "bold")).pack(pady=(16, 4))
    tk.Label(root, text="The local application is running in your browser.", font=("Segoe UI", 9)).pack(pady=3)

    def open_app():
        webbrowser.open(url)

    def close_app():
        try:
            server.shutdown()
            server.server_close()
        finally:
            root.destroy()

    buttons = tk.Frame(root)
    buttons.pack(pady=14)
    tk.Button(buttons, text="Open PDF application", width=19, command=open_app).pack(side="left", padx=5)
    tk.Button(buttons, text="Exit", width=8, command=close_app).pack(side="left", padx=5)

    root.protocol("WM_DELETE_WINDOW", close_app)
    root.after(500, open_app)
    root.mainloop()


if __name__ == "__main__":
    main()
