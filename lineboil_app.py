#!/usr/bin/env python3
"""
Line Boil Effect App
A simple GUI application to apply line boil effects to MP4 videos.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter


class LineBoilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Line Boil Effect")
        self.root.geometry("500x650")
        self.root.resizable(False, False)

        self.input_path = None
        self.output_path = None
        self.processing = False

        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Line Boil Effect", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=(0, 20))

        # Drop zone / File selection
        drop_frame = ttk.LabelFrame(main_frame, text="Input Video", padding="10")
        drop_frame.pack(fill=tk.X, pady=(0, 15))

        self.file_label = ttk.Label(drop_frame, text="No file selected", foreground="gray")
        self.file_label.pack(pady=5)

        btn_frame = ttk.Frame(drop_frame)
        btn_frame.pack(pady=5)

        self.browse_btn = ttk.Button(btn_frame, text="Browse...", command=self.browse_file)
        self.browse_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_file)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="10")
        params_frame.pack(fill=tk.X, pady=(0, 15))

        # Edge Threshold
        self.edge_threshold = self.create_slider(
            params_frame, "Edge Threshold:", 0, 255, 60,
            tooltip="Controls how strong an edge must be to be detected"
        )

        # Boil Strength
        self.boil_strength = self.create_slider(
            params_frame, "Boil Strength:", 0, 10, 2.0,
            tooltip="Amount of jitter/movement in the lines", step=0.1
        )

        # Noise Scale
        self.noise_scale = self.create_slider(
            params_frame, "Noise Scale:", 0.01, 0.2, 0.03,
            tooltip="Size of the noise patterns", step=0.01
        )

        # Min Thickness
        self.min_thickness = self.create_slider(
            params_frame, "Min Thickness:", 0, 5, 1,
            tooltip="Minimum line thickness"
        )

        # Max Thickness
        self.max_thickness = self.create_slider(
            params_frame, "Max Thickness:", 0, 5, 2,
            tooltip="Maximum line thickness"
        )

        # Invert checkbox
        self.invert_var = tk.BooleanVar(value=False)
        invert_check = ttk.Checkbutton(params_frame, text="Invert colors (black lines on white)", variable=self.invert_var)
        invert_check.pack(anchor=tk.W, pady=5)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor=tk.W)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=460)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Export button
        self.export_btn = ttk.Button(main_frame, text="Export Video", command=self.export_video)
        self.export_btn.pack(pady=10)

        # Status
        self.status_label = ttk.Label(main_frame, text="", foreground="gray")
        self.status_label.pack(pady=5)

    def create_slider(self, parent, label, min_val, max_val, default, step=1, tooltip=""):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        lbl = ttk.Label(frame, text=label, width=15)
        lbl.pack(side=tk.LEFT)

        var = tk.DoubleVar(value=default)

        value_label = ttk.Label(frame, text=f"{default:.2f}" if isinstance(default, float) else str(default), width=6)
        value_label.pack(side=tk.RIGHT)

        def update_label(val):
            if step < 1:
                value_label.config(text=f"{float(val):.2f}")
            else:
                value_label.config(text=str(int(float(val))))

        slider = ttk.Scale(frame, from_=min_val, to=max_val, variable=var,
                          orient=tk.HORIZONTAL, command=update_label)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        return var

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("MP4 files", "*.mp4"), ("All video files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
        )
        if filepath:
            self.input_path = filepath
            filename = os.path.basename(filepath)
            self.file_label.config(text=filename, foreground="black")
            self.status_label.config(text=f"Loaded: {filename}")

    def clear_file(self):
        self.input_path = None
        self.file_label.config(text="No file selected", foreground="gray")
        self.status_label.config(text="")

    def export_video(self):
        if not self.input_path:
            messagebox.showwarning("No Input", "Please select an input video first.")
            return

        if self.processing:
            messagebox.showinfo("Processing", "Already processing a video. Please wait.")
            return

        # Get output path
        default_name = os.path.splitext(os.path.basename(self.input_path))[0] + "_lineboil.mp4"
        output_path = filedialog.asksaveasfilename(
            title="Save Output Video",
            defaultextension=".mp4",
            initialfile=default_name,
            filetypes=[("MP4 files", "*.mp4")]
        )

        if not output_path:
            return

        self.output_path = output_path

        # Start processing in a thread
        self.processing = True
        self.export_btn.config(state=tk.DISABLED)
        self.browse_btn.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.process_video)
        thread.start()

    def process_video(self):
        try:
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                self.root.after(0, lambda: messagebox.showerror("Error", f"Unable to open input video: {self.input_path}"))
                return

            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height), False)

            # Get parameters
            edge_threshold = int(self.edge_threshold.get())
            boil_strength = float(self.boil_strength.get())
            noise_scale = float(self.noise_scale.get())
            min_thickness = int(self.min_thickness.get())
            max_thickness = int(self.max_thickness.get())
            invert = self.invert_var.get()

            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Edge detection with Sobel
                grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
                edges_mag = cv2.magnitude(grad_x, grad_y)
                edges_mag = np.clip(edges_mag, 0, 255).astype(np.uint8)
                _, edges_bin = cv2.threshold(edges_mag, edge_threshold, 255, cv2.THRESH_BINARY)

                # Random thickness per frame
                if max_thickness >= min_thickness and max_thickness > 0:
                    thickness = np.random.randint(min_thickness, max_thickness + 1)
                    if thickness > 0:
                        edges_bin = cv2.dilate(edges_bin, None, iterations=thickness)

                # Line boil effect - spatial jitter
                noise_field = np.random.randn(height, width)
                sigma = max(1.0, height * noise_scale)
                noise_field = gaussian_filter(noise_field, sigma=sigma)

                dx = (noise_field * boil_strength).astype(np.float32)
                dy = (noise_field[::-1] * boil_strength).astype(np.float32)
                grid_x, grid_y = np.meshgrid(
                    np.arange(width, dtype=np.float32),
                    np.arange(height, dtype=np.float32),
                )
                map_x = grid_x + dx
                map_y = grid_y + dy
                boiled = cv2.remap(
                    edges_bin,
                    map_x,
                    map_y,
                    interpolation=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT,
                )

                # Invert if requested
                if invert:
                    boiled = 255 - boiled

                out.write(boiled)

                frame_count += 1
                progress = int((frame_count / total_frames) * 100)
                self.root.after(0, lambda p=progress, f=frame_count, t=total_frames: self.update_progress(p, f, t))

            cap.release()
            out.release()

            self.root.after(0, self.processing_complete)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))
            self.root.after(0, self.reset_ui)

    def update_progress(self, progress, current, total):
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"Processing: {current}/{total} frames ({progress}%)")

    def processing_complete(self):
        self.progress_bar['value'] = 100
        self.progress_label.config(text="Complete!")
        self.status_label.config(text=f"Saved to: {os.path.basename(self.output_path)}", foreground="green")
        messagebox.showinfo("Complete", f"Video exported successfully!\n\n{self.output_path}")
        self.reset_ui()

    def reset_ui(self):
        self.processing = False
        self.export_btn.config(state=tk.NORMAL)
        self.browse_btn.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = LineBoilApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
