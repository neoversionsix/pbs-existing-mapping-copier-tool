from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
import webbrowser
import threading
import os
import sys
import traceback

app = Flask(__name__, template_folder='.')

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


        #Make sure the column the user enters for doing the mapping actually exists in both spreadsheets
        if key_column not in df_a.columns:
            raise ValueError(f"Key column '{key_column}' not found in file A")
        if key_column not in df_b.columns:
            raise ValueError(f"Key column '{key_column}' not found in file B")

        # Merge the dataframes
        merged_df = pd.merge(df_a, df_b, on=key_column, how='inner')

        # Select required columns
        map_columns = [col for col in merged_df.columns if col.startswith('MAP_PBS_DRUG_ID_')]
        final_df = merged_df[map_columns + ['MAPPED_SYNONYM_ID', 'PBS_CODE']]

        #Remove duplicate rows
        final_df = final_df.drop_duplicates().reset_index(drop=True)

        # Save the final dataframe to a global variable for later download
        global final_table
        final_table = final_df

        log_message(f"Created new table with {len(final_df)} rows and {len(final_df.columns)} columns")

        return jsonify({
            'rows_count': len(final_df),
            'columns_count': len(final_df.columns)
        })
    except Exception as e:
        log_message(f"An error occurred: {str(e)}")
        log_message(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_table.to_excel(writer, index=False)
        output.seek(0)
        log_message("Download complete: final_table.xlsx")
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name='final_table.xlsx')
    except Exception as e:
        log_message(f"An error occurred: {str(e)}")
        log_message(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/generate-update-script', methods=['GET'])
def generate_update_script():
    global final_table
    if final_table is None:
        return jsonify({'error': 'No data processed yet'}), 400

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
    for _, row in final_table.iterrows():
        block = script_template.format(
            PBS_CODE=row['PBS_CODE'],
            MAP_SYNONYM_ID_=row['MAPPED_SYNONYM_ID'],
            MAP_PBS_DRUG_ID_=row['MAP_PBS_DRUG_ID_']
        )
        full_script += block

    return full_script

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify(logs)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    log_message("Functionality Terminated, close this app")
    os._exit(0)

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)
    webbrowser.open_new('http://localhost:5000/')
    app.run(debug=False, port=5000, use_reloader=False)