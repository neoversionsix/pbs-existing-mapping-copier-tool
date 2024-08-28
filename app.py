from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
import webbrowser
import threading
import os
import sys
import traceback

app = Flask(__name__)

logs = []

file_a = None
file_b = None
key_column = None

def log_message(message):
    logs.append(message)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def read_excel_from_memory(file_storage):
    try:
        return pd.read_excel(file_storage, engine='openpyxl')
    except Exception as e:
        log_message(f"Error reading Excel file: {str(e)}")
        raise ValueError(f"Error reading Excel file: {str(e)}")

@app.route('/process', methods=['POST'])
def process():
    try:
        file_a = request.files['file_a']
        file_b = request.files['file_b']
        key_column = request.form['key_column']

        log_message(f"Processing files with key column: {key_column}")

        df_a = read_excel_from_memory(file_a)
        df_b = read_excel_from_memory(file_b)

        if key_column not in df_a.columns:
            raise ValueError(f"Key column '{key_column}' not found in file A")
        if key_column not in df_b.columns:
            raise ValueError(f"Key column '{key_column}' not found in file B")

        a_keys = set(df_a[key_column])
        b_keys = set(df_b[key_column])

        new_rows_count = sum(~df_b[key_column].isin(a_keys))
        non_existing_rows_count = sum(~df_a[key_column].isin(b_keys))

        log_message(f"New rows count: {new_rows_count}")
        log_message(f"Non-existing rows count: {non_existing_rows_count}")

        return jsonify({
            'new_rows_count': new_rows_count,
            'non_existing_rows_count': non_existing_rows_count
        })
    except Exception as e:
        log_message(f"An error occurred: {str(e)}")
        log_message(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        file_a = request.files['file_a']
        file_b = request.files['file_b']
        key_column = request.form['key_column']
        download_type = request.form['download_type']

        log_message(f"Downloading {download_type} with key column: {key_column}")

        df_a = read_excel_from_memory(file_a)
        df_b = read_excel_from_memory(file_b)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if download_type == 'new_rows':
                new_rows = df_b[~df_b[key_column].isin(df_a[key_column])]
                new_rows.to_excel(writer, index=False)
                filename = 'new_rows.xlsx'
            else:
                non_existing_rows = df_a[~df_a[key_column].isin(df_b[key_column])]
                non_existing_rows.to_excel(writer, index=False)
                filename = 'non_existing_rows.xlsx'

        output.seek(0)
        log_message(f"Download complete: {filename}")
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=filename)
    except Exception as e:
        log_message(f"An error occurred: {str(e)}")
        log_message(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify(logs)

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)
    webbrowser.open_new('http://localhost:5000/')
    app.run(debug=False, port=5000)