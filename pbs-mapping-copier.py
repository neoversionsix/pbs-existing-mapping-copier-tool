import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import pandas as pd
import io
import sys
import traceback
import os

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PBS Drug Mapping")
        self.geometry("800x600")
        
        # Initialize variables
        self.key_column = tk.StringVar(value='MAPPING_KEY')
        self.logs = []
        self.final_table = None
        
        # Set up the UI components
        self.create_widgets()
    
    def create_widgets(self):
        # Key column entry
        key_column_label = tk.Label(self, text="Matching Column:")
        key_column_label.pack()
        
        key_column_entry = tk.Entry(self, textvariable=self.key_column, width=50)
        key_column_entry.pack()
        
        # Process Files button
        process_button = tk.Button(self, text="Process copier.xlsx file", command=self.process_files)
        process_button.pack()
        
        # Results labels
        self.results_label = tk.Label(self, text="")
        self.results_label.pack()
        
        # Download Auto Mapping Table button
        self.download_button = tk.Button(self, text="Download Auto Mapping Table", command=self.download_table)
        self.download_button.pack()
        self.download_button['state'] = 'disabled'
        
        # Copy Auto Mapping Update Script to Clipboard button
        self.copy_script_button = tk.Button(self, text="Copy Auto Mapping Update Script to Clipboard", command=self.copy_update_script)
        self.copy_script_button.pack()
        self.copy_script_button['state'] = 'disabled'
        
        # Log Text widget
        log_label = tk.Label(self, text="Console Log:")
        log_label.pack()
        
        self.log_text = tk.Text(self, height=15)
        self.log_text.pack()
        
        # Close Button
        close_button = tk.Button(self, text="CLOSE", bg="red", fg="white", command=self.terminate_script)
        close_button.pack(pady=10)
    
    def log_message(self, message):
        self.logs.append(message)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
    
    def process_files(self):
        try:
            key_column = self.key_column.get()
            self.log_message(f"Processing files with key column: {key_column}")

            # Determine the correct path to 'copier.xlsx'
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            excel_file_path = os.path.join(application_path, 'copier.xlsx')
            
             # Read the Excel file 'copier.xlsx'
            df_a = pd.read_excel(excel_file_path, sheet_name='need-mapping', engine='openpyxl')
            df_b = pd.read_excel(excel_file_path, sheet_name='existing-mappings', engine='openpyxl')
            
            # Make sure the column the user enters for doing the mapping actually exists in both spreadsheets
            if key_column not in df_a.columns:
                raise ValueError(f"Key column '{key_column}' not found in sheet 'need-mapping'")
            if key_column not in df_b.columns:
                raise ValueError(f"Key column '{key_column}' not found in sheet 'existing-mappings'")
                
            # Merge the dataframes
            merged_df = pd.merge(df_a, df_b, on=key_column, how='inner')
            
            # Select required columns
            map_columns = [col for col in merged_df.columns if col.startswith('MAP_PBS_DRUG_ID_')]
            required_columns = ['MAPPED_SYNONYM_ID', 'PBS_CODE']
            missing_columns = [col for col in required_columns if col not in merged_df.columns]
            if missing_columns:
                raise ValueError(f"Columns {missing_columns} not found in the merged data.")
            if not map_columns:
                raise ValueError("No columns starting with 'MAP_PBS_DRUG_ID_' found in the merged data.")
            final_df = merged_df[map_columns + required_columns]
            
            # Remove duplicate rows
            final_df = final_df.drop_duplicates().reset_index(drop=True)
            
            # Save the final dataframe to an instance variable for later download
            self.final_table = final_df
            
            self.log_message(f"Created new table with {len(final_df)} rows and {len(final_df.columns)} columns")
            
            self.results_label.config(text=f"Created new table with {len(final_df)} rows and {len(final_df.columns)} columns")
            
            # Enable the download and copy script buttons
            self.download_button['state'] = 'normal'
            self.copy_script_button['state'] = 'normal'
            
        except Exception as e:
            self.log_message(f"An error occurred: {str(e)}")
            self.log_message(traceback.format_exc())
            messagebox.showerror("Error", str(e))
    
    def download_table(self):
        try:
            if self.final_table is None:
                messagebox.showerror("Error", "No data to save. Please process the files first.")
                return
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if file_path:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    self.final_table.to_excel(writer, index=False)
                self.log_message(f"Download complete: {file_path}")
        except Exception as e:
            self.log_message(f"An error occurred: {str(e)}")
            self.log_message(traceback.format_exc())
            messagebox.showerror("Error", str(e))
    
    def copy_update_script(self):
        try:
            if self.final_table is None:
                messagebox.showerror("Error", "No data to generate script. Please process the files first.")
                return
            
            script_template = """
;________________________________________________
;  {PBS_CODE} Mapping PBS_DRUG_ID: {MAP_PBS_DRUG_ID_} and SYNONYM_ID: {MAP_SYNONYM_ID_}
update into pbs_ocs_mapping P_O_M
set
    P_O_M.beg_effective_dt_tm = cnvtdatetime(curdate, 0008)
    ; Above line sets the activation time to today at 12:08 am, used to identify this type of update
    , P_O_M.end_effective_dt_tm = cnvtdatetime("31-DEC-2100")
    /*CHANGE THE ROW BELOW {MAP_PBS_DRUG_ID_}*/
    , P_O_M.pbs_drug_id = {MAP_PBS_DRUG_ID_} ; Swap With Pbs Drug Id that maps to the synonym id
    /*CHANGE THE ROW BELOW {MAP_SYNONYM_ID_}*/
    , P_O_M.synonym_id = {MAP_SYNONYM_ID_} ; Swap With Synonym Id that maps to the pbs_drug_id
    , P_O_M.drug_synonym_id = 0 ; clear multum mapping (multum mappings are not used)
    , P_O_M.main_multum_drug_code = 0 ; clear multum mapping
    , P_O_M.drug_identifier = "0" ; clear multum mapping
    , P_O_M.updt_dt_tm = cnvtdatetime(curdate,curtime3)
    , P_O_M.updt_id = reqinfo->updt_id
    , P_O_M.updt_cnt = P_O_M.updt_cnt + 1
where
    ;Update the next unused row
    P_O_M.pbs_ocs_mapping_id =
    (select min(pbs_ocs_mapping_id) from pbs_ocs_mapping where end_effective_dt_tm < sysdate)
    ; Only Update if the item is NOT already mapped
    and not exists
    (
        select 1
        from pbs_ocs_mapping
        /*CHANGE THE ROW BELOW {MAP_PBS_DRUG_ID_}*/
        where pbs_drug_id = {MAP_PBS_DRUG_ID_} ; Swap With Pbs Drug Id
        /*CHANGE THE ROW BELOW {MAP_SYNONYM_ID_}*/
        and synonym_id = {MAP_SYNONYM_ID_} ; Swap With Synonym Id
        and end_effective_dt_tm > sysdate
    )
;________________________________________________
"""
            full_script = ""
            for _, row in self.final_table.iterrows():
                block = script_template.format(
                    PBS_CODE=row['PBS_CODE'],
                    MAP_SYNONYM_ID_=row['MAPPED_SYNONYM_ID'],
                    MAP_PBS_DRUG_ID_=row['MAP_PBS_DRUG_ID_']
                )
                full_script += block

            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(full_script)
            self.log_message("Update script copied to clipboard!")
            messagebox.showinfo("Success", "Update script copied to clipboard!")
        except Exception as e:
            self.log_message(f"An error occurred: {str(e)}")
            self.log_message(traceback.format_exc())
            messagebox.showerror("Error", str(e))
    
    def terminate_script(self):
        self.log_message("Functionality Terminated, close this app")
        self.quit()

if __name__ == '__main__':
    app = Application()
    app.mainloop()
