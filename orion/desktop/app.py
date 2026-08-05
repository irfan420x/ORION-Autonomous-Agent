"""
ORION Desktop GUI
=================

Real desktop application for ORION Autonomous Agent.
Opens as a native window, can be minimized, shows real system data.

Usage:
    python3 -m orion.desktop.app
"""

import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import os
import time
import threading
from datetime import datetime


class OrionDesktopApp:
    """Main ORION Desktop Application."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("⚡ ORION - Autonomous Intelligence System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a1a')
        self.root.minsize(1000, 600)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
        # Colors
        self.colors = {
            'bg_primary': '#0a0a1a',
            'bg_secondary': '#0d1117',
            'bg_card': '#161b22',
            'text_primary': '#e6edf3',
            'text_secondary': '#8b949e',
            'accent_cyan': '#00d4ff',
            'accent_blue': '#0969da',
            'accent_green': '#3fb950',
            'accent_orange': '#d29922',
            'accent_red': '#f85149',
            'accent_purple': '#bc8cff',
            'border': '#21262d',
        }
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.colors['bg_primary'])
        self.style.configure('TLabel', background=self.colors['bg_primary'], 
                           foreground=self.colors['text_primary'])
        self.style.configure('TButton', background=self.colors['bg_card'],
                           foreground=self.colors['text_primary'])
        
        # Build UI
        self._build_top_bar()
        self._build_sidebar()
        self._build_main_content()
        self._build_bottom_bar()
        
        # Start update loop
        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_top_bar(self):
        """Build the top header bar."""
        top = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=60)
        top.pack(fill='x', side='top')
        top.pack_propagate(False)
        
        # Time
        self.time_label = tk.Label(top, text="", font=('Segoe UI', 14, 'bold'),
                                   bg=self.colors['bg_secondary'], fg=self.colors['accent_cyan'])
        self.time_label.pack(side='left', padx=20)
        
        # Title
        title_frame = tk.Frame(top, bg=self.colors['bg_secondary'])
        title_frame.pack(side='left', expand=True)
        
        tk.Label(title_frame, text="⚡ ORION", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg_secondary'], fg=self.colors['accent_cyan']).pack()
        tk.Label(title_frame, text="AUTONOMOUS INTELLIGENCE SYSTEM", 
                font=('Segoe UI', 8), bg=self.colors['bg_secondary'],
                fg=self.colors['text_secondary']).pack()
        
        # Greeting
        self.greeting_label = tk.Label(top, text="", font=('Segoe UI', 11),
                                       bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        self.greeting_label.pack(side='right', padx=20)
    
    def _build_sidebar(self):
        """Build left sidebar with navigation."""
        sidebar = tk.Frame(self.root, bg=self.colors['bg_secondary'], width=200)
        sidebar.pack(fill='y', side='left')
        sidebar.pack_propagate(False)
        
        # Navigation items
        nav_items = [
            ("📊", "DASHBOARD"),
            ("🤖", "AGENT"),
            ("📋", "TASKS"),
            ("🧠", "MEMORY"),
            ("🌐", "WORLD MODEL"),
            ("🔧", "TOOLS"),
            ("💻", "TERMINAL"),
            ("⚙️", "SETTINGS"),
        ]
        
        for icon, label in nav_items:
            btn = tk.Button(sidebar, text=f"  {icon}  {label}", font=('Segoe UI', 10),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                          activebackground=self.colors['bg_card'], activeforeground=self.colors['accent_cyan'],
                          relief='flat', anchor='w', padx=20, pady=10,
                          command=lambda l=label: self._nav_click(l))
            btn.pack(fill='x')
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.colors['bg_card']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.colors['bg_secondary']))
        
        # Voice Status
        voice_frame = tk.Frame(sidebar, bg=self.colors['bg_card'], pady=10)
        voice_frame.pack(fill='x', padx=10, pady=20)
        
        tk.Label(voice_frame, text="🎙️", font=('Segoe UI', 20),
                bg=self.colors['bg_card']).pack()
        tk.Label(voice_frame, text="Listening...", font=('Segoe UI', 9),
                bg=self.colors['bg_card'], fg=self.colors['accent_green']).pack()
        
        # System Health
        health_frame = tk.Frame(sidebar, bg=self.colors['bg_card'], pady=10)
        health_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(health_frame, text="SYSTEM HEALTH", font=('Segoe UI', 8, 'bold'),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack()
        
        self.health_label = tk.Label(health_frame, text="98%", font=('Segoe UI', 24, 'bold'),
                                     bg=self.colors['bg_card'], fg=self.colors['accent_green'])
        self.health_label.pack()
        
        tk.Label(health_frame, text="All Systems Operational", font=('Segoe UI', 8),
                bg=self.colors['bg_card'], fg=self.colors['accent_green']).pack()
    
    def _build_main_content(self):
        """Build main content area with cards."""
        main = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Configure grid
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, weight=1)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        
        # Card 1: System Overview
        self._build_system_card(main, 0, 0)
        
        # Card 2: Active Tasks
        self._build_tasks_card(main, 0, 1)
        
        # Card 3: Memory Status
        self._build_memory_card(main, 0, 2)
        
        # Card 4: Schedule
        self._build_schedule_card(main, 1, 0)
        
        # Card 5: Quick Actions
        self._build_actions_card(main, 1, 1)
        
        # Card 6: Process Monitor
        self._build_process_card(main, 1, 2)
    
    def _build_card(self, parent, title, row, column, **kwargs):
        """Create a styled card frame."""
        card = tk.Frame(parent, bg=self.colors['bg_card'], padx=15, pady=15)
        card.grid(row=row, column=column, padx=5, pady=5, sticky='nsew', **kwargs)
        
        header = tk.Frame(card, bg=self.colors['bg_card'])
        header.pack(fill='x')
        
        tk.Label(header, text=title, font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(side='left')
        
        return card
    
    def _build_system_card(self, parent, row, column):
        """Build system overview card."""
        card = self._build_card(parent, "📊 SYSTEM OVERVIEW", row, column)
        
        # Status badge
        self.status_badge = tk.Label(card, text="OPTIMAL", font=('Segoe UI', 8, 'bold'),
                                     bg=self.colors['accent_green'], fg='white', padx=8, pady=2)
        self.status_badge.pack(anchor='e')
        
        # Health gauge
        self.system_health_label = tk.Label(card, text="100%", font=('Segoe UI', 36, 'bold'),
                                           bg=self.colors['bg_card'], fg=self.colors['accent_cyan'])
        self.system_health_label.pack(pady=10)
        tk.Label(card, text="HEALTH", font=('Segoe UI', 8),
                bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack()
        
        # Resource bars
        resources_frame = tk.Frame(card, bg=self.colors['bg_card'])
        resources_frame.pack(fill='x', pady=10)
        
        self.resource_bars = {}
        for i, (name, icon) in enumerate([("CPU", "💻"), ("MEMORY", "🧠"), ("DISK", "💾")]):
            frame = tk.Frame(resources_frame, bg=self.colors['bg_card'])
            frame.pack(fill='x', pady=2)
            
            tk.Label(frame, text=f"{icon} {name}", font=('Segoe UI', 9),
                    bg=self.colors['bg_card'], fg=self.colors['text_primary'], width=10, anchor='w').pack(side='left')
            
            bar_frame = tk.Frame(frame, bg=self.colors['border'], height=8)
            bar_frame.pack(side='left', fill='x', expand=True, padx=5)
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg=self.colors['accent_cyan'], height=8)
            bar.pack(side='left', fill='y')
            
            self.resource_bars[name] = {'bar': bar, 'frame': bar_frame}
            
            self.resource_bars[name]['label'] = tk.Label(frame, text="0%", font=('Segoe UI', 9),
                                                         bg=self.colors['bg_card'], fg=self.colors['accent_cyan'], width=6)
            self.resource_bars[name]['label'].pack(side='right')
    
    def _build_tasks_card(self, parent, row, column):
        """Build active tasks card."""
        card = self._build_card(parent, "📋 ACTIVE TASKS", row, column)
        
        tk.Label(card, text="3 Active", font=('Segoe UI', 8, 'bold'),
                bg=self.colors['accent_orange'], fg='white', padx=8, pady=2).pack(anchor='e')
        
        tasks = [
            ("Build ORION World Model", 65, self.colors['accent_blue']),
            ("Analyze Codebase", 40, self.colors['accent_blue']),
            ("Update Documentation", 10, self.colors['accent_orange']),
            ("Backup System", 0, self.colors['accent_orange']),
        ]
        
        for task_name, progress, color in tasks:
            task_frame = tk.Frame(card, bg=self.colors['bg_card'])
            task_frame.pack(fill='x', pady=5)
            
            # Status dot
            dot = tk.Canvas(task_frame, width=8, height=8, bg=self.colors['bg_card'], highlightthickness=0)
            dot.create_oval(0, 0, 8, 8, fill=color)
            dot.pack(side='left', padx=(0, 8))
            
            # Task info
            info_frame = tk.Frame(task_frame, bg=self.colors['bg_card'])
            info_frame.pack(side='left', fill='x', expand=True)
            
            tk.Label(info_frame, text=task_name, font=('Segoe UI', 9),
                    bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor='w')
            
            # Progress bar
            bar_frame = tk.Frame(info_frame, bg=self.colors['border'], height=4)
            bar_frame.pack(fill='x', pady=2)
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg=color, height=4, width=progress * 2)
            bar.pack(side='left', fill='y')
            
            # Percentage
            tk.Label(task_frame, text=f"{progress}%", font=('Segoe UI', 9),
                    bg=self.colors['bg_card'], fg=self.colors['text_secondary']).pack(side='right')
    
    def _build_memory_card(self, parent, row, column):
        """Build memory status card."""
        card = self._build_card(parent, "🧠 MEMORY STATUS", row, column)
        
        tk.Label(card, text="Active", font=('Segoe UI', 8, 'bold'),
                bg=self.colors['accent_green'], fg='white', padx=8, pady=2).pack(anchor='e')
        
        stats_frame = tk.Frame(card, bg=self.colors['bg_card'])
        stats_frame.pack(fill='both', expand=True, pady=10)
        
        stats = [
            ("12,458", "Memories"),
            ("3,256", "Entities"),
            ("128", "Sessions"),
            ("89%", "Knowledge Base"),
        ]
        
        for i, (value, label) in enumerate(stats):
            frame = tk.Frame(stats_frame, bg=self.colors['bg_primary'], padx=10, pady=10)
            frame.grid(row=i//2, column=i%2, padx=3, pady=3, sticky='nsew')
            
            tk.Label(frame, text=value, font=('Segoe UI', 16, 'bold'),
                    bg=self.colors['bg_primary'], fg=self.colors['accent_purple']).pack()
            tk.Label(frame, text=label, font=('Segoe UI', 8),
                    bg=self.colors['bg_primary'], fg=self.colors['text_secondary']).pack()
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
    
    def _build_schedule_card(self, parent, row, column):
        """Build today's schedule card."""
        card = self._build_card(parent, "📅 TODAY'S SCHEDULE", row, column)
        
        schedule = [
            ("09:00", "Project Meeting"),
            ("11:30", "Code Review"),
            ("14:00", "Research Session"),
            ("16:00", "Client Call"),
            ("18:30", "Gym Time"),
        ]
        
        for time_str, title in schedule:
            frame = tk.Frame(card, bg=self.colors['bg_card'])
            frame.pack(fill='x', pady=3)
            
            tk.Label(frame, text=time_str, font=('Segoe UI', 10, 'bold'),
                    bg=self.colors['bg_card'], fg=self.colors['accent_cyan'], width=8, anchor='w').pack(side='left')
            tk.Label(frame, text=title, font=('Segoe UI', 10),
                    bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(side='left', padx=10)
    
    def _build_actions_card(self, parent, row, column):
        """Build quick actions card."""
        card = self._build_card(parent, "⚡ QUICK ACTIONS", row, column)
        
        actions = [
            ("🚀", "Launch App"), ("🔍", "Search Web"), ("💻", "Terminal"), ("📝", "Notes"),
            ("🎙️", "Voice"), ("📸", "Screenshot"), ("📁", "Files"), ("📈", "Monitor"),
        ]
        
        actions_frame = tk.Frame(card, bg=self.colors['bg_card'])
        actions_frame.pack(fill='both', expand=True)
        
        for i, (icon, label) in enumerate(actions):
            btn = tk.Button(actions_frame, text=f"{icon}\n{label}", font=('Segoe UI', 8),
                          bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                          activebackground=self.colors['accent_cyan'], relief='flat',
                          width=8, height=3,
                          command=lambda l=label: self._action_click(l))
            btn.grid(row=i//4, column=i%4, padx=3, pady=3, sticky='nsew')
        
        for i in range(4):
            actions_frame.grid_columnconfigure(i, weight=1)
    
    def _build_process_card(self, parent, row, column):
        """Build process monitor card."""
        card = self._build_card(parent, "📈 SYSTEM MONITOR", row, column)
        
        # Header
        header = tk.Frame(card, bg=self.colors['bg_card'])
        header.pack(fill='x')
        tk.Label(header, text="PID", font=('Segoe UI', 8, 'bold'), bg=self.colors['bg_card'],
                fg=self.colors['text_secondary'], width=8, anchor='w').pack(side='left')
        tk.Label(header, text="NAME", font=('Segoe UI', 8, 'bold'), bg=self.colors['bg_card'],
                fg=self.colors['text_secondary'], width=12, anchor='w').pack(side='left')
        tk.Label(header, text="CPU", font=('Segoe UI', 8, 'bold'), bg=self.colors['bg_card'],
                fg=self.colors['text_secondary'], width=8, anchor='e').pack(side='right')
        tk.Label(header, text="MEM", font=('Segoe UI', 8, 'bold'), bg=self.colors['bg_card'],
                fg=self.colors['text_secondary'], width=8, anchor='e').pack(side='right')
        
        # Process list
        self.process_frame = tk.Frame(card, bg=self.colors['bg_card'])
        self.process_frame.pack(fill='both', expand=True)
        
        self.process_labels = []
    
    def _build_bottom_bar(self):
        """Build bottom input bar."""
        bottom = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=60)
        bottom.pack(fill='x', side='bottom')
        bottom.pack_propagate(False)
        
        # Input field
        self.input_var = tk.StringVar()
        input_field = tk.Entry(bottom, textvariable=self.input_var, font=('Segoe UI', 12),
                             bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                             insertbackground=self.colors['accent_cyan'], relief='flat')
        input_field.pack(side='left', fill='x', expand=True, padx=20, pady=15)
        input_field.bind('<Return>', lambda e: self._send_message())
        
        # Send button
        send_btn = tk.Button(bottom, text="🎤", font=('Segoe UI', 14),
                           bg=self.colors['accent_cyan'], fg='white', relief='flat',
                           width=3, command=self._send_message)
        send_btn.pack(side='right', padx=20, pady=15)
        
        # App dock
        dock_frame = tk.Frame(bottom, bg=self.colors['bg_secondary'])
        dock_frame.pack(side='right', padx=10)
        
        dock_apps = [("💻", "Term"), ("🌐", "Web"), ("📝", "Code"), ("📁", "Files"), ("⚡", "ORION")]
        for icon, label in dock_apps:
            btn = tk.Button(dock_frame, text=icon, font=('Segoe UI', 12),
                          bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                          relief='flat', width=3,
                          command=lambda l=label: self._dock_click(l))
            btn.pack(side='left', padx=2)
    
    def _update_loop(self):
        """Background update loop for real-time data."""
        while self._running:
            try:
                # Update time
                now = datetime.now()
                self.time_label.config(text=now.strftime("%H:%M:%S"))
                
                # Update greeting
                hour = now.hour
                greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
                self.greeting_label.config(text=f"{greeting}, IRFAN")
                
                # Update system stats
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self.resource_bars['CPU']['label'].config(text=f"{cpu:.1f}%")
                self.resource_bars['MEMORY']['label'].config(text=f"{mem.percent:.1f}%")
                self.resource_bars['DISK']['label'].config(text=f"{disk.percent:.1f}%")
                
                # Update bar widths
                for name, percent in [('CPU', cpu), ('MEMORY', mem.percent), ('DISK', disk.percent)]:
                    bar = self.resource_bars[name]['bar']
                    frame = self.resource_bars[name]['frame']
                    frame.update_idletasks()
                    max_width = frame.winfo_width()
                    bar.configure(width=int(max_width * percent / 100))
                
                # Update health
                health = 100 - max(cpu, mem.percent, disk.percent)
                self.system_health_label.config(text=f"{health:.0f}%")
                self.health_label.config(text=f"{health:.0f}%")
                
                # Update processes
                self._update_processes()
                
                time.sleep(2)
            except Exception as e:
                print(f"Update error: {e}")
                time.sleep(5)
    
    def _update_processes(self):
        """Update process list."""
        try:
            # Clear old labels
            for label in self.process_labels:
                label.destroy()
            self.process_labels.clear()
            
            # Get top processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] and pinfo['cpu_percent'] > 0:
                        processes.append(pinfo)
                except:
                    pass
            
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            for proc in processes[:5]:
                frame = tk.Frame(self.process_frame, bg=self.colors['bg_card'])
                frame.pack(fill='x')
                
                tk.Label(frame, text=str(proc['pid']), font=('Segoe UI', 9),
                        bg=self.colors['bg_card'], fg=self.colors['text_secondary'], width=8, anchor='w').pack(side='left')
                tk.Label(frame, text=proc['name'][:12], font=('Segoe UI', 9),
                        bg=self.colors['bg_card'], fg=self.colors['text_primary'], width=12, anchor='w').pack(side='left')
                tk.Label(frame, text=f"{proc.get('cpu_percent', 0):.1f}%", font=('Segoe UI', 9),
                        bg=self.colors['bg_card'], fg=self.colors['accent_cyan'], width=8, anchor='e').pack(side='right')
                tk.Label(frame, text=f"{proc.get('memory_percent', 0):.1f}%", font=('Segoe UI', 9),
                        bg=self.colors['bg_card'], fg=self.colors['accent_green'], width=8, anchor='e').pack(side='right')
                
                self.process_labels.append(frame)
        except Exception as e:
            pass
    
    def _nav_click(self, item):
        """Handle navigation click."""
        print(f"Navigate to: {item}")
    
    def _action_click(self, action):
        """Handle quick action click."""
        print(f"Action: {action}")
        if action == "Terminal":
            os.system("x-terminal-emulator &")
        elif action == "Files":
            os.system("xdg-open ~ &")
    
    def _dock_click(self, app):
        """Handle dock app click."""
        print(f"Open: {app}")
    
    def _send_message(self):
        """Handle message send."""
        message = self.input_var.get()
        if message:
            print(f"Message: {message}")
            self.input_var.set("")
    
    def _on_close(self):
        """Handle window close."""
        self._running = False
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Launch ORION Desktop GUI."""
    app = OrionDesktopApp()
    app.run()


if __name__ == "__main__":
    main()
