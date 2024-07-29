import os
import zipfile
import xml.etree.ElementTree as ET
import json
import shutil

# Helper function to extract and clean text from an XML element
def get_text(element):
    if element is not None:
        return ' '.join(''.join(element.itertext()).split())
    return ""

# Navigate through each file in the current directory
for filename in os.listdir('.'):
    if filename.endswith('.zip'):
        base_name = filename[:-4]
        print(f"Working on folder: {base_name}")

        # Extract the ZIP file
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(base_name)

        # Prepare JSON data structure
        json_data = {}

        # Count XML files
        xml_files = [f for f in os.listdir(base_name) if f.endswith('.xml')]
        print(f"Found {len(xml_files)} XML files in {base_name}")

        json_data = []

        # Process each XML file
        for xml_file in xml_files:
            tree = ET.parse(os.path.join(base_name, xml_file))
            root = tree.getroot()

            for annonce in root.findall('.//annonce'):
                identifiant = annonce.find('.//identifiant').text if annonce.find('.//identifiant') is not None else ""
                if identifiant:
                    entry = {
                        "ID": identifiant,
                        "Date": get_text(annonce.find('.//dateDeclaration')),
                        "Type": get_text(annonce.find('.//type')),
                        "themes": [get_text(theme) for theme in annonce.findall('.//theme')],
                        "Titre": get_text(annonce.find('.//titre')),
                        "SiegeSocial": get_text(annonce.find('.//siegeSocial')),
                        "Text": get_text(annonce.find('.//objet')),
                        "Word_count": len(get_text(annonce.find('.//objet')).split())
                    }

                    json_data.append(entry)

        # Write to JSON file
        with open(f"{base_name}.json", 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        # Remove the extracted folder
        shutil.rmtree(base_name)

        print(f"Completed processing and cleaning up for folder: {base_name}")
