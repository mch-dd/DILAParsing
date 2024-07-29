import os
import subprocess
import json
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader

def extract_and_process_folders(root_directory):
    for folder_name in os.listdir(root_directory):
        folder_path = os.path.join(root_directory, folder_name)
        if os.path.isdir(folder_path):
            process_folder(folder_path, folder_name)

def process_folder(folder_path, folder_name):
    data_list = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.taz'):
            original_file_path = os.path.join(folder_path, file_name)
            output_dir = os.path.join(folder_path, file_name[:-12])
            os.makedirs(output_dir, exist_ok=True)

            new_file_path = original_file_path[:-4] + '.tar'
            os.rename(original_file_path, new_file_path)

            command = ['tar', '-xvf', new_file_path, '-C', output_dir]
            try:
                subprocess.run(command, check=True)
                print(f"Extraction of {new_file_path} successful.")
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while extracting {new_file_path}: {e}")
            
            os.rename(new_file_path, original_file_path)

            for root, _, files in os.walk(output_dir):
                for xml_file in files:
                    if xml_file.endswith('.xml'):
                        xml_path = os.path.join(root, xml_file)
                        data_list.extend(process_xml_file(xml_path, folder_path))

            delete_folder(output_dir)

    json_file_path = os.path.join(folder_path, f"{folder_name}.json")
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=4)
    print(f"Saved {json_file_path} successfully.")

    json_file_path = os.path.join(folder_path, f"{folder_name}.json")
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=4)
    print(f"Saved {json_file_path} successfully.")


def process_xml_file(xml_path, root_directory):
    entries = []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for annonce_ref in root.findall(".//ANNONCE_REF"):
        data = {
            "ID": annonce_ref.find(".//NOJO").text if annonce_ref.find(".//NOJO") is not None else "",
            "Texte_Nature": annonce_ref.find(".//TEXTE_NATURE").text if annonce_ref.find(".//TEXTE_NATURE") is not None else "",
            "Date": annonce_ref.find(".//TEXTE_DATE").text if annonce_ref.find(".//TEXTE_DATE") is not None else "",
            "Titre": annonce_ref.find(".//TEXTE_TITRE").text if annonce_ref.find(".//TEXTE_TITRE") is not None else "",
            "Text": "",
            "Word_Count": 0
        }
        
        nom_html = annonce_ref.find(".//NOM_HTML").text if annonce_ref.find(".//NOM_HTML") is not None else ""
        if nom_html:
            pdf_path = find_file_in_folder(root_directory, nom_html)
            if pdf_path:
                text, success = extract_text_from_pdf(pdf_path)
                if success:
                    data['Text'] = text
                    data['Word_Count'] = len(text.split())
        entries.append(data)
    return entries

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

def delete_folder(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(folder_path)
    print(f"Deleted {folder_path} successfully.")

# Replace 'root_directory' with the path to your actual root directory
root_directory = "BOCC"
extract_and_process_folders(root_directory)
