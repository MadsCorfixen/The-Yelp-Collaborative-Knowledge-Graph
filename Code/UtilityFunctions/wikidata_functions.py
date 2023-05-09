import sys
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON

def wikidata_query(sparql_query: str):
    """
    It takes a SPARQL query as a string, and returns a pandas dataframe of the results
    
    :param sparql_query: the query you want to run
    :type sparql_query: str
    :return: The query returns the wikidata item id, the wikidata item label, the wikidata item
    description, and the wikidata item category.
    """
    user_agent = "Yelp knowledge graph mapping/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent=user_agent)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    results_df = pd.json_normalize(results['results']['bindings'])
    
    return results_df


def category_query(schema_iri: str):
    return f"""
    SELECT distinct ?item ?itemLabel WHERE{{
        ?item wdt:P1709 <{schema_iri}>.
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en".}}
    }}"""
    