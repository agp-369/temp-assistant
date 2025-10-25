import customtkinter as ctk
import threading
import time
from . import dashboard_data
from . import window_manager
from plugins.system_monitor import SystemMonitorPlugin
from plugins.alarms import AlarmsPlugin

class AssistantGUI(ctk.CTk):
    def __init__(self, assistant):
        super().__init__()
        self.title(assistant.assistant_name)
        self.geometry("600x700")

        self.assistant = assistant
        self.assistant.output_callback = self.update_conversation

        # --- Main Tabbed Interface ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=10, pady=10)

        self.chat_tab = self.tab_view.add("Chat")
        self.dashboard_tab = self.tab_view.add("Dashboard")
        self.system_tab = self.tab_view.add("System Status")

        # --- Chat Tab ---
        self.setup_chat_tab()

        # --- Dashboard Tab ---
        self.setup_dashboard_tab()
        self.populate_dashboard()

        # --- System Status Tab ---
        self.system_monitor_plugin = [p for p in self.assistant.plugins if isinstance(p, SystemMonitorPlugin)][0]
        self.alarms_plugin = [p for p in self.assistant.plugins if isinstance(p, AlarmsPlugin)][0]
        self.setup_system_tab()
        self.start_system_monitor()

    def setup_chat_tab(self):
        # ... (same as before)
        self.conversation_area = ctk.CTkTextbox(self.chat_tab, wrap='word', state='disabled')
        self.conversation_area.pack(pady=10, padx=10, expand=True, fill='both')
        self.input_frame = ctk.CTkFrame(self.chat_tab)
        self.input_frame.pack(pady=10, padx=10, fill='x')
        self.input_box = ctk.CTkEntry(self.input_frame, placeholder_text="Type your command...")
        self.input_box.pack(side='left', expand=True, fill='x')
        self.input_box.bind("<Return>", self.send_command)
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_command)
        self.send_button.pack(side='right', padx=5)
        self.voice_button = ctk.CTkButton(self.input_frame, text="Start Listening", command=self.activate_voice)
        self.voice_button.pack(side='right')

    def setup_dashboard_tab(self):
        # ... (same as before)
        self.refresh_button = ctk.CTkButton(self.dashboard_tab, text="Refresh", command=self.populate_dashboard)
        self.refresh_button.pack(pady=5, padx=10, anchor="e")
        self.apps_frame = ctk.CTkFrame(self.dashboard_tab)
        self.apps_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(self.apps_frame, text="Running Applications (Click to Focus)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)
        self.apps_list_frame = ctk.CTkScrollableFrame(self.apps_frame, height=150)
        self.apps_list_frame.pack(fill='x', padx=5, pady=5)
        self.files_frame = ctk.CTkFrame(self.dashboard_tab)
        self.files_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(self.files_frame, text="Recent Files", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)
        self.files_list_frame = ctk.CTkScrollableFrame(self.files_frame, height=150)
        self.files_list_frame.pack(fill='x', padx=5, pady=5)
        self.shortcuts_frame = ctk.CTkFrame(self.dashboard_tab)
        self.shortcuts_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(self.shortcuts_frame, text="Custom Shortcuts", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)
        self.shortcuts_list_frame = ctk.CTkScrollableFrame(self.shortcuts_frame, height=150)
        self.shortcuts_list_frame.pack(fill='x', padx=5, pady=5)

    def setup_system_tab(self):
        # CPU Usage
        self.cpu_frame = ctk.CTkFrame(self.system_tab)
        self.cpu_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(self.cpu_frame, text="CPU Usage", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.cpu_label = ctk.CTkLabel(self.cpu_frame, text="Loading...")
        self.cpu_label.pack(side="right", padx=10)

        # Memory Usage
        self.mem_frame = ctk.CTkFrame(self.system_tab)
        self.mem_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(self.mem_frame, text="Memory Usage", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.mem_label = ctk.CTkLabel(self.mem_frame, text="Loading...")
        self.mem_label.pack(side="right", padx=10)

        # Battery Status
        self.bat_frame = ctk.CTkFrame(self.system_tab)
        self.bat_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(self.bat_frame, text="Battery Status", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.bat_label = ctk.CTkLabel(self.bat_frame, text="Loading...")
        self.bat_label.pack(side="right", padx=10)

        # Alarms/Reminders
        self.alarms_frame = ctk.CTkFrame(self.system_tab)
        self.alarms_frame.pack(pady=10, padx=10, fill='both', expand=True)
        ctk.CTkLabel(self.alarms_frame, text="Pending Reminders", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5)
        self.alarms_list_frame = ctk.CTkScrollableFrame(self.alarms_frame)
        self.alarms_list_frame.pack(fill='both', expand=True, padx=5, pady=5)

    def start_system_monitor(self):
        """Starts a background thread to update system stats."""
        def monitor_loop():
            while True:
                self.cpu_label.configure(text=self.system_monitor_plugin.get_cpu_usage())
                self.mem_label.configure(text=self.system_monitor_plugin.get_memory_usage())
                self.bat_label.configure(text=self.system_monitor_plugin.get_battery_status())

                # Check for and send low battery alert
                self.system_monitor_plugin.check_battery_alert()

                # Update alarms (simple display)
                for widget in self.alarms_list_frame.winfo_children():
                    widget.destroy()

                active_alarms = [a for a in self.alarms_plugin.alarms if a.is_alive()]
                if not active_alarms:
                    ctk.CTkLabel(self.alarms_list_frame, text="No pending reminders.").pack(anchor="w")
                else:
                    for alarm in active_alarms:
                        # This is a simplification; getting the message would be better
                        ctk.CTkLabel(self.alarms_list_frame, text=f"Reminder in {round(alarm.interval)}s").pack(anchor="w")

                time.sleep(2) # Update every 2 seconds

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    # ... (rest of the methods are the same)
    def populate_dashboard(self):
        for frame in [self.apps_list_frame, self.files_list_frame, self.shortcuts_list_frame]:
            for widget in frame.winfo_children():
                widget.destroy()
        running_apps = dashboard_data.get_running_applications()
        for app_name in running_apps:
            app_label = ctk.CTkButton(self.apps_list_frame, text=app_name, fg_color="transparent", anchor="w",
                                      command=lambda name=app_name: window_manager.bring_window_to_front(name))
            app_label.pack(anchor="w", fill="x")
        recent_files = dashboard_data.get_recent_files()
        for file_name in recent_files:
            ctk.CTkLabel(self.files_list_frame, text=file_name).pack(anchor="w")
        shortcuts = dashboard_data.get_custom_shortcuts()
        for shortcut_name in shortcuts:
            ctk.CTkLabel(self.shortcuts_list_frame, text=shortcut_name).pack(anchor="w")

    def send_command(self, event=None):
        command = self.input_box.get()
        if command:
            self.update_conversation(f"You: {command}", is_user=True)
            self.input_box.delete(0, 'end')
            threading.Thread(target=self.process_and_handle_exit, args=(command,), daemon=True).start()

    def activate_voice(self):
        self.update_conversation("You: (Listening for voice command...)", is_user=True)
        threading.Thread(target=self.listen_and_process, daemon=True).start()

    def listen_and_process(self):
        command = self.assistant.listen_for_command()
        if command:
            self.process_and_handle_exit(command)

    def process_and_handle_exit(self, command):
        if not self.assistant.process_command(command):
            self.destroy()

    def update_conversation(self, text, is_user=False):
        self.conversation_area.configure(state='normal')
        if is_user:
            self.conversation_area.insert('end', text + '\n\n')
        else:
            self.conversation_area.insert('end', f"{self.assistant.assistant_name}: {text}\n\n")
        self.conversation_area.configure(state='disabled')
        self.conversation_area.see('end')

    def start_wake_word_listener(self):
        wake_word_thread = threading.Thread(target=self.assistant.listen_for_wake_word, daemon=True)
        wake_word_thread.start()

    def start(self):
        self.update_conversation(f"Hello! I'm {self.assistant.assistant_name}. How can I help you?")
        self.start_wake_word_listener()
        self.mainloop()
