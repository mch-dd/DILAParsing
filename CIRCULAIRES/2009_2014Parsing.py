import os
import glob
import json
import tarfile
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
import re

def clean_text(text):
    # Replace any surrogate pairs with a replacement character or remove them
    # This version directly uses the replacement character method
    return text.encode('utf-8', 'replace').decode('utf-8')

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
            'Id_circulaire': root.findtext('ID_CIRCULAIRE', ""),
            'Etat': root.findtext('ETAT', ""),
            'Date_signature': root.findtext('DATE_SIGNATURE', ""),
            'Auteur': root.findtext('AUTEUR', ""),
            'Destinataire': root.findtext('DESTINATAIRE', ""),
            'nom_fichier_pdf': os.path.basename(root.findtext('NOM_FICHIER_PDF', ""))
        }
    except ET.ParseError as e:
        error_message = f"XML parse error in file {xml_file}: {e}\n"
        log_error(error_message)
        return None

def log_error(error_message):
    error_log_path = os.path.join(os.getcwd(), "error_log.txt")
    with open(error_log_path, 'a') as log_file:
        log_file.write(error_message)

def process_year(year):
    data = []
    for folder_name in ['xml', 'pdf']:
        directory = os.path.join(os.getcwd(), folder_name)
        tar_files = glob.glob(f'{directory}/{year}*.tar.gz')
        
        for tar_file in tar_files:
            print(f'Processing {tar_file}')
            with tarfile.open(tar_file, "r:gz") as tar:
                extract_folder = os.path.join(os.getcwd(), str(year), "extracted")
                os.makedirs(extract_folder, exist_ok=True)
                tar.extractall(path=extract_folder)

    xml_files = glob.glob(f'{os.path.join(os.getcwd(), str(year), "extracted")}/**/*.xml', recursive=True)
    for i, xml_file in enumerate(xml_files, start=1):
        print(f'Processing {xml_file}, {i} out of {len(xml_files)}')
        xml_data = parse_xml(xml_file)
        if xml_data:
            pdf_file_path = os.path.join(extract_folder, '**', xml_data['nom_fichier_pdf'])
            pdf_file_paths = glob.glob(pdf_file_path, recursive=True)
            if pdf_file_paths:
                text, success = extract_text_from_pdf(pdf_file_paths[0])
                if success:
                    xml_data['Text'] = text
                    xml_data['Word_count'] = len(text.split())
            data.append(xml_data)

    json_file_path = os.path.join(os.getcwd(), str(year), f"{year}.json")
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\u001b[42mCompleted processing for {year}. Found and processed {len(data)} XML files.\u001b[0m")
    os.system(f'rm -rf {os.path.join(os.getcwd(), str(year), "extracted")}')

# Loop to process each year from 2009 to 2014
years = ['2011', '2012', '2013', '2014']
for year in years:
    process_year(year)
