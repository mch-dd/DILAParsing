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
import re


# Define the root directory where to start the search
root_directory = 'SENAT'

# Years to look for
#years = [str(2006)]
#years = [[str(year) for year in range(2017, 2018)]]
years = ['2011','2012','2013','2014','2015']#['2016','2017','2018','2019','2020',"2021", "2022", "2023", "2024"]

def calculate_word_count(text):
    """Calculates the number of words in a string, stripping out HTML-like tags."""
    clean_text = re.sub('<[^<]+?>', '', text)  # Removing HTML-like tags
    words = clean_text.split()
    return len(words)

def extract_text_from_xml(xml_content, tag='Contenu'):
    """Extracts and returns clean text from specified tag in XML content, maintaining paragraph separation."""
    try:
        root = ET.fromstring(xml_content)
        # Navigate to the 'Contenu' tag directly
        contents = root.findall('.//' + tag)
        all_text = []
        for content in contents:
            # Append a newline at the end of each paragraph for clear separation
            paragraphs = content.findall('.//Para')
            for para in paragraphs:
                text_parts = [elem.strip() for elem in para.itertext() if elem.strip()]
                clean_text = ' '.join(text_parts)
                all_text.append(clean_text)
            # Join all paragraphs with a newline character to maintain visual separation
            full_text = '\n'.join(all_text)
            all_text.append(full_text)  # Reset for next 'Contenu' section
        return '\n'.join(all_text)
    except ET.ParseError as e:
        print(f"Error parsing XML for text extraction: {e}")
        return ""

def clean_text(text):
    text = re.sub(r'[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]', '', text)
    return text

def find_and_process_year_folders(root_dir, years):
    for subdir, dirs, files in os.walk(root_dir):
        for year in years:
            if year in dirs:
                print(f"Found folder for year: {year}")
                process_year_folder(os.path.join(subdir, year), year)
                dirs.remove(year)  # To avoid re-traversing the directory

def process_year_folder(year_path, year):
    json_data = []
    created_dirs = []

    for subdir, dirs, files in os.walk(year_path):
        for file in files:
            if file.endswith('.taz'):
                tar_file_path = os.path.join(subdir, file)
                output_dir = os.path.join(subdir, file[:-4])
                os.makedirs(output_dir, exist_ok=True)
                created_dirs.append(output_dir)

                try:
                    with tarfile.open(tar_file_path, 'r:*') as tar:  # 'r:*' opens for reading with transparent compression
                        tar.extractall(path=output_dir)
                        print(f"Extraction of {tar_file_path} successful.")
                        extract_tar_files(output_dir)
                except tarfile.TarError as e:
                    print(f"Failed to extract tar file {tar_file_path}: {e}")

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
    
    text = extract_text_from_xml(xml_content)

    json_entry = {
        "Type_Publication": root.findtext('.//typeAssemblee', ''),
        "Date": root.findtext('.//DateParution', ''),
        "Session_Parlementaire": root.findtext('.//SessionParlementaire', ''),
        "Numero_Parution": root.findtext('.//LegislatureNumero', ''),
        "Numero": root.findtext('.//NumeroGrebiche', ''),
        "Date_Seance": root.findtext('.//DateSeance', ''),
        "Num_Jour_Session": root.findtext('.//numSeanceJour', ''),
        "Num_Seance": root.findtext('.//numSeance', ''),
        "Validite": root.findtext('.//validite', ''),
        "Annex_Amendement": False,  # Default value,
        "Text": clean_text(text),
        "Word_count": calculate_word_count(text),  # Initialize word count
    }

    # Check for the presence of <ArticleAmendementAnnexe>
    if root.find('.//ArticleAmendementAnnexe') is not None:
        json_entry["Annex_Amendement"] = True

    return json_entry

def find_file_in_directory(directory, file_name):
    for subdir, dirs, files in os.walk(directory):
        if file_name in files:
            return os.path.join(subdir, file_name)
    return None

# Start the process
find_and_process_year_folders(root_directory, years)
