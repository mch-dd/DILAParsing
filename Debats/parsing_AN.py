import os
import json
import subprocess
import shutil
import tarfile
import re
import xml.etree.ElementTree as ET
import psutil
import pandas as pd
import gc

# Define the root directory where to start the search
root_directory = 'SENAT'

# Years to look for
years = ['2011']#,'2012','2013','2014','2015']

def calculate_word_count(text):
    """Calculates the number of words in a string, stripping out HTML-like tags."""
    clean_text = re.sub('<[^<]+?>', '', text)  # Removing HTML-like tags
    words = clean_text.split()
    return len(words)

def extract_text_from_xml(xml_content, tag='Contenu'):
    """Extracts and returns clean text from specified tag in XML content, maintaining paragraph separation."""
    try:
        root = ET.fromstring(xml_content)
        contents = root.findall('.//' + tag)
        all_text = []
        for content in contents:
            paragraphs = content.findall('.//Para')
            for para in paragraphs:
                text_parts = [elem.strip() for elem in para.itertext() if elem.strip()]
                clean_text = ' '.join(text_parts)
                all_text.append(clean_text)
            full_text = '\n'.join(all_text)
            all_text.append(full_text)  # Reset for next 'Contenu' section
        return '\n'.join(all_text)
    except ET.ParseError as e:
        print(f"Error parsing XML for text extraction: {e}")
        return ""

def clean_text(text):
    text = re.sub(r'[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]', '', text)
    return text

def split_text_into_chunks(text, chunk_size=5000):
    """Splits the text into chunks of a specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def find_and_process_year_folders(root_dir, years):
    for subdir, dirs, files in os.walk(root_dir):
        for year in years:
            if year in dirs:
                print(f"Found folder for year: {year}")
                process_year_folder(os.path.join(subdir, year), year)
                dirs.remove(year)  # To avoid re-traversing the directory

def process_year_folder(year_path, year):
    json_data = []

    for subdir, dirs, files in os.walk(year_path):
        for file in files:  
            if file.endswith('.taz'):
                original_file_path = os.path.join(subdir, file)
                output_dir = os.path.join(subdir, file[:-4])
                os.makedirs(output_dir, exist_ok=True)

                try:
                    subprocess.run(['tar', '-xzf', original_file_path, '-C', output_dir], check=True)
                    print(f"Extraction of {original_file_path} successful using system tar command.")
                    extract_tar_files(output_dir)
                    
                    xml_files = find_files(output_dir, '.xml')
                    for xml_file in xml_files:
                        print(f"Processing XML file {xml_file} for year {year}.")
                        json_entries = parse_xml(xml_file, year_path)
                        json_data.extend(json_entries)
                        check_memory_usage()  # Check memory usage after processing each XML file

                        # Explicitly invoking garbage collector
                        gc.collect()
                    
                    shutil.rmtree(output_dir)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to extract {original_file_path} using system tar command: {e}")
                except Exception as e:
                    print(f"An error occurred while extracting {original_file_path}: {e}")

    # Save the JSON data to a Parquet file in batches
    save_json_data_in_batches(json_data, year_path, year)

    print(f'\033[92mSaved parquet files for year {year} successfully\033[0m')

def extract_tar_files(directory):
    for subdir, dirs, files in os.walk(directory):
        for file in files[:2]:
            if file.endswith('.tar'):
                tar_path = os.path.join(subdir, file)
                try:
                    with tarfile.open(tar_path, 'r:') as tar:
                        tar.extractall(path=subdir)
                        print(f"Tar file {tar_path} extracted.")
                except tarfile.TarError:
                    print(f"Failed to extract tar file {tar_path}")

def find_files(directory, extension):
    files_found = []
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                files_found.append(os.path.join(subdir, file))
    return files_found

def parse_xml(xml_file_path, year_path):
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
    except UnicodeDecodeError:
        with open(xml_file_path, 'r', encoding='iso-8859-1') as file:
            xml_content = file.read()

    xml_content = xml_content.replace('&deg;', '°')

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing {xml_file_path}: {e}")
        return []
    
    text = extract_text_from_xml(xml_content)
    chunks = split_text_into_chunks(clean_text(text))

    json_entries = []
    for chunk_num, chunk_text in enumerate(chunks, start=1):
        json_entry = {
            "Type_Publication": root.findtext('.//typePublication', ''),
            "Date": root.findtext('.//dateParution', ''),
            "Numero_Parution": root.findtext('.//numParution', ''),
            "Numero": root.findtext('.//numeroGrebiche', ''),
            "Date_Seance": root.findtext('.//dateSeance', ''),
            "Num_Jour_Session": root.findtext('.//numJourSession', ''),
            "Num_Seance": root.findtext('.//numSeance', ''),
            "Session_Ord": root.findtext('.//sessionOrd', ''),
            "Annex_Amendement": False,
            "Text": chunk_text,
            "Word_count": calculate_word_count(chunk_text),
            "Chunk": chunk_num
        }

        if root.find('.//ArticleAmendementAnnexe') is not None:
            json_entry["Annex_Amendement"] = True

        json_entries.append(json_entry)

    return json_entries

def check_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    if mem_info.rss > 1 * 1024 ** 3:  # Limit set to 1GB
        print(f"Memory usage exceeded limit: {mem_info.rss / (1024 ** 3)} GB. Terminating process.")
        raise MemoryError("Memory usage exceeded limit. Terminating to prevent server crash.")

def save_json_data_in_batches(json_data, year_path, year, batch_size=1000):
    for i in range(0, len(json_data), batch_size):
        batch_data = json_data[i:i+batch_size]
        df = pd.DataFrame(batch_data)
        parquet_file_path = os.path.join(year_path, f"{year}_{i//batch_size + 1}.parquet")
        df.to_parquet(parquet_file_path, index=False, engine='pyarrow')
        print(f"Saved batch {i//batch_size + 1} to {parquet_file_path}")

# Start the process
find_and_process_year_folders(root_directory, years)
