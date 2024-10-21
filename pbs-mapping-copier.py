import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import os
import sys

def process_files():
    try:
        # Load the Excel sheets into dataframes
        df_existing = pd.read_excel('copier.xlsx', sheet_name='existing-mappings')
        df_new = pd.read_excel('copier.xlsx', sheet_name='need-mapping')

        # Ensure both dataframes contain the matching column 'MAPPING_KEY'
        if 'MAPPING_KEY' not in df_existing.columns or 'MAPPING_KEY' not in df_new.columns:
            messagebox.showerror("Error", "Missing 'MAPPING_KEY' column in one or both sheets.")
            return

        # Perform the join operation
        merged_df = pd.merge(df_new, df_existing, on='MAPPING_KEY', how='left')

        # Save the result as a new Excel file
        output_path = os.path.join(os.getcwd(), "final_table.xlsx")
        merged_df.to_excel(output_path, index=False)

        # Display results in the GUI
        result_label.config(text=f"Processed {len(merged_df)} rows and {len(merged_df.columns)} columns.\n"
                                 f"Saved as: {output_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def close_app():
    root.destroy()

# Create the main GUI window
root = tk.Tk()
root.title("PBS Drug Mapping")
root.geometry("500x300")

# Create a frame to hold the content
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(expand=True, fill='both')

# Title Label
title_label = tk.Label(frame, text="PBS Drug Mapping", font=("Arial", 16))
title_label.pack(pady=10)

# Process Button
process_button = tk.Button(frame, text="Process Files", command=process_files, width=20, pady=5)
process_button.pack(pady=5)

# Result Label
result_label = tk.Label(frame, text="", font=("Arial", 12), wraplength=400)
result_label.pack(pady=10)

# Close Button
close_button = tk.Button(frame, text="CLOSE", command=close_app, width=20, pady=5)
close_button.pack(pady=5)

# Run the GUI loop
root.mainloop()
