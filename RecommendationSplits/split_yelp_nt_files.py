import gzip
import json
import sys
import os
import pandas as pd

from rdflib import Namespace, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDFS

from Code.UtilityFunctions.run_query import run_query
from Code.UtilityFunctions.dictionary_functions import flatten_dictionary
from Code.UtilityFunctions.get_data_path import get_path
from Code.UtilityFunctions.schema_functions import get_schema_predicate, get_schema_type
from Code.UtilityFunctions.get_iri import get_iri

sys.path.append(sys.path[0][:sys.path[0].find('DVML-P7') + len('DVML-P7')])

schema = Namespace("https://schema.org/")
skos = Namespace("https://www.w3.org/2004/02/skos/core#")
business_uri = Namespace("https://www.yelp.com/biz/")
user_uri = Namespace("https://www.yelp.com/user_details?userid=")
yelpcat = Namespace("https://purl.archive.org/purl/yelp/business_categories#")
yelpont = Namespace("https://purl.archive.org/purl/yelp/yelp_ontology#")
yelpent = Namespace("https://purl.archive.org/purl/yelp/yelp_entities#")

def create_split_nt_file(file_name: str, rating_threshold, df_column, stage):
    """
    This function takes as input the Yelp JSON review file, creates a nt file from this review file. This functin is a version 
    which also properly handles the train, val and test splits used for recommendation methods.
    :param file_name: The Yelp JSON file to transform to RDF.
    :param rating_threshold: The minimum rating a review must have to be included in the RDF file. 
    :param df_column: Used to filter out reviews which are not in the train, val or test split.
    :param stage: The stage of the split, either train, val, test or original. Original is all splits combined.
    :return: a .nt.gz file with Yelp data in RDF format.
    """
    entity_name = file_name[22:-5]  # Either business, user, or review
    triple_file = gzip.open(filename=f"/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/yelp_{entity_name}_{stage}.nt.gz", mode="at",
                            encoding="utf-8")
    file_path = get_path(file_name)
    
    # Lists for keeping track of errors
    none_triples = []
    error_triples = []

    with open(file=file_path, mode="r") as file:
        # Iterate over every object in the JSON file as each object is one line.
        for line in file:
            try:
                line = json.loads(line)  # json.loads loads the JSON object into a dictionary.

                # If the file is reviews, the url depends on the line being iterated over.
                url = business_uri + line['business_id'] + '?hrid='

                G = Graph()  # Initialize a empty graph object to write a RDF triple to.

                json_key = list(line.keys())[0]  # Each dictionary has the ID as the value to the first key

                subject = get_iri(file_name) + line[json_key]  # get_iri makes sure the ID is a proper URI.

                if subject not in df_column.unique() or line['stars'] < rating_threshold:
                    continue

                # Adds a class to all subjects
                subject_class = get_schema_type(entity_name)

                G.add(triple=(URIRef(subject),
                            RDFS.Class,
                            URIRef(subject_class)))     

                # Creates a triple pointing to the subjects corresponding URL (Best practice).
                G.add(triple=(URIRef(subject),  
                              URIRef(schema + 'url'),  
                              URIRef(url + line[json_key])))  
                
                del line[json_key]  # After assigning the URI to the subject variable, we no longer need the first key/value pair

                # For reviews create a special triple making a connection between user and the review.
                G.add(triple=(URIRef(subject),
                                URIRef(schema + "author"),
                                URIRef(yelpent + 'user_id/' + line["user_id"])
                                ))
                
                del line["user_id"]  # No longer need the this key/value pair.

                line = flatten_dictionary(line)  # Some values are dictionaries themselves, so we flatten them before proceeding
                    
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

                        G.add(triple=(URIRef(subject),
                                      URIRef(predicate),  # E.g., hasBusinessParking, hashours
                                      URIRef(b_node)))  # Blank Node

                        blanknode_class = get_schema_type(_predicate)

                        G.add(triple=(URIRef(b_node),
                                      RDFS.Class,
                                      URIRef(blanknode_class)))

                        for sub_predicate, sub_object in _object.items():
                            G.add(triple=(URIRef(b_node),
                                          URIRef(yelpont + "has" + sub_predicate),
                                          Literal(sub_object)))
                            
                    elif _predicate in ["date", "friends", "elite"]:  # The values to these keys contains listed objects
                        obj_lst = _object.split(", ") if _predicate != "elite" else _object.split(",")  # Splits the listed objects

                        # get_schema_predicate assigns returns a proper schema.org predicate based on the key
                        # and a proper object datatype.
                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        if obj_lst:
                            for obj in obj_lst:
                                if _predicate == "date":
                                    obj = obj.replace(" ", "T")  # Cleans the date attribute

                                G.add(triple=(URIRef(subject),
                                              URIRef(predicate),
                                              Literal(obj, datatype=object_type)))
                    
                                        
                    elif _predicate == "business_id":  # If we are dealing with a reivew, we add a link to the business
                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        obj = yelpent + 'business_id/' + _object
                        
                        G.add(triple=(URIRef(subject),
                                      URIRef(predicate),
                                      URIRef(obj)))

                    elif type(_object) in (str, int, float, bool):
                        if _predicate == "yelping_since":
                            _object = _object.replace(" ", "T")

                        predicate, object_type = get_schema_predicate(_predicate, _object, file_name)
                        G.add(triple=(URIRef(subject),
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
    
    with open(f"none_list_{entity_name}.txt","wt") as file:
        for triple in none_triples:
            print(triple, file=file)

    with open(f"error_list_{entity_name}.txt","wt") as file:
        for triple in error_triples:
            print(triple, file=file)

def get_positive_users(rating_threshold: float, num_reviews_threshold: int) -> pd.DataFrame:
    """
    Retrieves users who have given positive reviews based on a rating threshold and a minimum number of reviews threshold.

    Args:
        rating_threshold (float): The minimum rating threshold for a review to be considered positive.
        num_reviews_threshold (int): The minimum number of reviews a user must have to be considered.

    Returns:
        pd.DataFrame: A Pandas DataFrame containing the users who meet the criteria.
    """
    # Define the SPARQL query to retrieve users with positive reviews
    get_positive_users_query = f"""
        SELECT ?user
        WHERE {{
            ?review rdfs:Class schema:UserReview .
            ?review schema:dateCreated ?timestamp .
            ?review schema:author ?user .
            ?review schema:aggregateRating ?rating .
            FILTER (?rating >= {rating_threshold}) .
        }}
        GROUP BY ?user 
        HAVING (COUNT(?review) >= {num_reviews_threshold}) 
    """
    
    # Run the SPARQL query and retrieve results as a Pandas DataFrame
    users_with_pos_reviews = run_query(query=get_positive_users_query, as_dataframe=True)
    
    # Return the DataFrame with the users who meet the criteria
    return users_with_pos_reviews

def batch_get_reviews(user_batch: str) -> pd.DataFrame:
    """
    Retrieves reviews for a batch of users based on a given user batch string.

    Args:
        user_batch (str): A string containing the batch of user URIs to retrieve reviews for.

    Returns:
        pd.DataFrame: A Pandas DataFrame containing the reviews for the users in the batch.
    """
    # Define the SPARQL query to retrieve reviews for the given user batch
    get_reviews_query = f"""
        SELECT ?user ?review ?business ?rating ?timestamp
        WHERE {{
            ?review schema:author ?user .
            ?review schema:about ?business .
            ?review schema:aggregateRating ?rating .
            ?review schema:dateCreated ?timestamp .

            VALUES ?user {{ {user_batch} }} .
        }}
    """

    # Run the SPARQL query and retrieve results as a Pandas DataFrame
    reviews_df = run_query(query=get_reviews_query, as_dataframe=True)
    
    # Return the DataFrame with the reviews for the users in the batch
    return reviews_df

def format_values_string(_input: set) -> str:
    """
    Formats a set of values into a string that can be used as input for a SPARQL query.

    Args:
        _input (set): A set of values to be formatted.

    Returns:
        str: A string containing the formatted values.
    """
    # Convert the input set to a list
    formatted = list(_input)
    
    # Join the list elements with angle brackets and wrap them in "<>"
    formatted = " ".join(f"<{entry}>" for entry in formatted)
    
    # Return the formatted string
    return formatted

def timewise_stratified_split(data: pd.DataFrame, class_column: str, time_column: str, train_size: float, val_size: float, test_size: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a time-wise stratified split on a given pandas DataFrame based on specified parameters.

    Parameters:
        -- data (pd.DataFrame): The input DataFrame to split.
        -- class_column (str): The name of the column in the DataFrame that represents the class or target variable.
        -- time_column (str): The name of the column in the DataFrame that represents the time or timestamp.
        -- train_size (float): The proportion of data to allocate for the training set, represented as a float between 0 and 1.
        -- val_size (float): The proportion of data to allocate for the validation set, represented as a float between 0 and 1.
        -- test_size (float): The proportion of data to allocate for the test set, represented as a float between 0 and 1.

    Returns:
        -- tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple of three DataFrames representing the time-wise stratified split of the input DataFrame:
            - train: The training set.
            - validation: The validation set.
            - test: The test set.
    """
    # Convert the time column to datetime objects for correct time-based sorting
    data[time_column] = pd.to_datetime(data[time_column])

    # Sort the DataFrame based on the time column in ascending order (oldest to newest)
    data.sort_values(by=time_column, ascending=True, inplace=True)

    # Reset the index of the DataFrame
    data.reset_index(drop=True, inplace=True)

    # Group the data by the class column
    grouped = data.groupby(class_column)

    # Define a helper function to calculate the count of rows based on the specified percentage
    def get_percent_count(group, percent):
        total_count = len(group)
        return int(total_count * percent)
    
    # Initialize empty lists to store the rows for each split
    train_rows = []
    validation_rows = []
    test_rows = []

    # Loop over the groups and perform the stratified split
    for _, group in grouped:

        # Calculate the number of rows to allocate for each split (based on the specified percentage)
        train_count = get_percent_count(group=group, percent=train_size)
        val_count = get_percent_count(group=group, percent=val_size)

        # Slice the group according to the calculated counts and append the rows to the appropriate list
        train_rows.append(group.iloc[:train_count])
        validation_rows.append(group.iloc[train_count: train_count+val_count])
        test_rows.append(group.iloc[train_count+val_count:])
    
    # Concatenate the rows to create the training, validation, and test sets
    train = pd.concat(train_rows)
    validation = pd.concat(validation_rows)
    test = pd.concat(test_rows)

    # Return a tuple of the resulting DataFrames representing the stratified split
    return (train, validation, test)


if __name__ == "__main__":
    users_with_pos_reviews = get_positive_users(num_reviews_threshold=10, rating_threshold=3.0)

    user_batch_cache = set()  # Create an empty set to store the user URIs in batches
    reviews_list = list()  # Create an empty list to store the resulting dataframes for reviews

    for row in users_with_pos_reviews.itertuples():
        user = row[1]  # Get the user URI from the current row of users_with_pos_reviews dataframe
        user_batch_cache.add(user)  # Add the user URI to the user batch cache

        if len(user_batch_cache) % 20 == 0:
            # If the user batch cache contains 20 user URIs, format them into a string for the VALUES statement in the query
            user_batch = format_values_string(_input=user_batch_cache)
            user_batch_cache.clear()  # Prepare the user batch cache for the next 20 users

            # Query the graph for reviews, businesses, ratings, and timestamps for the current batch of users
            review_batch = batch_get_reviews(user_batch=user_batch)
            reviews_list.append(review_batch)  # Append the resulting dataframe to the list of reviews

    if len(user_batch_cache) > 0:
        # If the last batch is less than 20, we still need to retrieve reviews, businesses, ratings, and timestamps
        user_batch = format_values_string(_input=user_batch_cache)
        review_batch = batch_get_reviews(user_batch=user_batch)
        reviews_list.append(review_batch)  # Append the resulting dataframe to the list of reviews

    reviews_df = pd.concat(reviews_list, ignore_index=True)  # Concatenate all the resulting dataframes into a single dataframe
    
    t = timewise_stratified_split(data=reviews_df, class_column="user.value", time_column="timestamp.value",
                              train_size=0.6, val_size=0.2, test_size=0.2) 

    train, val, test = t[0], t[1], t[2]
    all_df = pd.concat([train, val, test], ignore_index=True)

    # Save the split csv files 
    train.to_csv("/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/review_train.csv", index=False)
    val.to_csv("/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/review_val.csv", index=False)
    test.to_csv("/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/review_test.csv", index=False)
    
    myfiles=[
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_train.nt.gz", 
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_val.nt.gz",
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_test.nt.gz"
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_original.nt.gz"
             ]
    for i in myfiles:
        ## If file exists, delete it ##
        if os.path.isfile(i):
            os.remove(i)
        
    create_split_nt_file(file_name='yelp_academic_dataset_review.json', rating_threshold=3.0, df_column=train['review.value'], stage='train')
    create_split_nt_file(file_name='yelp_academic_dataset_review.json', rating_threshold=3.0, df_column=val['review.value'], stage='val')
    create_split_nt_file(file_name='yelp_academic_dataset_review.json', rating_threshold=3.0, df_column=test['review.value'], stage='test')
    create_split_nt_file(file_name='yelp_academic_dataset_review.json', rating_threshold=3.0, df_column=all_df['review.value'], stage='original')

    