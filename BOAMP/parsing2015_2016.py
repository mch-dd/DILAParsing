import os
import json
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import shutil

# Define the root directory where to start the search
root_directory = 'FluxHistorique/Boamp_v230'

# Years to look for
#years = [str(2006)]
#years = [[str(year) for year in range(2006, 2017)]]
years = ['2015', '2016']#, '2012', '2013', '2014']#, '2015', '2016']

def remove_specific_directories(directory, dir_names_to_remove):
    for subdir, dirs, files in os.walk(directory, topdown=False):  # Use topdown=False to allow directory removal
        for dir_name in dirs:
            if dir_name.lower() in dir_names_to_remove:
                full_dir_path = os.path.join(subdir, dir_name)
                try:
                    shutil.rmtree(full_dir_path)  # This removes the directory even if it has contents
                    print(f"Removed directory: {full_dir_path}")
                except Exception as e:
                    print(f"Error removing directory {full_dir_path}: {e}")


def find_and_process_year_folders(root_dir, years):
    for subdir, dirs, files in os.walk(root_dir):
        for year in years:
            if year in dirs:
                print(f"Found folder for year: {year}")
                process_year_folder(os.path.join(subdir, year), year)
                dirs.remove(year)  # To avoid re-traversing the directory

def process_year_folder(year_path, year):
    json_data = []
    for subdir, dirs, files in os.walk(year_path):
        for file in files:
            if file.endswith('.zip'):
                zip_path = os.path.join(subdir, file)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(subdir)

    xml_files = find_files(year_path, '.xml')
    print(f"Found {len(xml_files)} XML files for year {year}.")
    
    for index, xml_file in enumerate(xml_files):
        print(f"Processing XML file {index + 1}/{len(xml_files)} for year {year}.")
        json_entry = parse_xml(xml_file, year_path)  # Pass year_path as an argument here
        json_data.append(json_entry)
    
    # Save the JSON data to a file
    json_file_path = os.path.join(year_path, f"{year}.json")
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    
    # Cleanup: Delete all uncompressed files except the .zip and .json files
    for file in find_files(year_path, '.xml') + find_files(year_path, '.htm'):
        os.remove(file)

    remove_specific_directories(year_path, ['html', 'xml', 'htm'])
    print(f'\033[92mSaved {json_file_path} successfully\033[0m')

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

    # Change file extension to .HTM only if it ends with .htm
    if html_file_name.lower().endswith('.HTM'):
        html_file_name = html_file_name[:-4] + '.htm'

    if html_file_name:
        html_file_path = find_file_in_directory(year_path, html_file_name)
        if html_file_path:
            try:
                with open(html_file_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()
            except UnicodeDecodeError:
                with open(html_file_path, 'r', encoding='iso-8859-1') as html_file:
                    html_content = html_file.read()

            soup = BeautifulSoup(html_content, 'lxml')
            text = soup.get_text(separator=' ', strip=True)
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
