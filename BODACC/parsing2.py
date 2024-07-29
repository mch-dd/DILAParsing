import os
import tarfile
import xml.etree.ElementTree as ET
import json
import re
import subprocess

def process_taz_file(taz_path, year, json_output, prefix, error_log):
    decompressed_file_path = taz_path.rstrip('.taz') + '.decompressed'

    # Uncompress the .taz file using 'uncompress'
    result = subprocess.run(['uncompress', '-c', taz_path], capture_output=True, text=False)
    
    if result.returncode != 0:
        log_error(taz_path, "", result.stderr, error_log)
        return

    # Write the decompressed data to a new file
    with open(decompressed_file_path, 'wb') as decompressed_file:
        decompressed_file.write(result.stdout)

    # Process the decompressed tar file
    with tarfile.open(decompressed_file_path, 'r') as taz:
        members = [m for m in taz.getmembers() if m.isfile() and m.name.endswith('.xml')]
        for member in members:
            taz.extract(member, path=os.path.dirname(decompressed_file_path))
            file_path = os.path.join(os.path.dirname(decompressed_file_path), member.name)
            try:
                process_xml_file(file_path, year, json_output, taz_path, prefix)
            except ET.ParseError as e:
                log_error(taz_path, member.name, e, error_log)
            finally:
                os.remove(file_path)  # Delete the extracted file
    os.remove(decompressed_file_path)  # Delete the decompressed tar file

def process_xml_file(xml_path, year, json_output, original_file, prefix):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    if prefix == "PCL":
        process_pcl_file(root, json_output, original_file)
    elif prefix == "RCS-B":
        process_rcs_b_file(root, json_output, original_file)
    elif prefix == "RCS-A":
        process_rcs_a_file(root, json_output, original_file)
    elif prefix == "BILAN":
        process_bilan_file(root, json_output, original_file)

def process_pcl_file(root, json_output, original_file):
    for annonce in root.findall('.//annonce'):
        data = {}
        nojo = annonce.findtext('nojo', default="")
        numeroAnnonce = annonce.findtext('numeroAnnonce', default="")
        numeroDepartement = annonce.findtext('numeroDepartement', default="")
        data['id'] = f"{nojo}_{numeroAnnonce}_{numeroDepartement}"
        data['tribunal'] = annonce.findtext('tribunal', default="")
        data['date'] = annonce.find('jugement/date').text if annonce.find('jugement/date') is not None else ""
        identifiant_client_index = [child.tag for child in annonce].index('identifiantClient')
        text_elements = annonce[identifiant_client_index+1:]
        text = "\n".join(ET.tostring(element, encoding='unicode') for element in text_elements).strip()
        text = re.sub(r'</[^>]+>', '\n', text)
        data['text'] = re.sub(r'</?[^>]+>', '', text).replace('\n', '\n')
        data['word_count'] = len(data['text'].split())
        data['original_file'] = original_file
        json_output.append(data)

def process_rcs_b_file(root, json_output, original_file):
    for avis in root.findall('.//avis'):
        data = {}
        nojo = avis.findtext('nojo', default="")
        numeroAnnonce = avis.findtext('numeroAnnonce', default="")
        numeroDepartement = avis.findtext('numeroDepartement', default="")
        data['id'] = f"{nojo}_{numeroAnnonce}_{numeroDepartement}"
        data['tribunal'] = avis.findtext('tribunal', default="")
        data['date'] = root.findtext('dateParution', default="")
        
        identifiant_client_index = [child.tag for child in avis].index('tribunal')
        text_elements = avis[identifiant_client_index+1:]
        text = "\n".join(ET.tostring(element, encoding='unicode') for element in text_elements).strip()
        text = re.sub(r'</[^>]+>', '\n', text)
        data['text'] = re.sub(r'</?[^>]+>', '', text).replace('\n', '\n')
        data['word_count'] = len(data['text'].split())
        data['original_file'] = original_file
        json_output.append(data)

def process_rcs_a_file(root, json_output, original_file):
    for avis in root.findall('.//avis'):
        data = {}
        nojo = avis.findtext('nojo', default="")
        numeroAnnonce = avis.findtext('numeroAnnonce', default="")
        numeroDepartement = avis.findtext('numeroDepartement', default="")
        data['id'] = f"{nojo}_{numeroAnnonce}_{numeroDepartement}"
        data['tribunal'] = avis.findtext('tribunal', default="")
        data['date'] = root.findtext('dateParution', default="")

        identifiant_client_index = [child.tag for child in avis].index('tribunal')
        text_elements = avis[identifiant_client_index+1:]
        text = "\n".join(ET.tostring(element, encoding='unicode') for element in text_elements).strip()
        text = re.sub(r'</[^>]+>', '\n', text)
        data['text'] = re.sub(r'</?[^>]+>', '', text).replace('\n', '\n')
        data['word_count'] = len(data['text'].split())
        data['original_file'] = original_file
        json_output.append(data)

def process_bilan_file(root, json_output, original_file):
    for avis in root.findall('.//avis'):
        data = {}
        nojo = avis.findtext('nojo', default="")
        numeroAnnonce = avis.findtext('numeroAnnonce', default="")
        numeroDepartement = avis.findtext('numeroDepartement', default="")
        data['id'] = f"{nojo}_{numeroAnnonce}_{numeroDepartement}"
        data['tribunal'] = avis.findtext('tribunal', default="")
        data['date'] = root.findtext('dateParution', default="")

        identifiant_client_index = [child.tag for child in avis].index('tribunal')
        text_elements = avis[identifiant_client_index+1:]
        text = "\n".join(ET.tostring(element, encoding='unicode') for element in text_elements).strip()
        text = re.sub(r'</[^>]+>', '\n', text)
        data['text'] = re.sub(r'</?[^>]+>', '', text).replace('\n', '\n')
        data['word_count'] = len(data['text'].split())
        data['original_file'] = original_file
        json_output.append(data)

def save_json(year, json_output, prefix):
    json_folder = f"Json_{prefix}"
    os.makedirs(json_folder, exist_ok=True)
    json_path = os.path.join(json_folder, f"{prefix}_{year}.json")
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_output, json_file, indent=4, ensure_ascii=False)
    print(f"\033[92mSaved JSON file: {json_path}\033[0m")

def log_error(taz_path, xml_file, error, error_log):
    with open(error_log, 'a') as log_file:
        log_file.write(f"Error processing {xml_file} in {taz_path}: {error}\n")

def main():
    root_directory = "FluxHistorique"
    error_log = "error_log.txt"

    for year in range(2016, 2017):
        year_str = f"BODACC_{year}"
        directory_path = os.path.join(root_directory, year_str)

        json_outputs = {
            "PCL": [],
            "RCS-B": [],
            "RCS-A": [],
            "BILAN": []
        }

        for root, _, files in os.walk(directory_path):
            for file_name in files:
                if file_name.endswith('.taz'):
                    if file_name.startswith('PCL'):
                        prefix = "PCL"
                    elif file_name.startswith('RCS-B'):
                        prefix = "RCS-B"
                    elif file_name.startswith('RCS-A'):
                        prefix = "RCS-A"
                    elif file_name.startswith('BILAN'):
                        prefix = "BILAN"
                    else:
                        continue
                    taz_path = os.path.join(root, file_name)
                    print(f"Processing file: {taz_path}")
                    process_taz_file(taz_path, year, json_outputs[prefix], prefix, error_log)
        
        for prefix, json_output in json_outputs.items():
            save_json(year, json_output, prefix)

if __name__ == "__main__":
    main()
