import gzip
import os

import pandas as pd
from rdflib import Namespace, Graph, URIRef
from rdflib.namespace import RDFS
from Code.UtilityFunctions.schema_functions import class_hierarchy

schema = Namespace("https://schema.org/")
skos = Namespace("https://www.w3.org/2004/02/skos/core#")
yelpcat = Namespace("https://purl.archive.org/purl/yckg/categories#")
yelpvoc = Namespace("https://purl.archive.org/purl/yckg/vocabulary#")

def create_schema_hierarchy_file(read_dir: str, write_dir: str):
    """_summary_

    Args:
        read_dir (str): _description_
        write_dir (str): _description_
    """

    triple_file = gzip.open(os.path.join(write_dir, "schema_hierarchy.nt.gz"),
                            mode="at",
                            encoding="utf-8")
    
    class_hierarchies = class_hierarchy(read_dir=read_dir)
    
    G = Graph()  
    for idx, row in class_hierarchies.iterrows():  # Adds type hierarchies to the graph
        G.add(triple=(URIRef(Namespace(row['type'])),
                        RDFS.subClassOf,
                        URIRef(Namespace(row['superType']))))
    
    triple_file.write(G.serialize(format='nt'))
    triple_file.close()


def create_schema_mappings_file(read_dir: str, write_dir: str):
    """_summary_

    Args:
        read_dir (str): _description_
        write_dir (str): _description_
    """

    triple_file = gzip.open(os.path.join(write_dir, "yelp_schema_mappings.nt.gz"),
                        mode="at",
                        encoding="utf-8")
    
    schema_mapping = pd.read_csv(os.path.join(read_dir, "class_mappings_manual.csv"))

    # the column contains a string representation of a list, so we need to convert it to a list.
    schema_mapping['SchemaType'] = schema_mapping['SchemaType'].apply(lambda x: eval(x))
    schema_mapping = schema_mapping.explode('SchemaType')
    schema_mapping['YelpCategory'] = schema_mapping['YelpCategory'].apply(lambda x: yelpcat+x)
    schema_mapping['YelpCategory'] = schema_mapping['YelpCategory'].apply(lambda x: x.replace(" ", "_"))
    schema_mapping['SchemaType'] = schema_mapping['SchemaType'].apply(lambda x: "https://schema.org/"+x)

    category_mappings_cache = set()  # Cache for category mappings to avoid duplicates.

    # Initialise empty graph and populate with Yelp-Schema mappings
    G = Graph()
    for idx, row in schema_mapping.iterrows():
        G.add(triple=(
            URIRef(row.YelpCategory),
            URIRef(skos + "relatedMatch"),   
            URIRef(row.SchemaType)                         
        ))

        if row.SchemaType not in category_mappings_cache:
            G.add(triple=(
                URIRef(yelpvoc + "SchemaCategory"),
                URIRef(skos + "Member"),
                URIRef(row.SchemaType)
            ))
            category_mappings_cache.add(row.SchemaType)
    
    triple_file.write(G.serialize(format='nt'))
    triple_file.close()
    