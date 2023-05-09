import os
import pandas as pd
import numpy as np

from Code.UtilityFunctions.string_functions import turn_words_singular, space_words_lower
from sentence_transformers import SentenceTransformer

pd.options.mode.chained_assignment = None

def clean_yelp_categories(read_dir: str):
    """
    Args:
        read_dir (str): the path to read the data from

    Returns:
        list: A list containing all categories, having split the categories with & or /, and singularized
        dict: A dictionary with the original categories as keys and the singularized, and split, categories as values
    """

    biz = pd.read_json(path_or_buf=os.path.join(read_dir, "yelp_academic_dataset_business.json"), lines=True)

    categories_unique = list(set(biz["categories"].str.cat(sep=', ').split(sep=', ')))
    categories_dict = {categories_unique[i]: [categories_unique[i]] for i in range(len(categories_unique))}

    cat_string_manually_handled_df = pd.read_csv(filepath_or_buffer=os.path.join(read_dir, "manually_split_categories.csv"), delimiter=";", header=0)
    cat_string_manually_handled_dict = dict(zip(cat_string_manually_handled_df.iloc[:,0], cat_string_manually_handled_df.iloc[:,1]))
    cat_string_manually_handled_dict = {k: v.split(', ') for k, v in cat_string_manually_handled_dict.items()}
    categories_dict.update(cat_string_manually_handled_dict)

    yelp_categories_dict = turn_words_singular(categories_dict)

    yelp_categories = list({category for sublist in yelp_categories_dict.values() for category in sublist})

    return yelp_categories, yelp_categories_dict


def clean_schema_categories(read_dir: str):
    """
    Args:
        read_dir (str): the path to read the data from

    Returns:
        list: All Schema types turned to lowercase
        dict: All Schema types turned to lowercase as keys and original as values
    """

    schema = pd.read_csv(filepath_or_buffer=os.path.join(read_dir, "schemaorg-current-https-types.csv"))[["label", "subTypeOf"]]

    schema_categories = list(map(lambda x: space_words_lower(x), schema["label"].tolist()))
    schema_categories_dict = dict(zip(schema_categories, schema["label"].tolist()))

    return schema_categories, schema_categories_dict


def cos_sim_2d(x, y):
    """Calculates the cosine similarity between two 2d arrays
    """

    norm_x = x / np.linalg.norm(x, axis=1, keepdims=True)
    norm_y = y / np.linalg.norm(y, axis=1, keepdims=True)

    return np.matmul(norm_x, norm_y.T)


def category_mappings(threshold: float, read_dir: str):
    """Cleans the categories from Yelp and the Schema types. Then calculates the cosine similarity between the two, '
    and finds mappings above a threshold.

    Args:
        threshold (float): The threshold for the cosine similarity
        read_dir (str): the path to read the data from

    Returns:
        dict: A dictionary containing the Yelp category as key and the mapped Schema types as values.
    """

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    yelp_categories, yelp_categories_dict = clean_yelp_categories(read_dir)
    schema_categories, schema_categories_dict = clean_schema_categories(read_dir)

    swapped_yelp_categories = {sub_value: key for key, value in yelp_categories_dict.items() for sub_value in value}

    yelp_embeddings = model.encode(yelp_categories)
    schema_embeddings = model.encode(schema_categories)

    co_sim_matrix = pd.DataFrame(data=cos_sim_2d(yelp_embeddings, schema_embeddings),
                                 index=yelp_categories,
                                 columns=schema_categories
                                 ).apply(pd.to_numeric)

    mappings = pd.DataFrame(data={"mapped_schema": co_sim_matrix.idxmax(axis=1), "similarity": co_sim_matrix.max(axis=1)}, index=co_sim_matrix.index).sort_values(by="similarity", ascending=False).reset_index(names="yelp_category")

    # Getting correct names
    mappings["mapped_schema"] = mappings["mapped_schema"].apply(lambda x: schema_categories_dict.get(x))
    mappings["yelp_category"] = mappings["yelp_category"].apply(lambda x: swapped_yelp_categories.get(x))

    mappings = mappings[mappings['similarity'] >= threshold]
    mappings['mapped_schema'][mappings['mapped_schema'] == "None"] = None

    mapping_dictionary = mappings[["yelp_category", "mapped_schema"]].set_index('yelp_category').stack().groupby(level=0).agg(list).to_dict()

    return mapping_dictionary

