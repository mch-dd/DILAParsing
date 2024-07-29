import os
import json
import shutil
import xml.etree.ElementTree as ET
import subprocess

def parse_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        ID = root.find("FICHIERS_JOINTS/FICHIER_HTML").text.split("/")[-1].split(".")[0] if root.find("FICHIERS_JOINTS/FICHIER_HTML") is not None else ""
        Date = root.attrib.get("datedeclaration", "")
        Type = root.find("TYPE").attrib.get("code", "") if root.find("TYPE") is not None else ""
        themes = [theme.attrib.get("code", "") for theme in root.findall("THEMES/THEME")]
        Titre = root.find("TITRE").text if root.find("TITRE") is not None else ""
        SiegeSocial = root.find("SIEGE_SOCIAL").text if root.find("SIEGE_SOCIAL") is not None else ""
        Text = root.find("OBJET").text if root.find("OBJET") is not None else ""
        Word_count = len(Text.split()) if Text else 0
        
        return {
            "ID": ID,
            "Date": Date,
            "Type": Type,
            "Themes": themes,
            "Titre": Titre,
            "SiegeSocial": SiegeSocial,
            "Text": Text,
            "Word_count": Word_count
        }
    except ET.ParseError:
        return {}

def process_7z_files():
    processed_count = 0
    total_count = 0
    current_directory = os.getcwd()
    
    for file_name in os.listdir(current_directory):
        if file_name.endswith(".7z"):
            total_count += 1
            folder_name = file_name[:-3]
            print(f"Working on folder: {folder_name}")
            subprocess.run(["7z", "x", file_name], check=True)
            uncompressed_folder = os.path.join(current_directory, folder_name)
            
            json_data = []
            xml_count = 0
            
            for root, dirs, files in os.walk(uncompressed_folder):
                for file in files:
                    if file.endswith(".xml"):
                        xml_count += 1
                        xml_file_path = os.path.join(root, file)
                        entry = parse_xml(xml_file_path)
                        json_data.append(entry)
            
            print(f"Found {xml_count} XML files.")
            
            json_file_path = uncompressed_folder.replace("stock_assoc_", "") + ".json"
            with open(json_file_path, "w", encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)
            
            processed_count += 1
            shutil.rmtree(uncompressed_folder)  # Delete uncompressed folder
            print(f"Processed {processed_count} out of {total_count} files.")
            
    print("Processing complete.")

if __name__ == "__main__":
    process_7z_files()
