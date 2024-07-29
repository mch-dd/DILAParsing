import os
import json
import tarfile
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

def extract_and_process_data(year):
    json_file_path = f'BALO_{year}.json'
    data = []  # Initialize as an empty list

    taz_files = [f for f in os.listdir() if f.endswith('.taz')]
    total_files = len(taz_files)  # Calculate once before the loop

    for i, tar_file in enumerate(taz_files, start=1):
        print(f'Processing file: {tar_file}, {i} out of {total_files}')
        extract_folder_path = tar_file.replace('.taz', '')

        if not os.path.exists(extract_folder_path):
            os.makedirs(extract_folder_path)

        with tarfile.open(tar_file) as tar:
            tar.extractall(path=extract_folder_path)

        for member in os.listdir(extract_folder_path):
            if member.startswith('balo_diff') and member.endswith('.xml'):
                xml_path = os.path.join(extract_folder_path, member)
                tree = ET.parse(xml_path)
                root = tree.getroot()

                for annonce_ref in root.findall('.//ANNONCE_REF'):
                    entry = {
                        'Date': datetime.now().strftime('%Y/%m/%d'),  # Placeholder for actual date extraction
                        'Societe_nom': annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE').text if annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE') is not None else "",
                        'Societe_siege': annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE').attrib.get('siege', "") if annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE') is not None else "",
                        'Numero_affaire': annonce_ref.find('NUMERO_AFFAIRE').text if annonce_ref.find('NUMERO_AFFAIRE') is not None else "",
                        'Categorie': "",
                        'Categorie_1': "",
                        'Categorie_2': "",
                        'Text': "",
                        'Word_count': 0
                    }
                    categorie_1_element = annonce_ref.find('CATEGORIE/CATEGORIE_N1')
                    if categorie_1_element is not None:
                        entry['Categorie_1'] = categorie_1_element.attrib.get('name', '')

                    categorie_2_element = annonce_ref.find('CATEGORIE/CATEGORIE_N1/CATEGORIE_N2')
                    if categorie_2_element is not None:
                        entry['Categorie_2'] = categorie_2_element.attrib.get('name', '')
                    
                    # Extracting text from FTCONTENT
                    ftcontent = annonce_ref.find('.//FTCONTENT')
                    if ftcontent is not None:
                        cdata_text = ftcontent.text
                        # Stripping CDATA markers
                        cdata_text = cdata_text.replace('<![CDATA[', '').replace(']]>', '').strip()
                        entry['Text'] = cdata_text
                        entry['Word_count'] = len(cdata_text.split())

                    data.append(entry)

        # Cleanup: remove extracted files
        for root, dirs, files in os.walk(extract_folder_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(extract_folder_path)

    # Write updated data to JSON file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print("\033[92mCompleted processing all files.\033[0m")

if __name__ == "__main__":
    extract_and_process_data()
