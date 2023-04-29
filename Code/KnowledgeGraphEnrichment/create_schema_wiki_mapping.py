import os
import gzip

import pandas as pd
from rdflib import Graph, URIRef, Literal, XSD, RDFS, Namespace

from Code.UtilityFunctions.wikidata_functions import wikidata_query, category_query


def create_schema_wiki_mapping(read_dir: str, write_dir: str) -> None:
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

    # Create RDF file
    yelpont = Namespace("https://purl.archive.org/purl/yelp/yelp_ontology#")
    triple_file = os.path.join(write_dir, "schema_wiki_mappings.nt.gz")  # Compress into .gz format to save space on disk

    if os.path.isfile(triple_file):  # Remove file if it already exists
        os.remove(triple_file)

    triple_file = gzip.open(filename=triple_file, mode="at", encoding="utf-8")

    # Initialise empty graph and populate with Schema-Wikidata mappings
    G = Graph()
    for idx, row in wikidata_mapping.iterrows():
        # Add (spo) with mapping
        G.add(triple=(
            URIRef(row.SchemaType),                 # Subject
            URIRef("https://schema.org/sameAs"),    # Predicate
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
            URIRef(row.QID),
            RDFS.Class,
            URIRef(yelpont + "WikidataCategory")
        ))

    triple_file.write(G.serialize(format='nt'))
    triple_file.close()


if __name__ == '__main__':
    create_schema_wiki_mapping(read_dir="/home/ubuntu/vol1/OneDrive/DVML-P7/Data",
                               write_dir="/home/ubuntu/vol1/virtuoso/import")
