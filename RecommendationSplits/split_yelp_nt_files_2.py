import pandas as pd
import gzip
from rdflib import Graph, URIRef
from Code.UtilityFunctions.get_data_path import get_path
from Code.UtilityFunctions.get_iri import get_iri
from RecommendationSplits.split_yelp_nt_files import get_positive_users, format_values_string, batch_get_reviews, timewise_stratified_split

import os
import sys
sys.path.append(sys.path[0][:sys.path[0].find('DVML-P7') + len('DVML-P7')])

from Code.UtilityFunctions.run_query import run_query


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


def batch_get_review_attributes(review_batch: str) -> pd.DataFrame:
    get_review_attr = f"""
    SELECT ?review ?predicate ?object
    WHERE {{
        ?review ?predicate ?object .
        VALUES ?review {{ {review_batch} }} .
    }}
    """

    # Run the SPARQL query and retrieve results as a Pandas DataFrame
    reviews_attrs = run_query(query=get_review_attr, as_dataframe=True)
    
    # Return the DataFrame with the reviews for the users in the batch
    return reviews_attrs


def create_review_triples(reviews: pd.DataFrame):
    train_review_batch = set()  # Create an empty set to store the review URIs in batches
    reviews_list = list()  # Create an empty list to store the resulting dataframes for reviews

    for row in reviews['review.value']:
        train_review_batch.add(row)  # Add the review URI to the user batch cache

        if len(train_review_batch) % 20 == 0:
            # If the review batch cache contains 20 user URIs, format them into a string for the VALUES statement in the query
            formatted_batch = format_values_string(_input=train_review_batch)
            train_review_batch.clear()  # Prepare the review batch cache for the next 20 users

            # Query the graph for review attributes for the current batch of users
            review_batch = batch_get_review_attributes(review_batch=formatted_batch)
            reviews_list.append(review_batch)  # Append the resulting dataframe to the list of reviews

    if len(train_review_batch) > 0:
        # If the last batch is less than 20, we still need to retrieve review attributes
        formatted_batch = format_values_string(_input=train_review_batch)
        review_batch = batch_get_review_attributes(review_batch=formatted_batch)
        reviews_list.append(review_batch)  # Append the resulting dataframe to the list of reviews

    review_triples = pd.concat(reviews_list, ignore_index=True)  # Concatenate all the resulting dataframes into a single dataframe

    return review_triples


def create_review_attribute_graph(triples: pd.DataFrame, stage: str) -> None:
    print(f"Starting on stage {stage}")

    triples = triples.rename(columns={"review.value": "review", "predicate.value": "predicate", "object.value": "object"})

    triple_file = gzip.open(filename=f"/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/yelp_review_{stage}_attributes.nt.gz", mode="at", encoding="utf-8")

    triples_length = len(triples)

    for row in triples.itertuples():
        if row.Index % 5000 == 0:
            print(f"Progress: {triples_length // (row.Index+1)}")

        graph = Graph()

        graph.add(triple=(
            URIRef(row.review),
            URIRef(row.predicate),
            row.object
        ))

        triple_file.write(
            graph.serialize(format='nt')
        )
    
    triple_file.close()


if __name__ == "__main__":
    pos_users = get_positive_users(rating_threshold=3.0, num_reviews_threshold=10)

    user_batch_cache = set()  # Create an empty set to store the user URIs in batches
    reviews_list = list()  # Create an empty list to store the resulting dataframes for reviews

    for row in pos_users.itertuples():
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

    # Save the split csv files 
    # train.to_csv("/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/review_train.csv", index=False)
    # val.to_csv("/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/review_val.csv", index=False)
    # test.to_csv("/home/ubuntu/vol1/OneDrive/DVML-P7/Data/split-files/review_test.csv", index=False)
    
    myfiles=[
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_train_attributes.nt.gz", 
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_val_attributes.nt.gz",
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_test_attributes.nt.gz"
            "/home/ubuntu/vol1/virtuoso/import/yelp_review_all_attributes.nt.gz"
             ]
    for i in myfiles:
        ## If file exists, delete it ##
        if os.path.isfile(i):
            os.remove(i)


    train_triples = create_review_triples(reviews=train)
    validation_triples = create_review_triples(reviews=val)
    test_triples = create_review_triples(reviews=test)
    all_triples = pd.concat([train_triples, validation_triples, test_triples], ignore_index=True)

    create_review_attribute_graph(triples=train_triples, stage="train")
    create_review_attribute_graph(triples=validation_triples, stage="val")
    create_review_attribute_graph(triples=test_triples, stage="test")
    create_review_attribute_graph(triples=all_triples, stage="all")
