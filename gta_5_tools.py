import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
# Ensure pillow-dds plugin is installed: pip install pillow-dds

class TextureFinderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Texture & Asset Helper")
        self.geometry("900x650")  # Increased height for debug console

        # Main PanedWindow
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)  # Changed to vertical
        paned.pack(fill=tk.BOTH, expand=True)

        # Top frame for main content
        top_frame = ttk.Frame(paned)
        paned.add(top_frame, weight=3)

        # Bottom frame for debug console and progress
        bottom_frame = ttk.Frame(paned)
        paned.add(bottom_frame, weight=1)

        # Create horizontal paned window for main content
        main_paned = ttk.PanedWindow(top_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Left frame: controls and folders
        control_frame = ttk.Frame(main_paned, padding=10)
        main_paned.add(control_frame, weight=1)

        # Right frame: output
        output_frame = ttk.Frame(main_paned, padding=10)
        main_paned.add(output_frame, weight=2)

        # Folder selectors
        ttk.Label(control_frame, text="Step 1:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)
        self.processed_folder = tk.StringVar()
        ttk.Button(control_frame, text="Select Processed Textures Folder", command=self.select_processed_folder).pack(fill=tk.X)
        ttk.Label(control_frame, textvariable=self.processed_folder, wraplength=250).pack(fill=tk.X, pady=(5,10))

        ttk.Label(control_frame, text="Step 2:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)
        self.original_folder = tk.StringVar()
        ttk.Button(control_frame, text="Select Original Textures Folder", command=self.select_original_folder).pack(fill=tk.X)
        ttk.Label(control_frame, textvariable=self.original_folder, wraplength=250).pack(fill=tk.X, pady=(5,10))

        # Search mode
        ttk.Label(control_frame, text="Step 3:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)
        self.mode = tk.StringVar(value="name")
        modes = [("Search by Texture Name", "name"), ("Search by Folder Match", "folder")]
        for txt, val in modes:
            ttk.Radiobutton(control_frame, text=txt, variable=self.mode, value=val, 
                           command=self.update_search_mode).pack(anchor=tk.W)

        # Name search input
        self.name_entry = ttk.Entry(control_frame)
        self.name_entry.pack(fill=tk.X, pady=5)
        self.name_entry.insert(0, "texture_name.png")

        # Search button
        ttk.Button(control_frame, text="Search", command=self.run_search).pack(fill=tk.X, pady=(10,0))

        # Output listbox
        ttk.Label(output_frame, text="Matching Folders:").pack(anchor=tk.W)
        self.listbox = tk.Listbox(output_frame)
        self.listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Debug console
        ttk.Label(bottom_frame, text="Debug Console:").pack(anchor=tk.W)
        self.debug_text = tk.Text(bottom_frame, height=6, wrap=tk.WORD)
        self.debug_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        debug_scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.debug_text.yview)
        debug_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.debug_text.config(yscrollcommand=debug_scrollbar.set)

        # Progress bar and status
        progress_frame = ttk.Frame(bottom_frame)
        progress_frame.pack(fill=tk.X, pady=(5,0))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(side=tk.RIGHT, padx=5)

        # Menu bar
        menu_bar = tk.Menu(self)
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Batch DDS/PNG Converter", command=self.open_converter)
        tools_menu.add_command(label="FBX Matcher", command=self.open_fbx_matcher)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        # About menu
        about_menu = tk.Menu(menu_bar, tearoff=0)
        about_menu.add_command(label="Learn More", command=self.open_about)
        menu_bar.add_cascade(label="About", menu=about_menu)
        self.config(menu=menu_bar)

    def log_debug(self, message):
        self.debug_text.insert(tk.END, message + "\n")
        self.debug_text.see(tk.END)
        self.update_idletasks()

    def update_progress(self, current, total, message=None):
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        if message:
            self.progress_label.config(text=message)
        self.update_idletasks()

    def select_processed_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.processed_folder.set(path)
            self.log_debug(f"Selected processed folder: {path}")

    def select_original_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.original_folder.set(path)
            self.log_debug(f"Selected original folder: {path}")

    def run_search(self):
        original = self.original_folder.get()
        proc = self.processed_folder.get()
        if not original or not proc:
            messagebox.showwarning("Missing Folders", "Please select both the processed and original texture folders.")
            return

        self.listbox.delete(0, tk.END)
        matches = []  # Changed from set to list to maintain order
        self.progress_var.set(0)
        self.log_debug("Starting search...")

        # Count total folders for progress
        total_folders = sum(1 for _ in os.walk(original))
        current_folder = 0

        if self.mode.get() == "name":
            target = self.name_entry.get().strip().lower()
            # Remove extension from target if present
            target = os.path.splitext(target)[0]
            self.log_debug(f"Searching for: {target}")
            for dirpath, _, files in os.walk(original):
                current_folder += 1
                self.update_progress(current_folder, total_folders, 
                                   f"Searching folder {current_folder}/{total_folders}")
                for f in files:
                    # Compare base filenames without extensions
                    base_name = os.path.splitext(f)[0].lower()
                    if base_name == target:
                        matches.append((f, dirpath))
                        self.log_debug(f"Found match in: {dirpath}")
        else:
            # compare against processed textures
            # Create a dictionary of base filenames without extensions
            proc_files = {os.path.splitext(f)[0].lower(): f for f in os.listdir(proc) 
                         if f.lower().endswith('.png')}
            self.log_debug(f"Comparing against {len(proc_files)} processed textures")
            
            for dirpath, _, files in os.walk(original):
                current_folder += 1
                self.update_progress(current_folder, total_folders,
                                   f"Searching folder {current_folder}/{total_folders}")
                for f in files:
                    if f.lower().endswith('.dds'):  # Only check DDS files
                        base_name = os.path.splitext(f)[0].lower()
                        if base_name in proc_files:
                            matches.append((f"{proc_files[base_name]} → {f}", dirpath))
                            self.log_debug(f"Found match: {proc_files[base_name]} → {f} in {dirpath}")

        # Sort matches by filename
        matches.sort(key=lambda x: x[0].lower())
        
        # Display matches in listbox
        for match_text, dirpath in matches:
            self.listbox.insert(tk.END, f"{match_text}\n  └─ {dirpath}")

        self.log_debug(f"Search complete. Found {len(matches)} matches.")
        self.update_progress(total_folders, total_folders, "Search complete")

    def open_converter(self):
        ConverterPopup(self)

    def open_fbx_matcher(self):
        FBXMatcherPopup(self)

    def open_about(self):
        AboutPopup(self)

    def update_search_mode(self):
        """Update the state of the name entry based on the selected search mode"""
        if self.mode.get() == "folder":
            self.name_entry.config(state='disabled')
        else:
            self.name_entry.config(state='normal')

class ConverterPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Batch DDS & PNG Converter")
        self.geometry("400x150")
        ttk.Button(self, text="Select Folder", command=self.select_folder).pack(pady=10)
        self.folder = tk.StringVar()
        ttk.Label(self, textvariable=self.folder, wraplength=350).pack()
        self.mode = tk.StringVar(value="dds2png")
        ttk.Radiobutton(self, text="DDS -> PNG", variable=self.mode, value="dds2png").pack(anchor=tk.W)
        ttk.Radiobutton(self, text="PNG -> DDS", variable=self.mode, value="png2dds").pack(anchor=tk.W)
        ttk.Button(self, text="Convert", command=self.convert).pack(pady=10)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder.set(path)

    def convert(self):
        root = self.folder.get()
        if not root:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return
        count = 0
        for dirpath, _, files in os.walk(root):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                full = os.path.join(dirpath, f)
                if self.mode.get() == "dds2png" and ext == ".dds":
                    img = Image.open(full)
                    out = os.path.splitext(full)[0] + ".png"
                    img.save(out)
                    count += 1
                elif self.mode.get() == "png2dds" and ext == ".png":
                    img = Image.open(full)
                    out = os.path.splitext(full)[0] + ".dds"
                    img.save(out, format="DDS")
                    count += 1
        messagebox.showinfo("Conversion Complete", f"Converted {count} files.")

class FBXMatcherPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("FBX to XML Matcher")
        self.geometry("400x150")
        ttk.Button(self, text="Select Root Folder", command=self.select_folder).pack(pady=10)
        self.folder = tk.StringVar()
        ttk.Label(self, textvariable=self.folder, wraplength=350).pack()
        ttk.Button(self, text="Run Matcher", command=self.match).pack(pady=10)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder.set(path)

    def match(self):
        root = self.folder.get()
        if not root:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return
        xml_map = {}
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.lower().endswith('.xml'):
                    xml_map[os.path.splitext(f)[0]] = dirpath
        moved = 0
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.lower().endswith('.fbx'):
                    base = os.path.splitext(f)[0]
                    if base in xml_map:
                        src = os.path.join(dirpath, f)
                        dst = os.path.join(xml_map[base], f)
                        if os.path.abspath(src) != os.path.abspath(dst):
                            shutil.move(src, dst)
                            moved += 1
        messagebox.showinfo("FBX Matcher", f"Moved {moved} FBX files to matching XML folders.")

class AboutPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About Texture & Asset Helper")
        self.geometry("450x250")
        desc = (
            "TL:DR: Christian Got Tired Of Doing This Manually So He Made This Tool\n\n"

            "Texture & Asset Helper is a multi-purpose tool for GTA V modders and game asset teams.\n"  
            "It lets you:\n"
            " - Search original texture folders by filename or compare against processed textures to find matches.\n"
            " - Batch-convert DDS to PNG (and back) effortlessly.\n"
            " - Automatically match FBX files to their XML definitions.\n\n"
            
            "Built with Python, Tkinter & Pillow for cross-platform ease-of-use.\n"
            "Hopefully someone finds it useful!\n"
            "P.S. Nay if you're reading this, you owe me a beer."
        )
        ttk.Label(self, text=desc, wraplength=420, justify=tk.LEFT).pack(padx=10, pady=10)

if __name__ == '__main__':
    app = TextureFinderApp()
    app.mainloop()

# To build .exe:
# pip install pyinstaller  pillow-dds
# pyinstaller --onefile --windowed this_script.py
