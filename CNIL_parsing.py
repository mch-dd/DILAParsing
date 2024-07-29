import os
import tarfile
import json
import xml.etree.ElementTree as ET
import re
import shutil

def extract_tar_gz(tar_path, extract_path):
    """Extracts a .tar.gz file to a specified directory."""
    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(path=extract_path)
        print(f'Extracted {tar_path}')
    except Exception as e:
        print(f'Error extracting {tar_path}: {e}')

def find_files(directory, extension):
    """Finds all files in directory and its subdirectories with the given extension."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                yield os.path.join(root, file)

def calculate_word_count(text):
    """Calculates the number of words in a string, stripping out HTML-like tags."""
    clean_text = re.sub('<[^<]+?>', '', text)  # Removing HTML-like tags
    words = clean_text.split()
    return len(words)

def extract_text_between_tags(file_path, start_tag='<CONTENU>', end_tag='</CONTENU>'):
    """Extracts text between given tags in a file treated as plain text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            pattern = re.compile(re.escape(start_tag) + '(.*?)' + re.escape(end_tag), re.DOTALL)
            matches = pattern.findall(content)
            return ' '.join(matches)
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""

root_directory = 'CNIL'
limit_to_first_folder = False

for index, folder in enumerate(os.listdir(root_directory)):
    if limit_to_first_folder and index > 0:
        break

    if folder.endswith('.tar.gz'):
        folder_path = os.path.join(root_directory, folder[:-7])
        extract_tar_gz(os.path.join(root_directory, folder), folder_path)

        xml_files = list(find_files(folder_path, '.xml'))
        total_xml_files = len(xml_files)
        print(f"Found {total_xml_files} XML files in {folder_path}.")

        json_data = []
        for processed_count, xml_file in enumerate(xml_files, start=1):
            try:
                # Use XML parsing for metadata extraction
                tree = ET.parse(xml_file)
                root = tree.getroot()

                meta = root.find(".//META_COMMUN")
                meta_cnil = root.find(".//META_SPEC/META_CNIL")

                # Extract <CONTENU> text as plain text
                cnil_text = extract_text_between_tags(xml_file)

                entry = {
                    "ID": meta.find("ID").text if meta.find("ID") is not None else "",
                    "Nature": meta.find("NATURE").text if meta.find("NATURE") is not None else "",
                    "Titre": meta_cnil.find("TITRE").text if meta_cnil.find("TITRE") is not None else "",
                    "Numero": meta_cnil.find(".//NUMERO").text if meta_cnil.find(".//NUMERO") is not None else "",
                    "Date_Text": meta_cnil.find(".//DATE_TEXTE").text if meta_cnil.find(".//DATE_TEXTE") is not None else "",
                    "Date_Publi": meta_cnil.find(".//DATE_PUBLI").text if meta_cnil.find(".//DATE_PUBLI") is not None else "",
                    "Etat_Juridique": meta_cnil.find(".//ETAT_JURIDIQUE").text if meta_cnil.find(".//ETAT_JURIDIQUE") is not None else "",
                    "Text": cnil_text,
                    "Word_count": calculate_word_count(cnil_text)
                }

                json_data.append(entry)

                # Update progress
                progress = (processed_count / total_xml_files) * 100
                print(f"Processed {processed_count}/{total_xml_files} XML files. Progress: {progress:.2f}%")
            except ET.ParseError:
                print(f"Error parsing XML file: {xml_file}")

        # Save to JSON file, adjusting path as needed
        json_path = os.path.join(root_directory, folder[:-7] + '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"\033[92mSuccessfully saved data to {json_path}\033[0m")
