import tarfile
import os
import json
import xml.etree.ElementTree as ET
import subprocess
import zipfile

def extract_file(file_path, extract_to):
    """Extract a file with flexible handling for .tar.gz, .zip, and other formats."""
    try:
        if file_path.endswith('.tar.gz') or file_path.endswith('.tar') or file_path.endswith('.taz'):
            with tarfile.open(file_path, 'r:*') as tar:
                tar.extractall(path=extract_to)
        elif file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        else:
            print(f"Unsupported file format: {file_path}")
        print(f'Extracted to folder: {extract_to}')
    except (tarfile.ReadError, zipfile.BadZipFile) as e:
        print(f"Failed to open {file_path}. It may be corrupted or not a valid archive file. Error: {e}")


def parse_xml_to_json(xml_files, json_path):
    """Parse XML files and save the data as JSON."""
    result = []
    for xml_file in xml_files:
        try:
            # Read and decode the file with proper encoding handling
            with open(xml_file, 'rb') as file:  # Open the file in binary mode
                content = file.read()
                decoded_content = content.decode('iso-8859-1', errors='replace')  # Decode using 'iso-8859-1' with error replacement
            
            # Parse the XML from string
            root = ET.fromstring(decoded_content)

            for annonce in root.findall('.//ANNONCE_REF'):
                key = annonce.findtext('.//FICHIER_HTML').split('.')[0]
                data = {
                    'ID': key,
                    'Date': annonce.get('datedeclaration', ''),
                    'Type': annonce.find('.//TYPE').get('code', ''),
                    'Themes': [theme.get('code', '') for theme in annonce.findall('.//THEME')],
                    'Titre': annonce.findtext('.//TITRE', ''),
                    'SiegeSocial': annonce.findtext('.//SIEGE_SOCIAL', '').strip(),
                    'Text': annonce.findtext('.//OBJET', ''),
                    'Word_count': len(annonce.findtext('.//OBJET', '').split())
                }
                result.append(data)
        except ET.ParseError as e:
            print(f"Error parsing {xml_file}: {str(e)}")

    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(result, jf, ensure_ascii=False, indent=4)


def process_folder(folder, file_names):
    """Process specified files."""
    os.chdir(folder)
    files = [f for f in file_names if os.path.exists(f) and (f.endswith('.tar.gz') or f.endswith('.zip'))]  # Check for .tar.gz or .zip

    for file in files:
        base_name = file[:-7]  # Remove extension for .tar.gz
        if file.endswith('.zip'):
            base_name = file[:-4]  # Remove extension for .zip
        extract_path = os.path.join(folder, base_name)
        extract_file(file, extract_path)

        # Proceed with other operations only if extraction was successful
        if os.path.exists(extract_path):

        # Process inner taz files using subprocess
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file.endswith('.taz'):
                        old_file_path = os.path.join(root, file)
                        new_file_path = os.path.join(root, file[:-1] + 'r')  # change taz to tar
                        os.rename(old_file_path, new_file_path)
                        subprocess.run(['tar', '-xvf', new_file_path, '-C', root], check=True)
                        os.remove(new_file_path)

            # Collect and parse XML files
            xml_files = []
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file.endswith('.xml'):
                        xml_files.append(os.path.join(root, file))

            print(f'Found {len(xml_files)} XML files in {base_name}')
            json_path = os.path.join(folder, f'{base_name}.json')
            parse_xml_to_json(xml_files, json_path)

            # Cleanup extracted folders
            for root, dirs, files in os.walk(extract_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(extract_path)

# Example usage with specified filenames:
specific_files = ['ASS_2019.tar.gz']
process_folder(os.getcwd(), specific_files)
