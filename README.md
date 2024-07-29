# DILA Dataset Parsing Scripts

This repository contains Python scripts for parsing and processing the open data provided by the Direction de l'Information Légale et Administrative (DILA) from their official [open data website](https://echanges.dila.gouv.fr/OPENDATA/). These scripts are designed to handle various file formats and compression types, extracting raw data and converting it into a structured JSON format for easier access and manipulation.

## Table of Contents

- [Parsing Procedures](#parsing-procedures)
  - [Process One: Handling .tar.gz Compressed Folders](#process-one-handling-targz-compressed-folders)
  - [Process Two: Parsing Data in the "FluxHistorique" Folder](#process-two-parsing-data-in-the-fluxhistorique-folder)
- [Subsequent Data Handling Procedures - Text Extraction](#subsequent-data-handling-procedures---text-extraction)
- [Challenges Encountered](#challenges-encountered)
- [Examples of Clean Data Retrieved](#examples-of-clean-data-retrieved)
- [Folder Explanations and Volume](#folder-explanations-and-volume)
- [Contributing](#contributing)

## Parsing Procedures

### Process One: Handling .tar.gz Compressed Folders

**File Structure:** This method addresses folders predominantly containing `.tar.gz` compressed files. These archives usually consist of `.xml` files, which are the primary data source.

**Extraction and Parsing:**

1. **Uncompression:** The initial step involves decompressing `.tar.gz` files to access the contained `.xml` files.
2. **Data Conversion:** Following extraction, the `.xml` files are parsed and the extracted data is converted into JSON format (one JSON file per each `.tar.gz` file). This transformation aids in standardizing the data structure for ease of use in downstream applications.

### Process Two: Parsing Data in the "FluxHistorique" Folder

**File Structure:** In this scenario, files are organized within a main folder named "FluxHistorique," subdivided by year. The data for each year is either stored in compressed files (using formats like 7zip, tar.gz, taz, or zip) or in folders that contain compressed files.

**Extraction and Collection:**

1. **Decompression:** All files, irrespective of their compression format, are uncompressed.
2. **File Aggregation:** Post decompression, all `.xml` files are collected to extract pertinent information into JSON files (each file corresponds to each year).

## Subsequent Data Handling Procedures - Text Extraction

Once the metadata is extracted from the `.xml` files using the aforementioned processes, the `text` key for each JSON entry is retrieved based on the source document type:

- **Docx Documents:** Text is extracted directly from Word documents, with the necessary metadata like reference and path sourced from the corresponding `.xml` file.
- **HTML Documents:** Similar to Word documents, text is retrieved from HTML files, using metadata from `.xml` files to locate the required documents.
- **PDF Documents:** Text is extracted using the PyPDF2 library, using metadata from `.xml` files to locate the required documents. Due to the inherent complexities of PDF files, such as embedded tables and various formatting elements, text extraction can be challenging and sometimes unreliable.
- **Direct XML Content:** In some instances, the `.xml` files themselves contain the textual content, which can be directly parsed and used.

## Challenges Encountered

- **Inconsistent XML Structures:** Often, the structure or tags within `.xml` files vary from year to year, complicating the development of a consistent and stable parsing mechanism across different folders and timeframes.
- **Complexity in PDF Text Retrieval:** The extraction of text from PDFs is particularly problematic due to non-text elements like tables and formatted lists, which PyPDF2 struggles to interpret accurately. An improved pipeline for information extraction from PDFs is currently under development.
- **Variability in Document Formats:** While extraction from Word documents is generally straightforward, variations in document formats (e.g., .odt files) introduce additional complexity.
- **Issues with Taz Files:** Although some `.taz` files can be opened readily with the library `tarfile`, others require modification of the file extension and forced decompression, which complicates the process.
- **Incoherence in XML Encoding:** Not all XML files are encoded in the same way, making it difficult to utilize a stable and coherent parsing method.

## Examples of Clean Data Retrieved

```json
[
    {
        "etat_value": "MODIFIE",
        "date_debut_value": "2017-04-08",
        "titre": "Code des transports",
        "article": "R3121-24",
        "text": "Le ministère chargé des transports remplit, à l'égard du registre national de disponibilité des taxis, les missions prévues à l'article L. 3121-11-1 et précisées par la présente section, à titre gratuit pour ses utilisateurs. Il en assure le développement informatique et le maintien en conditions opérationnelles.",
        "word_count": 46
    },
    {
        "etat_value": "VIGUEUR",
        "date_debut_value": "2017-04-08",
        "titre": "Code des transports",
        "article": "R3121-1",
        "text": "I.-En application de l'article L. 3121-1, un véhicule affecté à l'activité de taxi est muni d'équipements spéciaux comprenant : 1° Un compteur horokilométrique homologué, dit \" taximètre \", conforme aux prescriptions du décret n° 2006-447 du 12 avril 2006 relatif à la mise sur le marché et à la mise en service de certains instruments de mesure ; 2° Un dispositif extérieur lumineux portant la mention \" taxi \", dont les caractéristiques sont fixées par le ministre chargé de l'industrie, qui s'illumine en vert lorsque le taxi est libre et en rouge lorsque celui-ci est en charge ou réservé ; 3° Une plaque fixée au véhicule et visible de l'extérieur indiquant le numéro de l'autorisation de stationnement ainsi que son ressort géographique tel qu'il est défini par l'autorité compétente pour délivrer l'autorisation de stationnement ; 4° Sauf à ce que le compteur horokilométrique en remplisse la fonction, un appareil horodateur homologué, fixé au véhicule, permettant, lorsqu'une durée maximale d'utilisation du taxi est prescrite par l'autorité compétente, d'enregistrer les heures de début et de fin de service du conducteur. II.-Il est, en outre, muni de : 1° Une imprimante, connectée au taximètre, permettant l'édition automatisée d'une note informant le client du prix total à payer conformément aux textes d'application de l'article L. 113-3 du code de la consommation ; 2° Un terminal de paiement électronique en état de fonctionnement et visible, tenu à la disposition du client, afin de permettre au conducteur d'accomplir l'obligation prévue à l'article L. 3121-11-2 et, le cas échéant, au prestataire de services de paiement d'accomplir l'obligation d'information prévue à l'article L. 314-14 du code monétaire et financier.",
        "word_count": 271
    },
    {
        "etat_value": "VIGUEUR",
        "date_debut_value": "2017-04-08",
        "titre": "Code des transports",
        "article": "R3121-22",
        "text": "Le tarif maximum d'une course de taxi est fixé par le décret n° 2015-1252 du 7 octobre 2015 relatif aux tarifs des courses des taxis et par les textes pris pour son application.",
        "word_count": 33
    }
]
```

## Folder Explanations and Volume

| Folder       | Explanation                                                                                                                                                                                                                                                                                                                                                             | Vol. of Words  |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| ACCO         | Agreements disseminated in accordance with Article of Decree No. 2017-752 of May 3, 2017, relating to the publicity of collective agreements. These agreements may concern groups, companies, and establishments. Disseminated are the agreements concluded, their modification(s), and their deletion.                                                                | 600,693,732    |
| AMF          | Financial information transmitted by l'Autorité des marchés financiers (AMF). Financial information serves as the raw material for investors (and other economic agents, lenders, clients, employees, government authorities, etc.) to make their decisions.                                                                                                             | 5,255,372,493  |
| ASSOCIATIONS | Declarations of creation, modification, or dissolution of associations governed by the 1901 law since its inception. Declarations of creation, modification, or dissolution of property owners' associations since 2004. Declarations of creation, modification, or dissolution of corporate foundations since 1991.                                                     | 103,188,343    |
| BALO         | The Bulletin des annonces légales obligatoires (BALO) collects information pertinent to publicly traded companies, financial institutions, and banking establishments. It encompasses a wide array of data including financial transactions, notices for general assembly meetings, and annual financial statements.                                                     | 417,687,457    |
| BOAMP        | The Bulletin officiel des annonces de marchés publics (BOAMP) serves as a vital platform for disseminating information related to public procurement. It encompasses various notices including calls for public tenders and the outcomes of contracts for state entities, the military, local authorities, and their public institutions.                                | 1,568,807,455  |
| BOCC         | The Bulletin officiel des conventions collectives (BOCC) serves as a comprehensive repository for all collective labor agreements. It includes texts that complement or amend existing collective agreements, which have been negotiated and deposited by social partners at the Ministry of Labor.                                                                      | 47,810,801     |
| BODACC       | The Bulletin officiel des annonces civiles et commerciales (BODACC) provides public notice of acts recorded in the commercial and companies register. It publishes various notices as stipulated by the commercial code and relevant legislative and regulatory texts.                                                                                                    | 1,757,440,801  |
| CAPP         | The Court of Cassation (CAPP) comprises a collection of rulings pertaining to civil and criminal matters. Selections of these decisions are curated by the respective jurisdictions in accordance with decree n° 2005-13 dated January 7, 2005.                                                                                                                           | 159,252,544    |
| CASS         | Significant judgments from judicial jurisprudence along with rulings from the Court of Cassation. Specifically, it encompasses decisions published in the Bulletin des chambres civiles since 1960 and the Bulletin de la chambre criminelle since 1963.                                                                                                                  | 127,289,156    |
| CIRCULARIES  | The folder contains regulations regarding instructions and circulars applicable within the French administrative framework, as detailed in articles R. 312-8 and R. 312-9 of the code des relations entre le public et l'administration.                                                                                                                                  | 297,828,411    |
| CNIL         | The repository comprises all deliberations of the CNIL (Commission nationale de l'informatique et des libertés), including opinions, recommendations, simplified norms, authorizations, and more, dating back to 2012.                                                                                                                                                    | 10,270,657     |
| CONSTIT      | The repository encompasses all decisions rendered by the Constitutional Council since its establishment by the Constitution of October 4, 1958.                                                                                                                                                                                                                           | 8,648,522      |
| DEBATS       | Debates of the Assemblee Nationale and Sénat.                                                                                                                                                                                                                                                                                                                             | Ongoing parsing|
| DOLE         | The folder contains laws enacted since the start of the XIIth legislature in June 2002, ordinances published since 2002, and laws in preparation in the form of bills and proposals.                                                                                                                                                                                     | 11,796,816     |
| INCA         | Unpublished rulings (not published in the Bulletin) issued by the Cour de cassation since 1989.                                                                                                                                                                                                                                                                            | 452,393,983    |
| JADE         | Decisions of the Conseil d'Etat, administrative courts of appeal d'appel and the tribunal des conflits.                                                                                                                                                                                                                                                                    | 828,590,452    |
| JORF         | Since 1990: the documentary collection of documents published in the "Laws and Decrees" edition of the Journal Officiel.                                                                                                                                                                                                                                                  | 554,912,887    |
| KALI         | Collective agreements and related texts included in the brochures published by DILA. The scope of the brochures includes extended national extended national collective agreements and certain national collective bargaining agreements that have not been extended. Each brochure contains the collective agreement(s) collective agreements relating to a given activity, as well as the agreements, wages and extension decrees. | 83,640,687     |
| LEGI         | The full consolidated text of national legislation and regulations.                                                                                                                                                                                                                                                                                                       | 412,409,434    |

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.


