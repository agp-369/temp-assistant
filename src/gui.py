import customtkinter as ctk
import threading
import time
from PIL import Image, ImageDraw
import pystray
from . import dashboard_data
from . import window_manager
from plugins.system_monitor import SystemMonitorPlugin
from plugins.alarms import AlarmsPlugin

class AssistantGUI(ctk.CTk):
    def __init__(self, assistant):
        super().__init__()

        # --- Theme and Colors ---
        self.BG_COLOR = "#0D1117"
        self.ACCENT_COLOR = "#00FFFF"
        self.HIGHLIGHT_COLOR = "#1E90FF"
        self.TEXT_COLOR = "#F3F4F6"
        self.FRAME_BG_COLOR = "#161B22"

        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.BG_COLOR)

        self.title(f"AGP System - {assistant.assistant_name}")
        self.geometry("700x800")

        self.assistant = assistant
        self.assistant.output_callback = self.update_conversation
        self.assistant.status_callback = self.update_status

        # --- Main Layout Frames ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=self.FRAME_BG_COLOR)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.pack_propagate(False)

        # Main content frame
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        # Central Output Panel
        self.chat_output_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.chat_output_frame.grid(row=0, column=0, sticky="nsew")
        self.chat_output_frame.grid_rowconfigure(0, weight=1)
        self.chat_output_frame.grid_rowconfigure(1, weight=0) # Row for typing indicator
        self.chat_output_frame.grid_columnconfigure(0, weight=1)

        # Avatar Panel
        self.avatar_frame = ctk.CTkFrame(self.main_content_frame, width=150, fg_color=self.FRAME_BG_COLOR)
        self.avatar_frame.grid(row=0, column=1, sticky="ns", padx=(10,0))
        self.avatar_frame.pack_propagate(False)
        ctk.CTkLabel(self.avatar_frame, text="AI Avatar", text_color=self.ACCENT_COLOR).pack(pady=10)


        self.conversation_area = ctk.CTkTextbox(self.chat_output_frame, wrap='word', state='disabled',
                                                 fg_color=self.FRAME_BG_COLOR, text_color=self.TEXT_COLOR,
                                                 border_color=self.HIGHLIGHT_COLOR, border_width=1)
        self.conversation_area.grid(row=0, column=0, sticky="nsew")

        self.typing_indicator = ctk.CTkLabel(self.chat_output_frame, text="", font=ctk.CTkFont(size=14, slant="italic"), text_color=self.ACCENT_COLOR)
        self.typing_indicator.grid(row=1, column=0, sticky="w", padx=10, pady=2)
        self.typing_animation_running = False
        self.typing_indicator.grid_remove() # Hide it initially

        # Bottom Frame for Tabs and Input
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # --- New Tabbed Interface for Tools ---
        self.tab_view = ctk.CTkTabview(self.bottom_frame, fg_color=self.FRAME_BG_COLOR,
                                       segmented_button_selected_color=self.HIGHLIGHT_COLOR,
                                       segmented_button_selected_hover_color=self.ACCENT_COLOR,
                                       segmented_button_unselected_color=self.FRAME_BG_COLOR,
                                       text_color=self.TEXT_COLOR)
        self.tab_view.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.tools_tab = self.tab_view.add("Tools")
        self.skills_tab = self.tab_view.add("Skills")
        self.files_tab = self.tab_view.add("Files")
        self.web_tab = self.tab_view.add("Web")
        self.stats_tab = self.tab_view.add("Stats")

        # Set tab background colors
        for tab in [self.tools_tab, self.skills_tab, self.files_tab, self.web_tab, self.stats_tab]:
            tab.configure(fg_color=self.FRAME_BG_COLOR)


        # --- Input Bar ---
        self.input_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5,10))
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Setup content for each part of the new layout
        self.setup_header()
        self.setup_input_bar()
        self.setup_tool_tabs()

        # Start background tasks
        self.start_system_monitor()
        self.populate_dashboard_tabs()

    def setup_header(self):
        ctk.CTkLabel(self.header_frame, text="🌐 AGP SYSTEM",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=self.ACCENT_COLOR).pack(side="left", padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.header_frame, text="Status: Initializing...",
                                          text_color=self.TEXT_COLOR, font=ctk.CTkFont(size=12))
        self.status_label.pack(side="right", padx=10)

        self.time_label = ctk.CTkLabel(self.header_frame, text="",
                                        text_color=self.TEXT_COLOR, font=ctk.CTkFont(size=12))
        self.time_label.pack(side="right", padx=10)

        threading.Thread(target=self.update_time, daemon=True).start()

    def setup_input_bar(self):
        self.voice_button = ctk.CTkButton(self.input_frame, text="🎙️", command=self.activate_voice,
                                           width=40, height=40, corner_radius=20,
                                           fg_color=self.HIGHLIGHT_COLOR, hover_color=self.ACCENT_COLOR,
                                           font=ctk.CTkFont(size=22))
        self.voice_button.grid(row=0, column=0, padx=(5, 10))

        self.input_box = ctk.CTkEntry(self.input_frame, placeholder_text="Type your command...",
                                       border_color=self.HIGHLIGHT_COLOR, fg_color=self.FRAME_BG_COLOR,
                                       text_color=self.TEXT_COLOR, corner_radius=15,
                                       font=ctk.CTkFont(size=14))
        self.input_box.grid(row=0, column=1, sticky="ew", ipady=8)
        self.input_box.bind("<Return>", self.send_command)

        self.send_button = ctk.CTkButton(self.input_frame, text="➤", command=self.send_command,
                                          width=40, height=40, corner_radius=20,
                                          font=ctk.CTkFont(size=18),
                                          fg_color=self.HIGHLIGHT_COLOR, hover_color=self.ACCENT_COLOR)
        self.send_button.grid(row=0, column=2, padx=(10, 5))

    def setup_tool_tabs(self):
        # This function will set up the content frames within each tab

        # --- Tools Tab (Running Apps) ---
        self.apps_list_frame = ctk.CTkScrollableFrame(self.tools_tab, height=150)
        self.apps_list_frame.pack(fill='x', padx=5, pady=5)
        ctk.CTkLabel(self.apps_list_frame, text="Running Applications (Click to Focus)", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        # --- Skills Tab (Custom Shortcuts) ---
        self.shortcuts_list_frame = ctk.CTkScrollableFrame(self.skills_tab, height=150)
        self.shortcuts_list_frame.pack(fill='x', padx=5, pady=5)
        ctk.CTkLabel(self.shortcuts_list_frame, text="Custom Shortcuts", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        # --- Files Tab (Recent Files) ---
        self.files_list_frame = ctk.CTkScrollableFrame(self.files_tab, height=150)
        self.files_list_frame.pack(fill='x', padx=5, pady=5)
        ctk.CTkLabel(self.files_list_frame, text="Recent Files", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

        # --- Web Tab (Placeholder) ---
        ctk.CTkLabel(self.web_tab, text="Web search and interaction features will appear here.").pack(padx=10, pady=10)

        # --- Stats Tab (System Monitor) ---
        self.system_monitor_plugin = [p for p in self.assistant.plugins if isinstance(p, SystemMonitorPlugin)][0]
        self.alarms_plugin = [p for p in self.assistant.plugins if isinstance(p, AlarmsPlugin)][0]

        self.cpu_label = ctk.CTkLabel(self.stats_tab, text="CPU: Loading...")
        self.cpu_label.pack(anchor="w", padx=10, pady=2)
        self.mem_label = ctk.CTkLabel(self.stats_tab, text="Memory: Loading...")
        self.mem_label.pack(anchor="w", padx=10, pady=2)
        self.bat_label = ctk.CTkLabel(self.stats_tab, text="Battery: Loading...")
        self.bat_label.pack(anchor="w", padx=10, pady=2)

        ctk.CTkLabel(self.stats_tab, text="Pending Reminders", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10,0))
        self.alarms_list_frame = ctk.CTkFrame(self.stats_tab)
        self.alarms_list_frame.pack(fill='x', expand=True, padx=10, pady=5)


    def start_system_monitor(self):
        """Starts a background thread to update system stats."""
        def monitor_loop():
            while True:
                # Update system stats
                cpu_usage = self.system_monitor_plugin.get_cpu_usage()
                mem_usage = self.system_monitor_plugin.get_memory_usage()
                battery_status = self.system_monitor_plugin.get_battery_status()

                self.cpu_label.configure(text=f"CPU: {cpu_usage:.1f}%")
                self.mem_label.configure(text=f"Memory: {mem_usage:.1f}%")

                if battery_status:
                    plugged_status = "🔌" if battery_status['power_plugged'] else "🔋"
                    self.bat_label.configure(text=f"Battery: {battery_status['percent']}% {plugged_status}")
                else:
                    self.bat_label.configure(text="Battery: N/A")

                self.system_monitor_plugin.check_battery_alert()

                # Update alarms
                for widget in self.alarms_list_frame.winfo_children():
                    widget.destroy()
                active_alarms = [a for a in self.alarms_plugin.alarms if a.is_alive()]
                if not active_alarms:
                    ctk.CTkLabel(self.alarms_list_frame, text="No pending reminders.").pack(anchor="w")
                else:
                    for alarm in active_alarms:
                        ctk.CTkLabel(self.alarms_list_frame, text=f"Reminder in {round(alarm.interval)}s").pack(anchor="w")

                time.sleep(2)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    def populate_dashboard_tabs(self):
        for frame in [self.apps_list_frame, self.files_list_frame, self.shortcuts_list_frame]:
            # Clear previous entries (skip label)
            for widget in frame.winfo_children()[1:]:
                widget.destroy()

        # Populate Running Apps (Tools)
        running_apps = dashboard_data.get_running_applications()
        for app_name in running_apps:
            app_label = ctk.CTkButton(self.apps_list_frame, text=app_name, fg_color="transparent", anchor="w",
                                      command=lambda name=app_name: window_manager.bring_window_to_front(name))
            app_label.pack(anchor="w", fill="x")

        # Populate Recent Files (Files)
        recent_files = dashboard_data.get_recent_files()
        for file_name in recent_files:
            ctk.CTkLabel(self.files_list_frame, text=file_name).pack(anchor="w")

        # Populate Custom Shortcuts (Skills)
        shortcuts = dashboard_data.get_custom_shortcuts()
        for shortcut_name in shortcuts:
            ctk.CTkLabel(self.shortcuts_list_frame, text=shortcut_name).pack(anchor="w")

        # Add a refresh button to the Tools tab
        self.refresh_button = ctk.CTkButton(self.tools_tab, text="Refresh", command=self.populate_dashboard_tabs,
                                             fg_color=self.HIGHLIGHT_COLOR, hover_color=self.ACCENT_COLOR)
        self.refresh_button.pack(pady=5, padx=5, side="bottom", anchor="e")

    def _animate_typing_indicator(self):
        """Animates the 'Thinking...' text."""
        if not self.typing_animation_running:
            return

        dots = self.typing_indicator.cget("text").count(".")
        new_dots = (dots + 1) % 4
        self.typing_indicator.configure(text=f"Thinking{'.' * new_dots}")

        # Schedule the next frame of the animation
        self.after(500, self._animate_typing_indicator)

    def update_time(self):
        """Updates the time label every second."""
        while True:
            try:
                self.time_label.configure(text=time.strftime("%H:%M:%S"))
                time.sleep(1)
            except Exception:
                # Window closed
                break

    def update_status(self, new_status):
        """Updates the assistant's status label."""
        self.status_label.configure(text=f"Status: {new_status}")

    def send_command(self, event=None):
        command = self.input_box.get()
        if command and not self.typing_animation_running:
            self.update_conversation(f"You: {command}", is_user=True)
            self.input_box.delete(0, 'end')

            # Start typing animation
            self.typing_indicator.grid()
            self.typing_animation_running = True
            self._animate_typing_indicator()

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
        # Stop typing animation when assistant responds
        if not is_user:
            self.typing_animation_running = False
            self.typing_indicator.grid_remove()

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
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.setup_tray_icon()
        self.start_wake_word_listener()
        self.mainloop()

    def create_tray_image(self):
        width = 64
        height = 64
        # A simple cyan circle on a dark background
        image = Image.new('RGB', (width, height), self.BG_COLOR)
        dc = ImageDraw.Draw(image)
        dc.ellipse(
            [(width // 4, height // 4), (width * 3 // 4, height * 3 // 4)],
            fill=self.ACCENT_COLOR
        )
        return image

    def setup_tray_icon(self):
        image = self.create_tray_image()
        menu = (pystray.MenuItem('Show', self.show_from_tray, default=True),
                pystray.MenuItem('Quit', self.quit_from_tray))
        self.tray_icon = pystray.Icon("nora", image, f"{self.assistant.assistant_name}", menu)

        # Run the icon in a separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def hide_to_tray(self):
        self.withdraw()

    def show_from_tray(self, icon, item):
        self.deiconify()

    def quit_from_tray(self, icon, item):
        self.tray_icon.stop()
        self.destroy()
