import os
import zipfile
import glob
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import datetime

def unzip_files(year):
    directories = ['xml unitaire.zip', 'html.zip']
    year_str = str(year)  # Convert year to string
    for directory in directories:
        dir_name = directory.replace('.zip', '')  # Remove the .zip extension for the folder name
        zip_path = os.path.join(year_str, directory)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            extract_path = os.path.join(year_str, dir_name)
            zip_ref.extractall(extract_path)

def count_xml_files(year):
    xml_files = glob.glob(f"{year}/xml unitaire/**/*.xml", recursive=True)
    print(f"Year {year} has {len(xml_files)} XML files.")
    return xml_files

def parse_xml_and_generate_json(year, xml_files):
    year_str = str(year)  # Convert year to string
    data = []
    i = 0
    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Convert date format
        date = root.attrib['date']
        formatted_date = datetime.datetime.strptime(date, '%Y%m%d').strftime('%Y/%m/%d')

        for annonce in root.findall('ANNONCE_REF'):
            societe_nom = annonce.find('NOMS_SOCIETE/NOM_SOCIETE').text
            societe_siege = annonce.find('NOMS_SOCIETE/NOM_SOCIETE').attrib['siege']
            affaire_number = annonce.find('NUMERO_AFFAIRE').text
            fichier_html_path = annonce.find('FICHIERS_JOINTS/FICHIER_HTML').text
            categorie = annonce.find('CATEGORIE').attrib.get('name', '')
            categorie_1_element = annonce.find('CATEGORIE/CATEGORIE_N1')
            categorie_1 = categorie_1_element.attrib.get('name', '') if categorie_1_element is not None else ""
            categorie_2_element = annonce.find('CATEGORIE/CATEGORIE_N1/CATEGORIE_N2')
            categorie_2 = categorie_2_element.attrib.get('name', '') if categorie_2_element is not None else "" 
            html_filename = fichier_html_path.split('/')[-1]
            html_file_path = glob.glob(f"{year_str}/html/**/{html_filename}", recursive=True)
            text_content = ''
            word_count = 0
            if html_file_path:
                for encoding in ['utf-8', 'iso-8859-1', 'windows-1252']:
                    try:
                        with open(html_file_path[0], 'r', encoding=encoding) as f:
                            html_content = f.read()
                            soup = BeautifulSoup(html_content, 'html.parser')
                            text_content = soup.get_text(separator=' ', strip=True)
                            word_count = len(text_content.split())
                            break  # Exit the loop if file is successfully read
                    except UnicodeDecodeError:
                        continue  # Try the next encoding if an error occurs

            data.append({
                'Date': formatted_date,
                'Societe_nom': societe_nom,
                'Societe_siege': societe_siege,
                'Numero_affaire': affaire_number,
                "Categorie" : categorie,
                "Categorie_1" : categorie_1,
                "Categorie_2": categorie_2,
                'Text': text_content,
                'Word_count': word_count
            })
            i += 1
            print(f'Processed {i} files out of {len(xml_files)}')

    with open(f"BALO_{year_str}.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def clean_up_folders(year):
    year_str = str(year)  # Convert year to string
    directories = ['xml unitaire', 'html']  # Directories to clean up
    for dir_name in directories:
        folder_path = os.path.join(year_str, dir_name)
        for root_dir, dirs, files in os.walk(folder_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root_dir, name))
            for name in dirs:
                os.rmdir(os.path.join(root_dir, name))
        os.rmdir(folder_path)

def main():
    years = range(2005, 2017)
    for year in years:
        print(f"Processing year: {year}")
        unzip_files(year)
        xml_files = count_xml_files(year)
        parse_xml_and_generate_json(year, xml_files)
        clean_up_folders(year)
        print(f"\033[92mCompleted year: {year}\033[0m")

if __name__ == "__main__":
    main()
