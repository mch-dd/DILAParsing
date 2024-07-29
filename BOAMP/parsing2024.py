import os
import json
import subprocess
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# Function to parse XML files
def parse_xml(xml_file_path, year_path):
    # Try to open the XML file
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
    except UnicodeDecodeError:
        # If UnicodeDecodeError occurs, try opening with a different encoding
        with open(xml_file_path, 'r', encoding='iso-8859-1') as file:
            xml_content = file.read()

    # Replace special characters
    xml_content = xml_content.replace('&deg;', '°')

    # Parse XML content
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing {xml_file_path}: {e}")
        return {}

    # Extract relevant information from XML
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
        "Word_count": 0,  # Initialize word count
    }
    
    # Find corresponding HTML file
    html_file_name = root.findtext('.//NOM_HTML', '')
    if html_file_name.endswith('.HTM'):
        html_file_name = html_file_name.replace('.htm', '.HTM')

    # If HTML file found, extract text
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

            # Parse HTML content
            soup = BeautifulSoup(html_content, 'lxml')
            # Extract text, clean it, and store in JSON entry
            text = soup.get_text(separator=' ', strip=True)
            json_entry["Text"] = text
            # Calculate word count
            json_entry["Word_count"] = len(text.split())

    return json_entry

# Function to find a file in a directory
def find_file_in_directory(directory, filename):
    for root, dirs, files in os.walk(directory):
        if filename in files:
            return os.path.join(root, filename)
    return None

# Main script
root_directory = "2024"
json_filename = "2024.json"
year_path = os.path.join(root_directory, json_filename.split('.')[0])

# Step 1: Save parsed information in a JSON file
data = []

# Step 2: Collect all .taz files and uncompress them
print("Collecting and uncompressing .taz files...")
taz_files = [file for file in os.listdir(root_directory) if file.endswith('.taz')]
for taz_file in taz_files:
    subprocess.run(['tar', '-xf', os.path.join(root_directory, taz_file)])

# Step 3: Collect all XML files
print("Collecting XML files...")
xml_files = [os.path.join(root, file) for root, _, files in os.walk(root_directory) for file in files if file.endswith('.xml')]

# Step 4: Parse XML files and save information in the JSON file
print("Parsing XML files...")
for xml_file in xml_files:
    entry = parse_xml(xml_file, year_path)
    if entry:
        data.append(entry)

# Step 5: Save all information in the JSON file
print("Saving data to JSON file...")
with open(json_filename, 'w') as json_file:
    json.dump(data, json_file, indent=4)

# Step 6: Delete uncompressed folders
print("Cleaning up uncompressed folders...")
for folder in os.listdir(root_directory):
    if os.path.isdir(os.path.join(root_directory, folder)):
        subprocess.run(['rm', '-rf', os.path.join(root_directory, folder)])

print("Process completed successfully.")
