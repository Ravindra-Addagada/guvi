"""
MicroStrategy Migration GUI - Jenkins Style
Build history at TOP showing Migration.py execution logs
FIXED VERSION - No lambda scope errors
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import sys
import json
from datetime import datetime
import glob

try:
    from mstrio.connection import Connection
    from mstrio.object_management.migration.migration import Migration
except ImportError:
    print("ERROR: mstrio-py library not installed!")
    print("Please install it with: pip install mstrio-py")
    sys.exit(1)


class JenkinsStyleMigrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Package Migration in different Environments")
        self.root.geometry("900x850")
        
        # Colors
        self.header_bg = "#4a5568"
        self.bg_color = "white"
        self.button_blue = "#4a90e2"
        
        self.root.configure(bg=self.bg_color)
        
        # Build storage
        self.builds_dir = "builds"
        os.makedirs(self.builds_dir, exist_ok=True)
        self.current_build_number = self.get_next_build_number()
        
        # Environment URLs
        self.environments = {
            "CRBP_LAB": "https://mstr-pbm-lab.cvshealth.com/MicroStrategyLibrary/",
            "CRBP_DEV": "https://mstr-pbm-dev.cvshealth.com/MicroStrategyLibrary/",
            "CRBP_QA": "https://mstr-pbm-qa.cvshealth.com/MicroStrategyLibrary/",
            "CRBP_PT": "https://mstr-pbm-pt.cvshealth.com/MicroStrategyLibrary/",
            "CRBP_PROD": "https://mstr-pbm-prod.cvshealth.com/MicroStrategyLibrary/"
        }
        
        # Variables
        self.environment_var = tk.StringVar(value="CRBP_DEV")
        self.action_var = tk.StringVar(value="Create Undo Package")
        self.project_name_var = tk.StringVar()
        self.package_name_var = tk.StringVar()
        
        # Build log
        self.current_build_log = []
        
        # Create UI
        self.create_header()
        self.create_build_history_section()
        self.create_form_section()
        self.create_console_section()
        
        self.log("Ready to start migration", "INFO")
    
    def get_next_build_number(self):
        """Get next build number"""
        builds = glob.glob(os.path.join(self.builds_dir, "build_*.json"))
        if not builds:
            return 1599  # Start from 1599 like in your Jenkins
        
        numbers = []
        for build in builds:
            try:
                num = int(os.path.basename(build).replace("build_", "").replace(".json", ""))
                numbers.append(num)
            except:
                pass
        
        return max(numbers) + 1 if numbers else 1599
    
    def load_build_history(self):
        """Load recent builds"""
        builds = []
        build_files = glob.glob(os.path.join(self.builds_dir, "build_*.json"))
        
        for build_file in sorted(build_files, reverse=True)[:5]:  # Last 5 builds
            try:
                with open(build_file, 'r') as f:
                    build_data = json.load(f)
                    builds.append(build_data)
            except:
                pass
        
        return builds
    
    def save_build(self, status, logs, windows_user="Unknown"):
        """Save build to history"""
        build_data = {
            "build_number": self.current_build_number,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_display": datetime.now().strftime("%b %d, %Y %I:%M %p"),
            "status": status,
            "environment": self.environment_var.get(),
            "action": self.action_var.get(),
            "project_name": self.project_name_var.get() or "inventory",
            "package_name": self.package_name_var.get(),
            "username": windows_user,
            "logs": logs
        }
        
        build_file = os.path.join(self.builds_dir, f"build_{self.current_build_number}.json")
        with open(build_file, 'w') as f:
            json.dump(build_data, f, indent=2)
        
        return build_data
    
    def load_build_logs(self, build_number):
        """Load logs for specific build"""
        build_file = os.path.join(self.builds_dir, f"build_{build_number}.json")
        
        if not os.path.exists(build_file):
            return None
        
        with open(build_file, 'r') as f:
            return json.load(f)
    
    def create_header(self):
        """Create header"""
        header_frame = tk.Frame(self.root, bg=self.header_bg, height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        breadcrumb = tk.Label(
            header_frame,
            text="jenkins > CI-Autheng > MCB Spcing > MicroStrategy Package Migration",
            font=("Arial", 10),
            fg="white",
            bg=self.header_bg,
            anchor="w"
        )
        breadcrumb.pack(side=tk.LEFT, padx=20, pady=15)
    
    def create_build_history_section(self):
        """Create build history section at TOP"""
        # Container
        history_container = tk.Frame(self.root, bg=self.bg_color)
        history_container.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Title
        title = tk.Label(
            history_container,
            text="Package Migration in different Environments",
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        title.pack(anchor="w")
        
        # Separator
        separator = tk.Frame(history_container, bg="#ddd", height=1)
        separator.pack(fill=tk.X, pady=(10, 15))
        
        # Migration History Header
        history_header = tk.Label(
            history_container,
            text="Migration History",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        history_header.pack(anchor="w", pady=(0, 10))
        
        # Build history frame (scrollable if needed)
        self.history_frame = tk.Frame(history_container, bg=self.bg_color)
        self.history_frame.pack(fill=tk.X)
        
        # Load and display builds
        self.refresh_build_history()
    
    def refresh_build_history(self):
        """Refresh build history display"""
        # Clear existing
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        builds = self.load_build_history()
        
        if not builds:
            no_builds = tk.Label(
                self.history_frame,
                text="No migrations yet. Click 'Migrate' to start your first migration.",
                font=("Arial", 10, "italic"),
                bg=self.bg_color,
                fg="#999"
            )
            no_builds.pack(anchor="w", pady=5)
        else:
            for build in builds:
                self.create_build_history_item(build)
    
    def create_build_history_item(self, build):
        """Create a build history item"""
        # Build container
        build_container = tk.Frame(self.history_frame, bg=self.bg_color)
        build_container.pack(fill=tk.X, pady=3)
        
        # Status icon
        if build['status'] == "SUCCESS":
            status_icon = "OK"
            status_color = "#5cb85c"
        elif build['status'] == "FAILURE":
            status_icon = "ERR"
            status_color = "#d9534f"
        else:
            status_icon = "RUN"
            status_color = "#999"
        
        # Build row
        build_row = tk.Frame(build_container, bg=self.bg_color, cursor="hand2")
        build_row.pack(fill=tk.X)
        
        # Status
        status_label = tk.Label(
            build_row,
            text=status_icon,
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=status_color,
            width=2
        )
        status_label.pack(side=tk.LEFT)
        
        # Build number and name
        build_text = f"#{build['build_number']} {build.get('project_name', 'inventory')}"
        build_label = tk.Label(
            build_row,
            text=build_text,
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#0066cc",
            cursor="hand2",
            anchor="w"
        )
        build_label.pack(side=tk.LEFT, padx=5)
        
        # Date
        date_label = tk.Label(
            build_row,
            text=build['date_display'],
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#666",
            anchor="w"
        )
        date_label.pack(side=tk.LEFT, padx=10)
        
        # Bind click to load logs
        for widget in [build_row, status_label, build_label, date_label]:
            widget.bind("<Button-1>", lambda e, bn=build['build_number']: self.load_build_console(bn))
    
    def load_build_console(self, build_number):
        """Load console logs for a specific build"""
        build_data = self.load_build_logs(build_number)
        
        if not build_data:
            return
        
        # Clear console
        self.console_text.delete("1.0", tk.END)
        
        # Header
        self.console_text.insert(tk.END, f"="*70 + "\n", "INFO")
        self.console_text.insert(tk.END, f"Migration #{build_number}\n", "INFO")
        self.console_text.insert(tk.END, f"Date: {build_data['date_display']}\n", "INFO")
        self.console_text.insert(tk.END, f"Status: {build_data['status']}\n", "INFO")
        self.console_text.insert(tk.END, f"Environment: {build_data['environment']}\n", "INFO")
        self.console_text.insert(tk.END, f"Action: {build_data.get('action', 'Create Undo Package')}\n", "INFO")
        self.console_text.insert(tk.END, f"Project: {build_data['project_name']}\n", "INFO")
        self.console_text.insert(tk.END, f"User: {build_data['username']}\n", "INFO")
        self.console_text.insert(tk.END, f"="*70 + "\n\n", "INFO")
        
        # Logs from Migration.py
        for log_entry in build_data.get('logs', []):
            level = log_entry.get('level', 'INFO')
            message = log_entry.get('message', '')
            timestamp = log_entry.get('timestamp', '')
            
            log_line = f"[{timestamp}] {message}\n"
            self.console_text.insert(tk.END, log_line, level)
        
        self.console_text.see(tk.END)
        
        # Show message
        messagebox.showinfo(
            "Migration Loaded",
            f"Loaded logs for Migration #{build_number}\n\n"
            f"Status: {build_data['status']}\n"
            f"Date: {build_data['date_display']}"
        )
    
    def create_form_section(self):
        """Create parameter form"""
        form_container = tk.Frame(self.root, bg=self.bg_color)
        form_container.pack(fill=tk.BOTH, padx=20, pady=10)
        
        # Subtitle
        subtitle = tk.Label(
            form_container,
            text="This migration requires parameters",
            font=("Arial", 11),
            bg=self.bg_color,
            fg="#666"
        )
        subtitle.pack(anchor="w", pady=(0, 15))
        
        # ENVIRONMENT
        self.create_param(form_container, "TARGET_ENVIRONMENT", "dropdown", self.environment_var,
                         list(self.environments.keys()))
        
        # ACTION
        self.create_param(form_container, "ACTION", "dropdown", self.action_var,
                         ["Create Undo Package", "Refresh Schema"])
        
        # PROJECT_NAME
        self.create_param(form_container, "PROJECT_NAME", "text", self.project_name_var,
                         ["Example: My Store Health Reporting (UAT)"])
        
        # PACKAGE_NAME (file path)
        self.create_param(form_container, "PACKAGE_NAME", "text", self.package_name_var,
                         ["Example: N:\\packages\\Migration_Package.mmp"])
        
        # Service Account Info
        info_frame = tk.Frame(form_container, bg=self.bg_color)
        info_frame.pack(fill=tk.X, pady=15)
        
        info_icon = tk.Label(
            info_frame,
            text="OPEN",
            font=("Arial", 14),
            bg=self.bg_color,
            fg="#4a90e2"
        )
        info_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        info_text = tk.Label(
            info_frame,
            text="This tool uses an authorized service account for migrations",
            font=("Arial", 9, "italic"),
            bg=self.bg_color,
            fg="#666",
            anchor="w"
        )
        info_text.pack(side=tk.LEFT, fill=tk.X)
        
        # Migrate button
        self.build_button = tk.Button(
            form_container,
            text="Migrate",
            command=self.run_migration,
            font=("Arial", 10, "bold"),
            bg=self.button_blue,
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        self.build_button.pack(anchor="w", pady=10)
    
    def create_param(self, parent, label_text, param_type, variable, options):
        """Create parameter field"""
        param_frame = tk.Frame(parent, bg=self.bg_color)
        param_frame.pack(fill=tk.X, pady=8)
        
        label = tk.Label(
            param_frame,
            text=label_text,
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        label.pack(anchor="w")
        
        if param_type == "dropdown":
            widget = ttk.Combobox(
                param_frame,
                textvariable=variable,
                values=options,
                state="readonly",
                width=35,
                font=("Arial", 10)
            )
        elif param_type == "password":
            widget = tk.Entry(
                param_frame,
                textvariable=variable,
                show="*",
                width=37,
                font=("Arial", 10)
            )
        else:
            widget = tk.Entry(
                param_frame,
                textvariable=variable,
                width=37,
                font=("Arial", 10)
            )
        
        widget.pack(anchor="w")
    
    def create_console_section(self):
        """Create console section"""
        console_container = tk.Frame(self.root, bg=self.bg_color)
        console_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        console_label = tk.Label(
            console_container,
            text="Console Output",
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        console_label.pack(anchor="w", pady=(0, 5))
        
        # Console text (increased height to 25)
        self.console_text = scrolledtext.ScrolledText(
            console_container,
            height=25,
            font=("Courier", 9),
            bg="black",
            fg="white",
            insertbackground="white"
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.console_text.tag_config("INFO", foreground="white")
        self.console_text.tag_config("SUCCESS", foreground="#5cb85c")
        self.console_text.tag_config("WARNING", foreground="#f0ad4e")
        self.console_text.tag_config("ERROR", foreground="#d9534f")
    
    def log(self, message, level="INFO"):
        """Add log to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        self.console_text.insert(tk.END, log_line, level)
        self.console_text.see(tk.END)
        
        # Add to current build log
        self.current_build_log.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def run_migration(self):
        """Run migration in background thread"""
        # Disable button
        self.build_button.config(
            state=tk.DISABLED, 
            text="Running Migration...", 
            bg="#6c757d"
        )
        
        # Clear log
        self.current_build_log = []
        
        # Run in thread
        thread = threading.Thread(target=self.execute_migration, daemon=True)
        thread.start()
    
    def execute_migration(self):
        """Execute migration"""
        try:
            # Get windows user for build history
            import getpass as gp
            try:
                windows_user = gp.getuser()
            except:
                windows_user = "Unknown"
            
            # Get parameters
            environment = self.environment_var.get()
            action = self.action_var.get()
            project = self.project_name_var.get() or "inventory"
            package_path = self.package_name_var.get()
            
            # Get URL
            base_url = self.environments.get(environment)
            
            self.log("="*60, "INFO")
            self.log(f"[Migration.py] Starting migration process", "INFO")
            self.log(f"[Migration.py] Build Number: {self.current_build_number}", "INFO")
            self.log("="*60, "INFO")
            self.log("")
            
            # Import config
            try:
                from config import get_service_account_password, SERVICE_ACCOUNT
                self.log("[Migration.py] Loaded service account configuration", "INFO")
            except ImportError:
                self.log("[Migration.py] ERROR: config.py not found", "ERROR")
                raise Exception("config.py not found. Run setup_service_account.py first.")
            
            # Get password
            self.log("[Migration.py] Retrieving service account password...", "INFO")
            password = get_service_account_password()
            if not password:
                raise Exception("Service account password not configured")
            
            self.log("[Migration.py] Service account password retrieved successfully", "SUCCESS")
            self.log("")
            
            # Connect
            self.log("[Migration.py] Connecting to MicroStrategy...", "INFO")
            self.log(f"[Migration.py]   URL: {base_url}", "INFO")
            self.log(f"[Migration.py]   Project: {project}", "INFO")
            self.log(f"[Migration.py]   User: {SERVICE_ACCOUNT['username']}", "INFO")
            
            conn = Connection(
                base_url,
                SERVICE_ACCOUNT['username'],
                password,
                project_name=project,
                login_mode=1
            )
            
            self.log("[Migration.py] Connected to MicroStrategy successfully", "SUCCESS")
            self.log(f"[Migration.py]   Project ID: {conn.project_id}", "INFO")
            self.log("")
            
            if action == "Create Undo Package":
                self.log("[Migration.py] Action: Apply Migration Package with Undo", "INFO")
                
                # Validate package
                if not package_path:
                    raise Exception("Package path is required")
                if not os.path.exists(package_path):
                    raise Exception(f"Package file not found: {package_path}")
                
                file_size = os.path.getsize(package_path)
                size_mb = file_size / (1024 * 1024)
                
                self.log("[Migration.py] Applying migration package...", "INFO")
                self.log(f"[Migration.py]   Package: {package_path}", "INFO")
                self.log(f"[Migration.py]   Size: {size_mb:.2f} MB", "INFO")
                self.log("[Migration.py]   This may take several minutes...", "INFO")
                
                migration = Migration.migrate_from_file(
                    connection=conn,
                    file_path=package_path,
                    name="Migration_Job",
                    package_type='project',
                    target_project_id=conn.project_id
                )
                
                self.log("[Migration.py] Package applied successfully!", "SUCCESS")
                self.log("[Migration.py] Undo package created automatically", "INFO")
                
                # Get environment info - safely handle different response types
                try:
                    if hasattr(migration, 'environments') and migration.environments:
                        self.log("[Migration.py] Importing to environments:", "INFO")
                        for env_info in migration.environments:
                            # Handle both dict and object types
                            if isinstance(env_info, dict):
                                env_name = env_info.get('name', 'Unknown')
                            else:
                                env_name = getattr(env_info, 'name', 'Unknown')
                            self.log(f"[Migration.py]   Environment: {env_name}", "INFO")
                except Exception as env_error:
                    # Don't fail migration if we can't parse environment info
                    self.log(f"[Migration.py]   Note: Could not parse environment details", "INFO")
                
                self.log("")
                self.log("[Migration.py] Migration package imported successfully!", "SUCCESS")
                self.log("")
                
                self.log("[Migration.py] Refreshing schema...", "INFO")
                try:
                    # Schema refresh API call
                    response = conn.post(
                        endpoint='/api/model/schema/reload',
                        headers={'X-MSTR-ProjectID': conn.project_id}
                    )
                    
                    if response.ok:
                        self.log("[Migration.py] Schema refresh initiated successfully", "SUCCESS")
                        self.log(f"[Migration.py]   Project: {project}", "INFO")
                        self.log(f"[Migration.py]   Status: Schema updating in background...", "INFO")
                    else:
                        self.log(f"[Migration.py] Schema refresh failed: {response.status_code}", "WARNING")
                        self.log(f"[Migration.py]   Response: {response.text}", "WARNING")
                        
                except Exception as schema_error:
                    self.log(f"[Migration.py] Schema refresh error: {str(schema_error)}", "WARNING")
                    self.log("[Migration.py]   Migration completed, but schema refresh failed", "WARNING")
                
            elif action == "Refresh Schema":
                self.log("[Migration.py] Action: Refresh Schema Only", "INFO")
                self.log("[Migration.py] Refreshing schema...", "INFO")
                
                try:
                    # Schema refresh API call
                    response = conn.post(
                        endpoint='/api/model/schema/reload',
                        headers={'X-MSTR-ProjectID': conn.project_id}
                    )
                    
                    if response.ok:
                        self.log("[Migration.py] Schema refresh initiated successfully", "SUCCESS")
                        self.log(f"[Migration.py]   Project: {project}", "INFO")
                        self.log(f"[Migration.py]   Status: Schema updating in background...", "INFO")
                    else:
                        self.log(f"[Migration.py] Schema refresh failed: {response.status_code}", "ERROR")
                        self.log(f"[Migration.py]   Response: {response.text}", "ERROR")
                        raise Exception(f"Schema refresh failed: {response.status_code}")
                        
                except Exception as schema_error:
                    self.log(f"[Migration.py] Schema refresh error: {str(schema_error)}", "ERROR")
                    raise
            
            self.log("")
            self.log("="*60, "SUCCESS")
            self.log("MIGRATION SUCCESSFUL", "SUCCESS")
            self.log("="*60, "SUCCESS")
            
            self.save_build("SUCCESS", self.current_build_log, windows_user)
            self.current_build_number += 1
            
            self.root.after(0, self.refresh_build_history)
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"Migration #{self.current_build_number - 1} completed successfully!"
            ))
            
        except Exception as error:
            # Capture error message BEFORE lambda
            error_message = str(error)
            build_num = self.current_build_number
            
            # Get windows_user for error case
            import getpass as gp
            try:
                windows_user = gp.getuser()
            except:
                windows_user = "Unknown"
            
            self.log("="*60, "ERROR")
            self.log(f"MIGRATION FAILED: {error_message}", "ERROR")
            self.log("="*60, "ERROR")
            
            self.save_build("FAILURE", self.current_build_log, windows_user)
            self.current_build_number += 1
            
            self.root.after(0, self.refresh_build_history)
            # FIXED: Use captured variables instead of 'e'
            self.root.after(0, lambda: messagebox.showerror(
                "Failed",
                f"Migration #{build_num} failed:\n\n{error_message}"
            ))
        
        finally:
            self.root.after(0, lambda: self.build_button.config(
                state=tk.NORMAL, text="Migrate", bg=self.button_blue
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = JenkinsStyleMigrationGUI(root)
    root.mainloop()
