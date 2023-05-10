import gzip
import json
import os

from rdflib import Namespace, Graph, URIRef, Literal, BNode, XSD
from rdflib.namespace import RDF
from collections import Counter

from Code.UtilityFunctions.dictionary_functions import flatten_dictionary
from Code.UtilityFunctions.schema_functions import get_schema_predicate, get_schema_type
from Code.UtilityFunctions.get_iri import get_iri

schema = Namespace("https://schema.org/")
skos = Namespace("https://www.w3.org/2004/02/skos/core#")
business_uri = Namespace("https://www.yelp.com/biz/")
user_uri = Namespace("https://www.yelp.com/user_details?userid=")
yelpcat = Namespace("https://purl.archive.org/purl/yckg/categories#")
yelpvoc = Namespace("https://purl.archive.org/purl/yckg/vocabulary#")
yelpent = Namespace("https://purl.archive.org/purl/yckg/entities#")

def create_nt_file(file_name: str, read_dir: str, write_dir: str):
    """
    This function takes as input one of three Yelp JSON files (The tip/checkin files are handled in different functions),
    transforms the objects in that file to RDF format, and writes them to a output file.
    :param file_name: The Yelp JSON file to transform to RDF.
    :param read_dir: The directory to read the Yelp JSON file from.
    :param write_dir: The directory to write the RDF file to.
    :return: a .nt.gz file with Yelp data in RDF format.
    """
    entity_name = file_name[22:-5]  # Either business, user, or review
    triple_file = gzip.open(filename=os.path.join(write_dir, f"yelp_{entity_name}.nt.gz"), mode="at", encoding="utf-8")
    file_path = os.path.join(read_dir, file_name)
    
    # Lists for keeping track of errors
    none_triples = []
    error_triples = []

    with open(file=file_path, mode="r") as file:

        # Creates the URLs which we link to
        if file_name == "yelp_academic_dataset_business.json":
            url = business_uri
        elif file_name == 'yelp_academic_dataset_user.json':
            url = user_uri
            
        category_cache = set()  # Cache for categories to avoid triple duplicates.

        # Iterate over every object in the JSON file as each object is one line.
        for line in file:
            try:
                line = json.loads(line)  # json.loads loads the JSON object into a dictionary.

                # If the file is reviews, the URL depends on the line being iterated over.
                if file_name == 'yelp_academic_dataset_review.json':
                    url = business_uri + line['business_id'] + '?hrid='

                G = Graph()  # Initialize an empty graph object to write triples to.

                json_key = list(line.keys())[0]  # Each dictionary has the ID as the value to the first key
                subject = get_iri(file_name) + line[json_key]  # get_iri makes sure the ID is a proper IRI.
                subjectURI = URIRef(subject)
                subject_class = get_schema_type(entity_name) #get_schema_type returns the schema type for the entity.

                G.add(triple=(subjectURI,
                            RDF.type,
                            URIRef(subject_class)))     

                G.add(triple=(subjectURI,  
                              URIRef(schema + 'url'),  
                              URIRef(url + line[json_key])))  
                
                del line[json_key]  # After assigning the IRI to the subject variable, we no longer need the first key/value pair

                # For reviews create a special triple making a connection between user and the review.
                if file_name == "yelp_academic_dataset_review.json":
                    G.add(triple=(subjectURI,
                                  URIRef(schema + "author"),
                                  URIRef(yelpent + 'user_id/' + line["user_id"])
                                  ))
                    del line["user_id"]  # No longer need the this key/value pair.

                line = flatten_dictionary(line)  # Some values are dictionaries themselves, so we flatten them before proceeding
                
                # In this if statement we handle the categories in the business file which are a special case.
                if file_name == 'yelp_academic_dataset_business.json':
                    if line['categories']:
                        categories = line['categories'].split(", ") # Categories are initially one long comma-separated string.
                        del line['categories']  # No longer need this key/value pair.
                        
                        for category in categories:
                            category = category.replace(' ', '_').replace("&", "_").replace("/", "_")  # Need to replace special characters as we use it as IRI.

                            G.add(triple=(
                                subjectURI,
                                URIRef(schema + "keywords"),
                                URIRef(yelpcat + category)
                                ))

                            if category not in category_cache:
                                G.add(triple=(
                                    URIRef(yelpcat + category),
                                    RDF.type,
                                    URIRef(yelpvoc + "YelpCategory")
                                    ))
                                
                                category_cache.add(category)
                
                # Now we iterate over the rest of the key/value pairs and transform them to RDF format.
                for _predicate, _object in line.items():
                    if _object in ("None", None, "none", "null", "Null", "NULL", ""): # Some values are None, add to them a list, and skip them.
                        none_triples.append((subject, _predicate, _object))
                        continue
                    # Some values are dictionaries, which needs to be handled differently.
                    elif isinstance(_object, dict) or _predicate in ("BusinessParking", "GoodForMeal", "Ambience", "Music", "BestNights", "HairSpecializesIn", "DietaryRestrictions"):
                        if isinstance(_object, str):
                            _object = _object.replace("'", '"').replace("None", "null").replace('u"', '"').replace("True", "true").replace("False", "false") 
                            _object = json.loads(_object)
                        
                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        b_node = BNode()

                        G.add(triple=(subjectURI,
                                      URIRef(predicate),  
                                      b_node))  

                        blanknode_class = get_schema_type(_predicate)

                        G.add(triple=(b_node,
                                      RDF.type,
                                      URIRef(blanknode_class)))

                        for sub_predicate, sub_object in _object.items():
                            G.add(triple=(b_node,
                                          URIRef(yelpvoc + "has" + sub_predicate),
                                          Literal(sub_object)))
                            
                    elif _predicate in ["date", "friends", "elite"]:  # The values to these keys contains listed objects
                        obj_lst = _object.split(", ") if _predicate != "elite" else _object.split(",")  # Splits the listed objects

                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        if obj_lst:
                            for obj in obj_lst:
                                if _predicate == "date":
                                    obj = obj.replace(" ", "T")  # Cleans the date attribute
                                
                                if _predicate == "friends":
                                    obj = yelpent + 'user_id/' + obj  
                                    G.add(triple=(subjectURI,
                                              URIRef(predicate),
                                              URIRef(obj)))
                                
                                else:
                                    G.add(triple=(subjectURI,
                                                URIRef(predicate),
                                                Literal(obj, datatype=object_type)))
                    
                                        
                    elif _predicate == "business_id":  # If we are dealing with a reivew, we add a link to the business
                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        obj = yelpent + 'business_id/' + _object
                        
                        G.add(triple=(subjectURI,
                                      URIRef(predicate),
                                      URIRef(obj)))

                    elif type(_object) in (str, int, float, bool):
                        if _predicate == "yelping_since":
                            _object = _object.replace(" ", "T")

                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        G.add(triple=(subjectURI,
                                      URIRef(predicate),
                                      Literal(_object, datatype=object_type)))
                                            
                    else:
                        error_triples.append((subject, _predicate, _object))   

                triple_file.write(
                    G.serialize(format='nt'))  # Writes to the .nt file the graph now containing a RDF triple.

            except Exception as e:
                print(e)
                print(line)

    triple_file.close()
    
    with open(os.path.join("Code", "Errors", f"none_list_{entity_name}.txt"),"wt") as file:
        for triple in none_triples:
            print(triple, file=file)

    with open(os.path.join("Code", "Errors", f"error_list_{entity_name}.txt"),"wt") as file:
        for triple in error_triples:
            print(triple, file=file)


def create_checkin_nt_file(read_dir: str, write_dir: str):
    """Creates a .nt file containing the Checkin data from the Yelp dataset.
    The checkin json only contains two lines, a business id and a string of dates."""

    file_name = "yelp_academic_dataset_checkin.json"
    entity_name = file_name[22:-5]

    triple_file = gzip.open(filename=os.path.join(write_dir, f"yelp_{entity_name}.nt.gz"), mode="at", encoding="utf-8")
    file_path = os.path.join(read_dir, file_name)

    with open(file=file_path, mode="r") as file:
        for line in file:
            try:
                line = json.loads(line)

                G = Graph()  

                json_key = list(line.keys())[0]  # Each dictionary has the ID as the value to the first key, in this case the business id
                business = get_iri(file_name) + line[json_key]  # get_iri makes sure the businnes_id is a valid IRI

                dates = line["date"].split(", ")  # The date key contains a list of dates, which we split

                if dates[0] == "": # If the list is empty, we skip it
                    continue
                dates = [date.replace(" ", "T") for date in dates]  # Cleans the date attribute
                date_counter = Counter(dates) # Counts the number of times a date appears in the list

                for date, count in date_counter.items():
                    
                    b_node = BNode()
        
                    G.add(triple=(b_node,
                                  URIRef(schema + "object"),
                                  URIRef(business)))
                    
                    G.add(triple=(b_node,
                                  RDF.type,
                                  URIRef(schema + "ArriveAction")))
                    
                    G.add(triple=(b_node,
                                  URIRef(schema + 'startTime'),
                                  Literal(date, datatype=XSD.dateTime)))
                    
                    G.add(triple=(b_node,
                                 URIRef(schema + 'interactionStatistic'),
                                 Literal(count, datatype=XSD.integer)))
                    
                triple_file.write(G.serialize(format='nt'))  # Writes to the .nt file the graph now containing a RDF triple

            except Exception as e:
                print(e)

    triple_file.close()


def create_tip_nt_file(read_dir: str, write_dir: str):
    """
    Special case of the create_nt_file function. This function transforms the tip JSON file to RDF format.
    :return: A .nt.gz file with Yelp tip data in RDF format.
    """

    file_name = "yelp_academic_dataset_tip.json"
    entity_name = file_name[22:-5]

    triple_file = gzip.open(filename=os.path.join(write_dir, f"yelp_{entity_name}.nt.gz"), mode="at", encoding="utf-8")
    file_path = os.path.join(read_dir, file_name)

    with open(file=file_path, mode="r") as file:
        for line in file:
            try:
                line = json.loads(line)
                G = Graph()
                b_node = BNode()
                user = line["user_id"]                
                del line["user_id"]

                # Creates the edge between a user and their tip
                G.add(triple=(b_node,
                              URIRef(schema + "author"),
                              URIRef(yelpent + 'user_id/' + user)))

                # Assigns a RDF type to the blank node.
                G.add(triple=(b_node,
                              RDF.type,
                              URIRef(yelpvoc + 'Tip')))

                for _predicate, _object in line.items():
                    predicate, object_type = get_schema_predicate(_predicate, _object, file_name)

                    if _predicate == "date":
                        obj = _object.replace(" ", "T")
                    elif _predicate == "business_id":
                        obj = yelpent + 'business_id/' + _object
                    else:
                        obj = _object

                    G.add(triple=(b_node,
                                  URIRef(predicate),
                                  Literal(obj, datatype=object_type)))

                triple_file.write(G.serialize(format="nt"))

            except Exception as e:
                print(e)
                print(b_node, _predicate, _object)

    triple_file.close()
    