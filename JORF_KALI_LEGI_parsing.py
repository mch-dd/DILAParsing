import tarfile
import os
import re
import json
import gc  # Import the garbage collection module
from lxml import etree as ET

# Regex for HTML tag removal
html_tag_re = re.compile('<(?!br\\s*/?).*?>')

# Function to remove HTML tags, preserving <br/> tags, and replace newline characters
def clean_text(text):
    text_no_html = re.sub(html_tag_re, '', text)
    text_no_newlines = text_no_html.replace('\n', ' ')
    return text_no_newlines

def is_empty_file(file_path):
    return os.path.getsize(file_path) == 0

# Function to process an XML file
def process_xml(file_path, json_data):
    if is_empty_file(file_path):
        print(f"Skipping empty file: {file_path}")
        return

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()


        etat_tag = root.find(".//ETAT")
        etat_value = etat_tag.text.strip() if etat_tag is not None and etat_tag.text is not None else 'N/A'
        date_debut_tag = root.find(".//DATE_DEBUT")
        date_debut_value = date_debut_tag.text.strip() if date_debut_tag is not None and date_debut_tag.text is not None else 'N/A'
        titre_txt = root.find(".//TITRE_TXT")
        titre = titre_txt.get('c_titre_court', 'N/A') if titre_txt is not None else 'N/A'
        num = root.find(".//NUM")
        article = num.text if num is not None else 'N/A'
        contenu = root.find(".//BLOC_TEXTUEL/CONTENU")
        text = clean_text(''.join(contenu.itertext())) if contenu is not None else 'N/A'
        word_count = len(text.split())  # Count words in the cleaned text

        if text != 'N/A':
            json_data.append({
                "etat_value": etat_value,
                "date_debut_value": date_debut_value,
                "titre": titre,
                "article": article,
                "text": text,
                "word_count": word_count  # Add word count to the JSON data
            })
    
    except ET.XMLSyntaxError as e:
        print(f"Error parsing {file_path}: {e}")

# Extracts tar.gz files and processes the directories within
def extract_and_process_tar(tar_path, output_dir):
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(path=output_dir)
        process_directory(output_dir)
        cleanup_directory(output_dir)
    gc.collect()  # Perform garbage collection after each tar file processing

# Process all XML files in a directory
def process_directory(directory):
    json_data = []
    file_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                try:
                    process_xml(file_path, json_data)
                    if len(json_data) >= 10000:
                        save_json(json_data, directory, file_count)
                        json_data = []
                        file_count += 1
                        gc.collect()  # Clear memory after saving 10000 entries
                except Exception as e:
                    print(f"Failed to process file {file_path}: {e}")

    if json_data:
        save_json(json_data, directory, file_count)

# Save JSON to a file
def save_json(data, directory, file_count):
    with open(f'{directory}_{file_count+1}.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

import shutil  # Import shutil module for handling file operations

# Cleanup directory using shutil
def cleanup_directory(directory):
    shutil.rmtree(directory, ignore_errors=True)  # Remove the directory and all its contents


# Main function to process all tar.gz files in the current directory
def process_all_tar_files_in_current_directory():
    current_directory = os.getcwd()  # Get the current working directory
    for tar_file in os.listdir(current_directory):
        if tar_file.endswith('.tar.gz'):
            tar_path = os.path.join(current_directory, tar_file)
            output_dir = tar_path.replace('.tar.gz', '')
            extract_and_process_tar(tar_path, output_dir)
            print(f'Processing {tar_path}')

# Example: Process all tar.gz files in the current directory
process_all_tar_files_in_current_directory()

