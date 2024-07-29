import os
import json
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import subprocess
import shutil
import os
import shutil
import zipfile
import json
import xml.etree.ElementTree as ET
import tarfile
import subprocess
import os

# Define the root directory where to start the search
root_directory = '2024'

# Years to look for
#years = [str(2006)]
#years = [[str(year) for year in range(2017, 2018)]]
years = ['2024']

def find_and_process_year_folders(root_dir, years):
    for subdir, dirs, files in os.walk(root_dir):
        for year in years:
            if year in dirs:
                print(f"Found folder for year: {year}")
                process_year_folder(os.path.join(subdir, year), year)
                dirs.remove(year)  # To avoid re-traversing the directory

#def process_year_folder(year_path, year):
#    json_data = []
#    created_dirs = []  # List to store directories created during extraction

    # Navigate the directory structure using os.walk
#    for subdir, dirs, files in os.walk(year_path):
#        for file in files:  # Limiting to first 5 files for demo purposes
#            if file.endswith('.taz'):
#                original_file_path = os.path.join(subdir, file)
#                output_dir = os.path.join(subdir, file[:-4])  # Directory for extracted contents
#                os.makedirs(output_dir, exist_ok=True)
#                created_dirs.append(output_dir)

                # Extract using zipfile module
#                try:
#                    with zipfile.ZipFile(original_file_path, 'r') as zip_ref:
#                        zip_ref.extractall(output_dir)
#                        print(f"Extraction of {original_file_path} successful.")
#                        # After extracting, look for .tar files and extract them
#                        extract_tar_files(output_dir)
#                except zipfile.BadZipFile:
#                    print(f"The file {original_file_path} is not a valid ZIP archive.")
#                except Exception as e:
#                    print(f"An error occurred while extracting {original_file_path}: {e}")

def process_year_folder(year_path, year):
    json_data = []
    created_dirs = []  # List to store directories created during extraction

    for subdir, dirs, files in os.walk(year_path):
        for file in files:
            if file.endswith('.tar.gz'):
                original_file_path = os.path.join(subdir, file)
                output_dir = os.path.join(subdir, file[:-7])  # Directory for extracted contents
                os.makedirs(output_dir, exist_ok=True)
                created_dirs.append(output_dir)

                # Extract using tarfile module
                try:
                    with tarfile.open(original_file_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(output_dir)
                        print(f"Extraction of {original_file_path} successful.")
                        # After extracting .tar.gz, now check for .taz files in the output directory
                        extract_taz_files(output_dir)
                except tarfile.TarError as e:
                    print(f"An error occurred while extracting {original_file_path}: {e}") 

    # Function to find XML files
    xml_files = find_files(year_path, '.xml')
    print(f"Found {len(xml_files)} XML files for year {year}.")

    # Process each XML file
    for index, xml_file in enumerate(xml_files):
        print(f"Processing XML file {index + 1}/{len(xml_files)} for year {year}.")
        json_entry = parse_xml(xml_file, year_path)
        json_data.append(json_entry)

    # Save the JSON data to a file
    json_file_path = os.path.join(year_path, f"{year}.json")
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    # Cleanup: Delete all created directories to free up space
    for dir_path in created_dirs:
        shutil.rmtree(dir_path)
    
    print(f'\033[92mSaved {json_file_path} successfully\033[0m')

def extract_tar_files(directory):
    """Recursively extract tar files found in directory."""
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.tar'):
                tar_path = os.path.join(subdir, file)
                try:
                    with tarfile.open(tar_path, 'r:') as tar:
                        tar.extractall(path=subdir)
                        print(f"Tar file {tar_path} extracted.")
                except tarfile.TarError:
                    print(f"Failed to extract tar file {tar_path}")


def extract_taz_files(directory):
    """Recursively extract taz files found in directory using the tar command."""
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.taz'):
                taz_path = os.path.join(subdir, file)
                extract_dir = taz_path[:-4]
                os.makedirs(extract_dir, exist_ok=True)
                try:
                    # Using the tar command to extract the files
                    subprocess.run(['tar', '-xzf', taz_path, '-C', extract_dir], check=True)
                    print(f"taz file {taz_path} extracted.")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to extract taz file {taz_path}: {e}")



def find_files(directory, extension):
    files_found = []
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                files_found.append(os.path.join(subdir, file))
    return files_found

def parse_xml(xml_file_path, year_path):
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
    except UnicodeDecodeError:
        with open(xml_file_path, 'r', encoding='iso-8859-1') as file:
            xml_content = file.read()

    xml_content = xml_content.replace('&deg;', '°')

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing {xml_file_path}: {e}")
        return {}

    json_entry = {
        "ID": root.findtext('.//IDWEB', ''),
        "Acheteur": root.findtext('.//DONNEES/IDENTITE/DENOMINATION', ''),
        "Acheteur_detail": root.findtext('.//DONNEES/IDENTITE/CORRESPONDANT', ''),
        "Acheteur_adresse": root.findtext('.//DONNEES/IDENTITE/ADRESSE', ''),
        "Acheteur_CP": root.findtext('.//DONNEES/IDENTITE/CP', ''),
        "Acheteur_Ville": root.findtext('.//DONNEES/IDENTITE/VILLE', ''),
        "Object": root.findtext('.//OBJET/OBJET_COMPLET', ''),
        "Date": root.findtext('.//DATE_PUBLICATION', '').replace('\n', ''),
        "Text": "",
        "Word_count": 0  # Initialize word count
    }
    html_file_name = root.findtext('.//NOM_HTML', '')
    if html_file_name.endswith('.HTM'):
        html_file_name = html_file_name.replace('.htm', '.HTM')   
    
    if html_file_name:
        html_file_path = find_file_in_directory(year_path, html_file_name)
        if html_file_path:
            try:
                with open(html_file_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()
            except UnicodeDecodeError:
                # Fallback encoding for files that aren't UTF-8
                with open(html_file_path, 'r', encoding='iso-8859-1') as html_file:
                    html_content = html_file.read()
            
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            # Extract text, cleaning it from any HTML tags and formatting
            text = soup.get_text(separator=' ', strip=True)
            # Store the clean text in the JSON entry
            json_entry["Text"] = text
            # Calculate and store the word count
            json_entry["Word_count"] = len(text.split())

    return json_entry

def find_file_in_directory(directory, file_name):
    for subdir, dirs, files in os.walk(directory):
        if file_name in files:
            return os.path.join(subdir, file_name)
    return None

# Start the process
find_and_process_year_folders(root_directory, years)
