import os
import glob
import json
import tarfile
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader

# Define your root directory
root_dir = 'FLUX'

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
        return text, True
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return "", False

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    id_circulaire = root.find('ID_CIRCULAIRE').text
    etat = root.find('ETAT').text
    date_signature = root.find('DATE_SIGNATURE').text
    auteur = root.find('AUTEUR').text
    destinataire = root.find('DESTINATAIRE').text
    nom_fichier_pdf = root.find('NOM_FICHIER_PDF').text.split('/')[-1] if root.find('NOM_FICHIER_PDF') is not None and root.find('NOM_FICHIER_PDF').text is not None else ""
    
    return {
        'Id_circulaire': id_circulaire,
        'Etat': etat,
        'Date_signature': date_signature,
        'Auteur': auteur,
        'Destinataire': destinataire,
        'nom_fichier_pdf': nom_fichier_pdf
    }

data = []  # Initialize as a list

# New JSON file path for consolidated data
json_file_path = os.path.join(root_dir, "2024.json")

# Find .tar.gz files only in the root directory, not considering subdirectories
tar_files = glob.glob(f'{root_dir}/*.tar.gz')

print(f'Found {len(tar_files)} .tar.gz files in the root directory')

for tar_file in tar_files:
    print(f'Processing {tar_file}')
    with tarfile.open(tar_file, "r:gz") as tar:
        extract_folder = tar_file[:-7]  # Remove .tar.gz extension
        os.makedirs(extract_folder, exist_ok=True)
        tar.extractall(path=extract_folder)
        
        xml_files = glob.glob(f'{extract_folder}/**/*.xml', recursive=True)
        for xml_file in xml_files:
            xml_data = parse_xml(xml_file)
            pdf_file_path = find_file_in_folder(extract_folder, xml_data['nom_fichier_pdf'])
            xml_data['Text'] = ""
            xml_data['Word_count'] = 0            
            if pdf_file_path:
                text, success = extract_text_from_pdf(pdf_file_path)
                if success:
                    xml_data['Text'] = text
                    xml_data['Word_count'] = len(text.split())
            # Exclude 'nom_fichier_pdf' from the data to be saved
            del xml_data['nom_fichier_pdf']
            data.append(xml_data)

        # Clean up extracted folder
        os.system(f'rm -rf {extract_folder}')

# Write the consolidated data to the JSON file
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Completed processing. Found and processed {len(data)} XML files.")
