import os
import tarfile
import json
import xml.etree.ElementTree as ET
import shutil

def get_text(element):
    """ Extracts and cleans text from an XML element. """
    if element is not None:
        return ' '.join(''.join(element.itertext()).split())
    return ""

def process_directories(directory):
    # Traverse the given directory for all .taz files and extract them
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.taz'):
                taz_path = os.path.join(root, file)
                with tarfile.open(taz_path, 'r:gz') as taz:
                    taz.extractall(path=root)
                    os.remove(taz_path)  # Remove the .taz file after extraction

    # Create JSON file
    json_data = []
    xml_files_count = 0

    # Process XML files after all .taz files have been uncompressed
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                xml_files_count += 1
                # Parse XML files
                xml_path = os.path.join(root, file)
                tree = ET.parse(xml_path)
                root_xml = tree.getroot()

                for annonce in root_xml.findall('.//annonce'):
                    identifiant = annonce.findtext('.//identifiant', '')
                    date_declaration = annonce.findtext('.//dateDeclaration', '')
                    type_code = annonce.find('.//type').get('code', '') if annonce.find('.//type') is not None else ''
                    themes = [theme.text.strip() for theme in annonce.findall('.//theme')]
                    titre = annonce.findtext('.//titre', '')
                    siege_social = get_text(annonce.find('.//siegeSocial'))
                    text = annonce.findtext('.//objet', '')
                    word_count = len(text.split())

                    entry = {
                        "ID": identifiant,
                        "Date": date_declaration,
                        "Type": type_code,
                        "Themes": themes,
                        "Titre": titre,
                        "SiegeSocial": siege_social,
                        "Text": text,
                        "Word_count": word_count
                    }

                    json_data.append(entry)

    # Save the processed data into a JSON file
    json_file_path = os.path.join(directory, 'processed_data.json')
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    print(f"Found {xml_files_count} XML files in the directory.")
    print(f"Processed {len(json_data)} annonces out of {xml_files_count} XML files.")

# Example usage, replace 'current_directory' with the actual directory you want to process
current_directory = 'ASS_2024'
process_directories(current_directory)
