import os
import tarfile
import json
import xml.etree.ElementTree as ET
import shutil

def get_text(element):
    if element is not None:
        return ' '.join(''.join(element.itertext()).split())
    return ""

def process_tar_files(file_names):
    for file_name in file_names:
        base_name = file_name.replace('.tar.gz', '')
        print(f"Working on folder: {base_name}")

        # Uncompress tar.gz file
        with tarfile.open(file_name, 'r:gz') as tar:
            tar.extractall(path=base_name)

        # Uncompress all .taz files before proceeding to XML processing
        for root, dirs, files in os.walk(base_name):
            for file in files:
                if file.endswith('.taz'):
                    taz_path = os.path.join(root, file)
                    with tarfile.open(taz_path, 'r:gz') as taz:
                        taz.extractall(path=root)
                        os.remove(taz_path)  # Optionally remove the .taz file after extraction

        # Create JSON file
        json_data = []
        xml_files_count = 0

        # Process XML files after all .taz files have been uncompressed
        for root, dirs, files in os.walk(base_name):
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
                        siege_social = get_text(annonce.find('.//siegeSocial'))  # Fixed this line
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

        with open(f"{base_name}.json", 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        print(f"Found {xml_files_count} XML files in {base_name}")
        print(f"Processed {len(json_data)} annonces out of {xml_files_count} XML files")

        # Delete the uncompressed folder to save space
        shutil.rmtree(base_name)

# Example usage
file_names = ["ASS_2020.tar.gz", "ASS_2021.tar.gz", "ASS_2022.tar.gz", "ASS_2023.tar.gz"]
process_tar_files(file_names)
