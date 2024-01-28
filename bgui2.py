import signal
import customtkinter as ctk
import subprocess
from tkinter import filedialog, messagebox, scrolledtext
import threading
import queue
import os
from PIL import Image, ImageTk, ImageFilter
import requests
from io import BytesIO

class ProgramLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Infinity Panel")
        self.geometry("800x400")

        self.file_path = ctk.StringVar()
        self.is_program_running = threading.Event()
        self.process = None
        self.queue = queue.Queue()

        self.label = ctk.CTkLabel(self, text="Infinity Panel")
        self.label.pack(pady=10)

        # Create a frame for buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(side="left", padx=10, pady=10)

        self.browse_button = ctk.CTkButton(button_frame, text="Select Bot", command=self.browse_file)
        self.browse_button.pack(pady=10)

        self.launch_button = ctk.CTkButton(button_frame, text="Launch Bot", command=self.launch_program)
        self.launch_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(button_frame, text="Stop Bot", command=self.stop_program, state=ctk.DISABLED)
        self.stop_button.pack(pady=10)

        # Move the console frame to the left
        self.console_frame = ctk.CTkFrame(self, width=400, height=400, bg_color="#f0f0f0", corner_radius=5)
        self.console_frame.pack(side="left", expand=True, padx=10, pady=10)

        self.console_logs = scrolledtext.ScrolledText(self.console_frame, width=40, height=20, bg="#f0f0f0",
                                                      fg="#000000", wrap="word", state="disabled")
        self.console_logs.pack(padx=10, pady=10)

        # Create a frame for labels on the right side
        labels_frame = ctk.CTkFrame(self)
        labels_frame.pack(side="right", padx=10, pady=10)

        self.bot_status_label = ctk.CTkLabel(labels_frame, text="Bot Status")
        self.bot_status_label.pack(pady=5)

        self.bot_status_value_label = ctk.CTkLabel(labels_frame, text="OFFLINE", text_color="#FF0000")
        self.bot_status_value_label.pack(pady=2)

        self.bot_profile_label = ctk.CTkLabel(labels_frame, text="Bot Profile")
        self.bot_profile_label.pack(pady=5)

        # Replace "YOUR_BOT_TOKEN" with a valid Discord bot token
        bot_token = "MTIwMDQwNzY5OTc3MTM1OTMyMg.GL7Wde.AbamQ9rKynHFOz7hYodDPl1J0SNBoJk34YRpK4"

        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        config_file_path = "config.txt"
        user_id = self.read_user_id_from_config(config_file_path)
        response = requests.get(f"https://discord.com/api/v9/users/{user_id}", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            username = user_data["username"]
            discriminator = user_data["discriminator"]
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{user_data['avatar']}.png"

            response = requests.get(avatar_url)
            image_data = BytesIO(response.content)
            original_image = Image.open(image_data)

            # Resize the image
            resized_image = original_image.resize((150, 150))  # Adjust the dimensions as needed

            # Convert the image to CTkImage
            ctk_image = ctk.CTkImage(resized_image, size=(50, 50))

            # Create a label to display the image
            self.image_label = ctk.CTkLabel(labels_frame, image=ctk_image, text="")
            self.image_label.pack(pady=3)

            # Create a label for bot username
            my_font5 = ctk.CTkFont(family="Comic Sans", size=15)
            self.username_label = ctk.CTkLabel(labels_frame, text=username, font=my_font5, text_color="#9400D3", corner_radius=5)
            self.username_label.pack(pady=5)

            self.protocol("WM_DELETE_WINDOW", self.on_closing)


    def read_user_id_from_config(self, config_file_path):
        try:
            with open(config_file_path, "r") as file:
                for line in file:
                    if line.startswith("userid"):
                        _, user_id = line.strip().split("=")
                        return user_id.strip(' "')
        except FileNotFoundError:
            messagebox.showerror("Error", f"Config file '{config_file_path}' not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading user ID from config file: {e}")
        return ""

    def read_token_from_config(self, config_file_path):
        try:
            with open(config_file_path, "r") as file:
                for line in file:
                    if line.startswith("token"):
                        _, user_id = line.strip().split("=")
                        return user_id.strip(' "')
        except FileNotFoundError:
            messagebox.showerror("Error", f"Config file '{config_file_path}' not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading user ID from config file: {e}")
        return ""
    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JAR Files", "*.jar")])
        if file_path:
            self.file_path.set(file_path)

    def launch_program(self):
        program_path = self.file_path.get()
        if program_path:
            self.stop_button.configure(state=ctk.NORMAL)
            self.is_program_running.set()
            threading.Thread(target=self.run_subprocess, args=(["java", "-Dnogui=true", "-jar", program_path],)).start()

    def run_subprocess(self, command):
        try:
            self.is_program_running.set()
            self.update_bot_status("ONLINE")  # Update bot status to ONLINE when the process starts
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                            bufsize=1)

            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.queue.put(line)

            self.process.stdout.close()
            self.process.wait()
        except subprocess.CalledProcessError as e:
            self.queue.put(e.stderr)
        except Exception as e:
            self.queue.put(f"Error running subprocess: {e}")
        finally:
            self.is_program_running.clear()
            self.update_bot_status("OFFLINE")  # Update bot status to OFFLINE when the process completes

    def update_bot_status(self, status):
        self.bot_status_value_label.configure(text=status, text_color="#00FF00" if status == "ONLINE" else "#FF0000")

    def stop_program(self):
        try:
            if self.process and self.is_program_running.is_set():
                if os.name == 'posix':  # Unix-based systems
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:  # Windows
                    self.process.terminate()
                    self.process.communicate()  # Wait for the process to complete
        except Exception as e:
            print(f"Error stopping program: {e}")
        finally:
            self.is_program_running.clear()
            self.stop_button.configure(state=ctk.DISABLED)

    def update_console_logs(self):
        while True:
            try:
                line = self.queue.get_nowait()
                if line == "ProcessCompleted":
                    break

                self.console_logs.configure(state="normal")
                self.console_logs.insert("end", line)
                self.console_logs.configure(state="disabled")
                self.console_logs.yview("end")
                self.update_idletasks()
            except queue.Empty:
                pass

    def on_closing(self):
        if self.is_program_running.is_set():
            messagebox.showinfo("Program Running", "Please stop the program before closing.")
        else:
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                self.destroy()

if __name__ == "__main__":
    app = ProgramLauncherApp()
    threading.Thread(target=app.update_console_logs).start()
    app.mainloop()
