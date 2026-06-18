import os
import sys
import pandas as pd
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "src", "models"))

from src.models import fitness
from src.models.woa import MetadataWOAAuditor
from main import run_pipeline
from src.utils.audit_report import generate_text_report

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TextRedirector:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, string):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", string)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        pass

class WOABaseline(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("WOA Baseline")
        self.geometry("1100x780")
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.header_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#0b0d19")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="WOA Baseline for Bias Auditing", 
            font=ctk.CTkFont(family="Outfit", size=26, weight="bold"),
            text_color="#3b82f6"
        )
        self.title_lbl.pack(anchor="w", padx=25, pady=(15, 0))
        
        self.subtitle_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="Whale Optimization Algorithm As Bias Auditing Tool", 
            font=ctk.CTkFont(family="Outfit", size=12),
            text_color="#9ca3af"
        )
        self.subtitle_lbl.pack(anchor="w", padx=25, pady=(2, 15))
        
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        
        self.tab_data = self.tabview.add("1. Data Prep")
        self.tab_audit = self.tabview.add("2. Bias Audit")
        self.tab_report = self.tabview.add("3. Audit Report")
        
        for tab in [self.tab_data, self.tab_audit, self.tab_report]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            
        self.build_data_tab()
        self.build_audit_tab()
        self.build_report_tab()
        
        self.base_df_path = None
        sys.stdout = TextRedirector(self.console_textbox)
        print("WOA Baseline initialized successfully.")
        
    def build_data_tab(self):
      
        self.data_grid = ctk.CTkFrame(self.tab_data, fg_color="transparent")
        self.data_grid.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.data_grid.grid_columnconfigure(0, weight=1) 
        self.data_grid.grid_columnconfigure(1, weight=1) 
        self.data_grid.grid_rowconfigure(0, weight=1)
        
        self.prep_frame = ctk.CTkFrame(self.data_grid, corner_radius=12)
        self.prep_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.prep_frame.grid_columnconfigure(0, weight=1)
        
        lbl = ctk.CTkLabel(self.prep_frame, text="Dataset Source Controller", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.btn_browse = ctk.CTkButton(self.prep_frame, text="📁 Browse Base CSV Dataset", command=self.browse_csv, height=40)
        self.btn_browse.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.file_status_lbl = ctk.CTkLabel(
            self.prep_frame, 
            text="No base dataset loaded.", 
            text_color="#9ca3af",
            font=ctk.CTkFont(size=12)
        )
        self.file_status_lbl.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.btn_pipe = ctk.CTkButton(
            self.prep_frame, 
            text="⚙️ Run Preprocessing Pipeline", 
            fg_color="#8b5cf6", 
            hover_color="#7c3aed",
            height=40,
            command=self.run_pipeline_thread
        )
        self.btn_pipe.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.preview_lbl = ctk.CTkLabel(self.prep_frame, text="Pipeline Stages Check:", font=ctk.CTkFont(size=14, weight="bold"))
        self.preview_lbl.grid(row=5, column=0, padx=20, pady=(25, 5), sticky="w")
        
        self.step1_lbl = ctk.CTkLabel(self.prep_frame, text="○ remove_duplicates.py", text_color="#9ca3af")
        self.step1_lbl.grid(row=6, column=0, padx=25, pady=2, sticky="w")
        self.step2_lbl = ctk.CTkLabel(self.prep_frame, text="○ handle_missing_data.py", text_color="#9ca3af")
        self.step2_lbl.grid(row=7, column=0, padx=25, pady=2, sticky="w")
        self.step3_lbl = ctk.CTkLabel(self.prep_frame, text="○ outlier_remover.py", text_color="#9ca3af")
        self.step3_lbl.grid(row=8, column=0, padx=25, pady=2, sticky="w")

        self.logs_frame = ctk.CTkFrame(self.data_grid, corner_radius=12)
        self.logs_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        self.logs_frame.grid_columnconfigure(0, weight=1)
        self.logs_frame.grid_rowconfigure(1, weight=1)
        
        lbl_console = ctk.CTkLabel(self.logs_frame, text="💻 Execution Log Terminal", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_console.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.console_textbox = ctk.CTkTextbox(self.logs_frame, font=ctk.CTkFont(family="Consolas", size=12), text_color="#38bdf8")
        self.console_textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.console_textbox.configure(state="disabled")

    def build_audit_tab(self):
        self.audit_grid = ctk.CTkFrame(self.tab_audit, fg_color="transparent")
        self.audit_grid.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.audit_grid.grid_columnconfigure(0, weight=1)
        self.audit_grid.grid_columnconfigure(1, weight=1) 
        self.audit_grid.grid_rowconfigure(0, weight=1)
        
        # LEFT: WOA Configuration & Trigger
        self.cfg_frame = ctk.CTkFrame(self.audit_grid, corner_radius=12)
        self.cfg_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        self.cfg_frame.grid_columnconfigure(0, weight=1)
        
        lbl = ctk.CTkLabel(self.cfg_frame, text="Whale Optimization Algorithm Setup", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")
        
        whales_lbl = ctk.CTkLabel(self.cfg_frame, text="Population Size (Number of Whales):", text_color="#9ca3af")
        whales_lbl.grid(row=1, column=0, padx=20, pady=(5, 2), sticky="w")
        self.entry_whales = ctk.CTkEntry(self.cfg_frame)
        self.entry_whales.insert(0, "20")
        self.entry_whales.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        iter_lbl = ctk.CTkLabel(self.cfg_frame, text="Max Search Iterations:", text_color="#9ca3af")
        iter_lbl.grid(row=3, column=0, padx=20, pady=(5, 2), sticky="w")
        self.entry_iter = ctk.CTkEntry(self.cfg_frame)
        self.entry_iter.insert(0, "325")
        self.entry_iter.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.btn_run_audit = ctk.CTkButton(
            self.cfg_frame, 
            text="🚀 Execute WOA Bias Audit", 
            fg_color="#8b5cf6", 
            hover_color="#7c3aed",
            height=40,
            command=self.run_audit_thread
        )
        self.btn_run_audit.grid(row=5, column=0, padx=20, pady=30, sticky="ew")
        
        self.results_frame = ctk.CTkFrame(self.audit_grid, corner_radius=12)
        self.results_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(2, weight=1)
        
        lbl_res = ctk.CTkLabel(self.results_frame, text="🚨 Audit Peak Bias Findings", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_res.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")
        
        self.lbl_conv = ctk.CTkLabel(self.results_frame, text="Bias Score: -", font=ctk.CTkFont(size=13))
        self.lbl_conv.grid(row=1, column=0, padx=25, pady=4, sticky="w")
        
        self.findings_textbox = ctk.CTkTextbox(
            self.results_frame, 
            font=ctk.CTkFont(family="Outfit", size=13),
            fg_color="transparent",
            text_color="#fda4af"
        )
        self.findings_textbox.grid(row=2, column=0, padx=20, pady=15, sticky="nsew")
        self.findings_textbox.insert("0.0", "Awaiting execution to locate bias hotspots...")
        self.findings_textbox.configure(state="disabled")

    def build_report_tab(self):
        self.report_grid = ctk.CTkFrame(self.tab_report, fg_color="transparent")
        self.report_grid.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.report_grid.grid_columnconfigure(0, weight=1)
        self.report_grid.grid_rowconfigure(1, weight=1)
        
        self.report_frame = ctk.CTkFrame(self.report_grid, corner_radius=12, border_color="#3b82f6", border_width=1)
        self.report_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10))
        self.report_frame.grid_columnconfigure(0, weight=1)
        
        self.report_header = ctk.CTkLabel(
            self.report_frame, 
            text="📄 Saved Bias Audit Report (data/bias_audit_report.txt)", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#3b82f6"
        )
        self.report_header.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.report_textbox = ctk.CTkTextbox(self.report_frame, height=220, font=ctk.CTkFont(family="Consolas", size=11), text_color="#38bdf8")
        self.report_textbox.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        self.report_textbox.insert("0.0", "No active report generated. Execute the WOA Bias Audit to compile details.")
        self.report_textbox.configure(state="disabled")
        
        self.swarm_frame = ctk.CTkFrame(self.report_grid, corner_radius=12)
        self.swarm_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(10, 0))
        self.swarm_frame.grid_columnconfigure(0, weight=1)
        self.swarm_frame.grid_rowconfigure(1, weight=1)
        
        self.swarm_lbl = ctk.CTkLabel(self.swarm_frame, text="👥 Search Agents Final State (Whales)", font=ctk.CTkFont(size=15, weight="bold"))
        self.swarm_lbl.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.swarm_textbox = ctk.CTkTextbox(self.swarm_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.swarm_textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.swarm_textbox.insert("0.0", "Run WOA audit to display search agent final positions.")
        self.swarm_textbox.configure(state="disabled")

    def run_pipeline_thread(self):
        self.btn_pipe.configure(state="disabled")
        self.step1_lbl.configure(text="● Removing Duplicates...", text_color="#3b82f6")
        threading.Thread(target=self.run_pipeline_action, daemon=True).start()
        
    def run_audit_thread(self):
        self.btn_run_audit.configure(state="disabled")
        threading.Thread(target=self.run_audit_action, daemon=True).start()

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.base_df_path = path
            self.file_status_lbl.configure(text=f"Loaded: {os.path.basename(path)}", text_color="#10b981")
            try:
                df = pd.read_csv(path)
                df.to_csv("data/raw/dirty_ACSIncome_2018_100K.csv", index=False)
                print("Dataset imported and saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read CSV: {e}")

    def run_pipeline_action(self):
        print("\n--- Running Preprocessing Pipeline ---")
        try:
            run_pipeline()
            print("Preprocessing pipeline complete. Provenance metadata exported successfully.")
            
            # Update step statuses
            self.step1_lbl.configure(text="✓ remove_duplicates.py", text_color="#10b981")
            self.step2_lbl.configure(text="✓ handle_missing_data.py", text_color="#10b981")
            self.step3_lbl.configure(text="✓ outlier_remover.py", text_color="#10b981")
            
            self.after(0, lambda: messagebox.showinfo("Success", "Pipeline processing complete!"))
        except Exception as e:
            print(f"Error during pipeline execution: {e}")
            self.step1_lbl.configure(text="✗ Failed", text_color="#ef4444")
        finally:
            self.btn_pipe.configure(state="normal")

    def run_audit_action(self):
        print("\n--- Running WOA Bias Audit ---")
        try:
            num_whales = int(self.entry_whales.get())
            max_iter = int(self.entry_iter.get())
        except ValueError:
            self.after(0, lambda: messagebox.showerror("Error", "Invalid inputs for search agents configuration!"))
            self.btn_run_audit.configure(state="normal")
            return
            
        fitness._logs_cache = None 
        
        try:
            auditor = MetadataWOAAuditor(num_whales=num_whales, max_iter=max_iter)
            result = auditor.run_audit()
            
            conv_score = result["max_fitness_score"]
            self.lbl_conv.configure(text=f"Bias Score: {conv_score:.6f}")
            
            self.findings_textbox.configure(state="normal")
            self.findings_textbox.delete("0.0", "end")
            details = (
                f"AUDIT SCORE SUMMARY:\n"
                f"---------------------------------\n"
                f"• Target Group Found: \"{result['demographic_group']}\"\n"
                f"• Pipeline Step:      \"{result['transformation_name']}\"\n"
                f"• Script File:        \"{result['script_name']}\"\n"
                f"• Max Fitness Bias:   {conv_score:.6f}"
            )
            self.findings_textbox.insert("0.0", details)
            self.findings_textbox.configure(state="disabled")
            
            try:
                generate_text_report(result, 0.0, 0)
            except Exception as report_err:
                print(f"Warning: could not write text report file: {report_err}")

            self.update_report()
            
            self.update_swarm_output(result['whales'], conv_score)
            
            print(f"WOA audit completed successfully. Global optimum bias fitness = {conv_score:.6f}")
            self.after(0, lambda: messagebox.showinfo("Success", "WOA Bias Audit execution complete!"))
            
        except Exception as e:
            print(f"Error during WOA execution: {e}")
        finally:
            self.btn_run_audit.configure(state="normal")

    def update_report(self):
        report_path = os.path.join(root_dir, "data", "bias_audit_report.txt")
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                text = f"Error reading report file: {e}"
        else:
            text = "Audit Report file (data/bias_audit_report.txt) not found. Please run the audit."
            
        self.report_textbox.configure(state="normal")
        self.report_textbox.delete("0.0", "end")
        self.report_textbox.insert("0.0", text)
        self.report_textbox.configure(state="disabled")

    def update_swarm_output(self, whales, max_fit):
        self.swarm_textbox.configure(state="normal")
        self.swarm_textbox.delete("0.0", "end")
        
        sorted_whales = sorted(whales, key=lambda x: x["fitness_score"], reverse=True)
        
        header = f"{'Agent ID':<10} | {'Coordinates [S, T, D]':<22} | {'Fitness Score':<15} | {'Step Name':<22} | {'Vulnerable demographic Group'}\n"
        separator = "-" * 110 + "\n"
        
        self.swarm_textbox.insert("end", header)
        self.swarm_textbox.insert("end", separator)
        
        for w in sorted_whales:
            w_id = f"Agent #{w['whale_id']}"
            pos = w.get("position", [])
            pos_str = f"[{int(round(pos[0]))}, {int(round(pos[1]))}, {int(round(pos[2]))}]" if len(pos) >= 3 else "N/A"
            fit_score = f"{w['fitness_score']:.6f}"
            trans = w.get("transformation_name", "None")[:20]
            demo = w.get("demographic_group", "None")
            
            row = f"{w_id:<10} | {pos_str:<22} | {fit_score:<15} | {trans:<22} | {demo}\n"
            self.swarm_textbox.insert("end", row)
            
        self.swarm_textbox.configure(state="disabled")

if __name__ == "__main__":
    app = WOABaseline()
    app.mainloop()
