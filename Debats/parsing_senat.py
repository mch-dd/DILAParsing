import os
import xml.etree.ElementTree as ET
import json

def normalize_tag(element):
    """Recursively convert all tags in the element tree to lowercase."""
    element.tag = element.tag.lower()
    for child in element:
        normalize_tag(child)

def process_xml_file(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Normalize all tags to lowercase
        normalize_tag(root)

        # Define the structure of the JSON output without "Annex_Amendement"
        output = {
            "Type_Publication": None,
            "Date": None,
            "Numero_Parution": None,
            "NumeroGrebiche": None,
            "Date_Seance": None,
            "Num_Jour_Session": None,
            "Num_Seance": None,
            "Session_Ord": None,
            "Text": None,
            "filename": os.path.basename(xml_file),
            "word_count": 0
        }

        # Find the <metadonnees> element
        metadonnees = root.find(".//metadonnees")
        if metadonnees is not None:
            output["Type_Publication"] = metadonnees.findtext("typepublication")
            output["Date"] = metadonnees.findtext("dateparution")
            output["Numero_Parution"] = metadonnees.findtext("numparution")
            output["NumeroGrebiche"] = metadonnees.findtext("numerogrebiche")
            output["Date_Seance"] = metadonnees.findtext("dateseance")
            output["Num_Jour_Session"] = metadonnees.findtext("numjoursession")
            output["Num_Seance"] = metadonnees.findtext("numseance")
            session = metadonnees.find(".//session")
            if session is not None:
                output["Session_Ord"] = session.findtext("sessionord")

        # Extract all <contenu> elements and concatenate their text
        contenu_texts = []
        for contenu in root.findall(".//contenu"):
            contenu_texts.append(''.join(contenu.itertext()))
        full_text = ''.join(contenu_texts)
        output["Text"] = full_text
        output["word_count"] = len(full_text.split())

        return output
    except ET.ParseError as e:
        print(f"Error parsing {xml_file}: {e}")
        return None

def process_subfolder(subfolder, output_base_folder):
    json_entries = []
    for xml_file in os.listdir(subfolder):
        if xml_file.endswith(".xml"):
            xml_path = os.path.join(subfolder, xml_file)
            json_entry = process_xml_file(xml_path)
            if json_entry:
                json_entries.append(json_entry)

    if json_entries:
        # Create output JSON file path
        subfolder_name = os.path.basename(subfolder)
        output_json_path = os.path.join(output_base_folder, f"{subfolder_name}.json")

        # Write JSON entries to a file
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_entries, f, ensure_ascii=False, indent=4)

def main(main_folder, output_base_folder):
    os.makedirs(output_base_folder, exist_ok=True)
    for root, dirs, _ in os.walk(main_folder):
        for subfolder in dirs:
            subfolder_path = os.path.join(root, subfolder)
            process_subfolder(subfolder_path, output_base_folder)

if __name__ == "__main__":
    main_folder = "/mnt/jupiter/DILA/Debats/SENAT"  # Replace with the path to your main folder
    output_base_folder = "/mnt/jupiter/DILA/Debats/SENAT/SENAT_JSONs"  # Replace with the path to your desired output base folder

    main(main_folder, output_base_folder)