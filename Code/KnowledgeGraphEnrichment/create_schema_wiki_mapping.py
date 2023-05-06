import sys
sys.path.append(sys.path[0][:sys.path[0].find('YelpOpenDatasetKnowledgeGraph') + len('YelpOpenDatasetKnowledgeGraph')])

import os
import gzip

import pandas as pd
from rdflib import Graph, URIRef, Literal, XSD, RDFS, Namespace

from Code.UtilityFunctions.wikidata_functions import wikidata_query, category_query

skos = Namespace("https://www.w3.org/2004/02/skos/core#")
yelpcat = Namespace("https://purl.archive.org/purl/yckg/categories#")
yelpvoc = Namespace("https://purl.archive.org/purl/yckg/vocabulary#")

def create_yelp_wiki_mapping(read_dir: str, write_dir: str) -> None:
    """This function creates a GZIP-compressed .nt file with the Schema-Wikidata mappings.

    Args:
        read_dir (str): The path to the directory in which the function should read files. This function uses the `class_mappings_manual.csv` to retrieve the relevant SchemaTypes to map to Wikidata
        write_dir (str): The path to the directory in which the function should write the .nt.gz file.
    """
    # Read the csv file containing the Yelp-Schema mappings
    schema_mapping = pd.read_csv(filepath_or_buffer=os.path.join(read_dir, "class_mappings_manual.csv"))

    # the column `SchemaType` contains a string representation of a list, so we convert it to a list using `eval` and `explode`.
    schema_mapping['SchemaType'] = schema_mapping['SchemaType'].apply(lambda x: eval(x))
    schema_mapping = schema_mapping.explode('SchemaType')
    schema_mapping['SchemaType'] = schema_mapping['SchemaType'].apply(lambda x: "https://schema.org/" + x)  # Add IRI

    # Initialise empty DataFrame with columns `SchemaType`, `QID`, and `Label` and populate it with Schema-Wikidata mappings
    wikidata_mapping = pd.DataFrame(columns=['SchemaType', 'QID', 'Label'])
    for _type in schema_mapping['SchemaType']:
        wikidata_cat_query = wikidata_query(category_query(schema_iri=_type))  # Query Wikidata for any items with a SameAs relation to the specifid Schema Type `_type`

        if not wikidata_cat_query.empty:  # If the query finds no results, we skip the _type
            to_concat = {'SchemaType': _type,
                        'QID': list(wikidata_cat_query['item.value']),
                        'Label': list(wikidata_cat_query['itemLabel.value'])}
            
            wikidata_mapping = wikidata_mapping.append(to_concat, ignore_index=True)

    # Clean the resulting DataFrame containing the mappings. Any list results are exploded into new rows, duplicates are dropped, and the index is reset.
    wikidata_mapping = wikidata_mapping.explode("QID")
    wikidata_mapping = wikidata_mapping.explode("Label")
    wikidata_mapping = wikidata_mapping.drop_duplicates()
    wikidata_mapping = wikidata_mapping.reset_index(drop=True)

    mapping_dataframe = pd.merge(left=wikidata_mapping, right=schema_mapping, how='left', on='SchemaType')  # Merge the Schema-Wikidata mappings with the Schema-Yelp mappings

    # Create RDF file
    triple_file = os.path.join(write_dir, "yelp_wiki_mappings.nt.gz")  # Compress into .gz format to save space on disk

    if os.path.isfile(triple_file):  # Remove file if it already exists
        os.remove(triple_file)

    triple_file = gzip.open(filename=triple_file, mode="at", encoding="utf-8")

    # Initialise empty graph and populate with Yelp-Wikidata mappings
    G = Graph()
    for idx, row in mapping_dataframe.iterrows():
        # Add (spo) with mapping
        G.add(triple=(
            URIRef(yelpcat + row.YelpCategory.replace(' ', '_').replace("&", "_").replace("/", "_")), # Subject
            URIRef(skos + "relatedMatch"),          # Predicate
            URIRef(row.QID)                         # Object
        ))

        # Add (spo) with Wikidata label
        G.add(triple=(
            URIRef(row.QID),
            RDFS.label,
            Literal(row.Label, datatype=XSD.string)
        ))

        # Add (spo) specifying the class of the QID as stemming from Wikidata
        G.add(triple=(
            URIRef(yelpvoc + "WikidataCategory"),
            URIRef(skos + "Member"),
            URIRef(row.QID)
        ))

    triple_file.write(G.serialize(format='nt'))
    triple_file.close()
