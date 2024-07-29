import os
import json
import tarfile
import xml.etree.ElementTree as ET
from datetime import datetime
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyPDF2.

    Args:
        pdf_path (str): The file path to the PDF document.

    Returns:
        str: The extracted text from the PDF.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"  # Extract text from each page
    except Exception as e:
        raise Exception(f"Failed to extract PDF text: {e}")
    return text

def extract_and_process_data(start_year=2018, end_year=2022):
    for year in range(start_year, end_year + 1):
        year_folder = str(year)
        json_file_path = f'BALO_{year}.json'
        error_log_path = f'Error_{year}.txt'
        data = []

        print(f'Processing year: {year}')

        taz_files = [f for f in os.listdir(year_folder) if f.endswith('.taz')]
        total_files = len(taz_files)

        for i, tar_file in enumerate(taz_files, start=1):
            print(f'Processing file: {tar_file}, {i} out of {total_files}')
            tar_file_path = os.path.join(year_folder, tar_file)
            extract_folder_path = os.path.join(year_folder, tar_file.replace('.taz', ''))
            if not os.path.exists(extract_folder_path):
                os.makedirs(extract_folder_path)

            with tarfile.open(tar_file_path) as tar:
                tar.extractall(path=extract_folder_path)

            for member in os.listdir(extract_folder_path):
                if member.endswith('.xml'):
                    try:
                        xml_path = os.path.join(extract_folder_path, member)
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        date = datetime.strptime(root.attrib['date'], '%Y%m%d').strftime('%Y/%m/%d')

                        for annonce_ref in root.findall('ANNONCE_REF'):
                            fichier_txt_element = annonce_ref.find('FICHIERS_JOINTS/FICHIER_TXT')
                            text, word_count = "", 0
                            if fichier_txt_element is not None:
                                txt_path = os.path.join(extract_folder_path, fichier_txt_element.text)
                                if os.path.exists(txt_path):
                                    with open(txt_path, 'r', encoding='utf-8') as txt_file:
                                        text = txt_file.read()
                                        word_count = len(text.split())
                            else:
                                fichier_pdf_element = annonce_ref.find('FICHIERS_JOINTS/FICHIER_PDF')
                                if fichier_pdf_element is not None:
                                    pdf_path = os.path.join(extract_folder_path, fichier_pdf_element.text)
                                    if os.path.exists(pdf_path):
                                        try:
                                            text = extract_text_from_pdf(pdf_path)
                                            word_count = len(text.split())
                                        except Exception as e:
                                            with open(error_log_path, 'a') as error_file:
                                                error_file.write(f'Error processing PDF {pdf_path}: {e}\n')
                                            continue

                            entry = {
                                'Date': date,
                                'Societe_nom': annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE').text if annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE') is not None else "",
                                'Societe_siege': '',
                                'Numero_affaire': annonce_ref.find('NUMERO_AFFAIRE').text,
                                'Categorie': annonce_ref.find('CATEGORIE').attrib.get('name', ''),
                                'Categorie_1': "",
                                'Categorie_2': "",
                                'Text': text,
                                'Word_count': word_count
                            }

                            societe_siege_element = annonce_ref.find('NOMS_SOCIETE/NOM_SOCIETE')
                            if societe_siege_element is not None:
                                entry['Societe_siege'] = societe_siege_element.attrib.get('siege', '')

                            categorie_1_element = annonce_ref.find('CATEGORIE/CATEGORIE_N1')
                            if categorie_1_element is not None:
                                entry['Categorie_1'] = categorie_1_element.attrib.get('name', '')

                            categorie_2_element = annonce_ref.find('CATEGORIE/CATEGORIE_N1/CATEGORIE_N2')
                            if categorie_2_element is not None:
                                entry['Categorie_2'] = categorie_2_element.attrib.get('name', '')

                            data.append(entry)

                    except Exception as e:
                        with open(error_log_path, 'a') as error_file:
                            error_file.write(f'Error processing XML {member}: {e}\n')
                        continue

            # Cleanup
            for root, dirs, files in os.walk(extract_folder_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(extract_folder_path)

        # Write updated data to JSON file
        with open(json_file_path, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"\033[92mCompleted year: {year}\033[0m")

if __name__ == "__main__":
    extract_and_process_data()
