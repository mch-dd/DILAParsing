import os
import glob
import json
import tarfile
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
import re

root_dir = 'FLUX'

def clean_text(text):
    text = re.sub(r'[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]', '', text)
    return text


def find_file_in_folder(folder_path, file_name):
    for root, _, files in os.walk(folder_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def extract_text_from_pdf(pdf_path):
    try:
        text = ""
        with open(pdf_path, 'rb') as f:
            pdf = PdfReader(f)
            for page in pdf.pages:
                text += page.extract_text() or ""
        return clean_text(text), True
    except Exception as e:
        error_message = f"Error extracting text from PDF {pdf_path}: {e}\n"
        log_error(error_message)
        return "", False

def parse_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        return {
            'Id_circulaire': root.find('.//ID_CIRCULAIRE').text or "",
            'Etat': root.find('.//ETAT').text or "",
            'Date_signature': root.find('.//DATE_SIGNATURE').text or "",
            'Auteur': root.find('.//AUTEUR').text or "",
            'Destinataire': root.find('.//DESTINATAIRE').text or "",
            'nom_fichier_pdf': root.find('.//NOM_FICHIER_PDF').text.split('/')[-1] or ""
        }
    except ET.ParseError as e:
        error_message = f"XML parse error in file {xml_file}: {e}\n"
        log_error(error_message)
        return None

def log_error(error_message):
    error_log_path = os.path.join(os.getcwd(), "error_log_20142023.txt")
    with open(error_log_path, 'a') as log_file:
        log_file.write(error_message)

data = []

for year in range(2023, 2024):
    year_folder = os.path.join(root_dir, str(year))
    if not os.path.exists(year_folder):
        continue

    json_file_path = os.path.join(year_folder, f"{year}.json")

    tar_files = glob.glob(f'{year_folder}/**/*.tar.gz', recursive=True)
    tar_files = tar_files

    print(f'Found {len(tar_files)} .tar.gz files')

    for i, tar_file in enumerate(tar_files, 1):
        print(f'Processing {i} of {len(tar_files)} in {year}')
        with tarfile.open(tar_file, "r:gz") as tar:
            extract_folder = tar_file[:-7]  # Remove .tar.gz extension
            os.makedirs(extract_folder, exist_ok=True)
            tar.extractall(path=extract_folder)
            
            xml_files = glob.glob(f'{extract_folder}/**/*.xml', recursive=True)
            for xml_file in xml_files:
                xml_data = parse_xml(xml_file)
                if xml_data:
                    xml_data['Text'] = ""
                    xml_data['Word_count'] = 0
                    pdf_file_path = ""
                    if xml_data['nom_fichier_pdf']:
                        search_path = os.path.join(extract_folder, '**', xml_data['nom_fichier_pdf'])
                        pdf_file_paths = glob.glob(search_path, recursive=True)
                        if pdf_file_paths:
                            pdf_file_path = pdf_file_paths[0]
                            text, success = extract_text_from_pdf(pdf_file_path)
                            if success:
                                xml_data['Text'] = clean_text(text)
                                xml_data['Word_count'] = len(text.split())
                    del xml_data['nom_fichier_pdf']  # Now safe to delete as xml_data is confirmed not None.
                    data.append(xml_data)

                # Additionally, make sure to only delete the key if it exists and xml_data is not None
                if xml_data and 'nom_fichier_pdf' in xml_data:
                    del xml_data['nom_fichier_pdf']

            os.system(f'rm -rf {extract_folder}')

    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\u001b[42mCompleted processing for {year_folder}. Found and processed {len(data)} XML files.\u001b[0m")
