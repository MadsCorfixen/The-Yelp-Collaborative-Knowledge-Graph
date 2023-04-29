import gzip
import sys
import os

import pandas as pd
from rdflib import Namespace, Graph, URIRef
from rdflib.namespace import RDFS

from UtilityFunctions.get_data_path import get_path

sys.path.append(sys.path[0][:sys.path[0].find('DVML-P7') + len('DVML-P7')])

schema = Namespace("https://schema.org/")
skos = Namespace("https://www.w3.org/2004/02/skos/core#")
yelpcat = Namespace("https://purl.archive.org/purl/yelp/business_categories#")
yelpont = Namespace("https://purl.archive.org/purl/yelp/yelp_ontology#")

def create_schema_hierarchy_file(read_dir: str, write_dir: str):
    """_summary_

    Args:
        read_dir (str): _description_
        write_dir (str): _description_
    """

    triple_file = gzip.open(os.path.join(write_dir, "schema_hierarchy.nt.gz"),
                            mode="at",
                            encoding="utf-8")
    
    class_hierarchies = pd.read_csv(os.path.join(read_dir, "class_hierarchy.csv"))

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
            URIRef(skos + "narrowMatch") if "&" in row.YelpCategory or "/" in row.YelpCategory else URIRef(skos + "closeMatch"),   
            URIRef(row.SchemaType)                         
        ))

        if row.SchemaType not in category_mappings_cache:
            G.add(triple=(URIRef(row.SchemaType),
                            RDFS.Class,
                            URIRef(yelpont + "SchemaCategory")))
            category_mappings_cache.add(row.SchemaType)
    
    triple_file.write(G.serialize(format='nt'))
    triple_file.close()


if __name__ == "__main__":

    myfiles=["/home/ubuntu/vol1/virtuoso/import/schema_hierarchy.nt.gz", 
             "/home/ubuntu/vol1/virtuoso/import/yelp_schema_mappings.nt.gz"
             ]
    for i in myfiles:
        ## If file exists, delete it ##
        if os.path.isfile(i):
            os.remove(i)
        else:    ## Show an error ##
            print("Error: %s file not found" % i)
    
    create_schema_hierarchy_file(read_dir="/home/ubuntu/vol1/OneDrive/DVML-P7/Data", write_dir="/home/ubuntu/vol1/virtuoso/import")
    create_schema_mappings_file(read_dir="/home/ubuntu/vol1/OneDrive/DVML-P7/Data", write_dir="/home/ubuntu/vol1/virtuoso/import")
    