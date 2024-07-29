import os
import tarfile
import json
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader

def extract_and_process_tar_files(root_directory):
    tar_files = [f for f in os.listdir(root_directory) if f.endswith('.tar.gz')]
    
    print(f"Found {len(tar_files)} .tar.gz files.")
    i = 0

    for tar_file in tar_files:
        folder_name = tar_file[:-7]  # Remove .tar.gz extension
        folder_path = os.path.join(root_directory, folder_name)
        tar_path = os.path.join(root_directory, tar_file)
        
        # Extract tar file
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=folder_path)
        
        print(f"Uncompressed {tar_file} successfully.")
        
        # Process XML files
        xml_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))
        
        print(f"Found {len(xml_files)} xml files in {folder_name}.")
        
        # Parse XML and create JSON
        data_list = []
        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            data = {
                "ID_Diffuseur": root.find(".//identificationDiffuseur").attrib.get("IDI_COD_DIF", ""),
                "ID_Societe_country": root.find(".//identificationSociete").attrib.get("ISO_PAY_SS", ""),
                "ID_Societe_name": root.find(".//identificationSociete").attrib.get("ISO_NOM_SOC", ""),
                "ID_societe": root.find(".//identificationSociete").attrib.get("ISO_CD_ISI", ""),
                "InformationDeposee": root.find(".//InformationDeposee").attrib.get("INF_DAT_EMT", ""),
                "Title": root.find(".//InformationDeposee").attrib.get("INF_TIT_INF", ""),
                "Text": "",
                "Word_count": 0,
                "PDF_file_name": "",
                "PDF_folder_path": "",
                "XML_file_name": os.path.basename(xml_file)
            }
            
            content_file_name = root.find(".//FichierDeContenu").attrib.get("INF_FIC_NOM", "").split('/')[-1]
            content_file_path = find_file_in_folder(folder_path, content_file_name)
            
            if content_file_path and content_file_path.endswith('.pdf'):
                text, success = extract_text_from_pdf(content_file_path, root_directory)
                if success:
                    data['Text'] = text
                    data['Word_count'] = len(text.split())
                    data['PDF_file_name'] = os.path.basename(content_file_path)
                    data['PDF_folder_path'] = os.path.dirname(content_file_path)
                else:
                    log_error(content_file_path, root_directory)
            
            data_list.append(data)
        
        # Save JSON file
        json_file_path = os.path.join(root_directory, f"{folder_name}.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(data_list, json_file, ensure_ascii=False, indent=4)

        i += 1

        print(f'\033[94mProcessed {i} folders out of {len(tar_files)}\033[0m')

        print(f"\033[92mSaved {json_file_path} successfully.\033[0m")
        
        # Clean up: delete uncompressed folder
        delete_folder(folder_path)
    
    print('\033[92mFinished Task\033[0m')
        

def log_error(file_path, root_directory):
    error_message = f"Error parsing {file_path}\n"
    with open(os.path.join(root_directory, "ERROR_parsing_PDFs.txt"), "a") as error_log:
        error_log.write(error_message)

def find_file_in_folder(folder_path, file_name):
    for root, dirs, files in os.walk(folder_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return ""

def extract_text_from_pdf(pdf_path, root_directory):
    try:
        text = ""
        with open(pdf_path, 'rb') as f:
            pdf = PdfReader(f)
            for page_num in range(len(pdf.pages)):  # Correct loop usage
                page = pdf.pages[page_num]  # Access the page correctly for PyPDF2 >= 3.0.0
                text += page.extract_text()  # Correct method to extract text
        return text, True
    except Exception as e:
        print(f"\033[91mError processing {pdf_path}: {str(e)}\033[0m")
        return "", False

def delete_folder(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(folder_path)
    print(f"Deleted {folder_path} successfully.")

# List of folders to test the script on, replace with your actual root directory
root_directory = "AMF"
extract_and_process_tar_files(root_directory)
