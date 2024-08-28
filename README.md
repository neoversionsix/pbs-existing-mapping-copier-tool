# pbs-existing-mapping-copier-tool
Loads the new PBS items from the most recent package and compares them with existing mappings. It then finds mappings that can be copied over to the new items, saving us a lot of time mapping new items.

Requirements.txt is just used to install packages quicky using:
pip install -r requirements.txt


To package the app use:
pyinstaller --add-data "index.html;." --hidden-import=openpyxl --name "PBS Drug Mapping" --onefile --windowed run.py