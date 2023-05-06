from rdflib import Namespace

schema = Namespace("https://schema.org/")
skos = Namespace("https://www.w3.org/2004/02/skos/core#")
business_uri = Namespace("https://www.yelp.com/biz/")
user_uri = Namespace("https://www.yelp.com/user_details?userid=")
yelpcat = Namespace("https://purl.archive.org/purl/yckg/categories#")
yelpvoc = Namespace("https://purl.archive.org/purl/yckg/vocabulary#")
yelpent = Namespace("https://purl.archive.org/purl/yckg/entities#")
wd = Namespace("https://www.wikidata.org/entity/")
wdt = Namespace("https://www.wikidata.org/wiki/Property:")
population_predicate = wdt + "P1082"  # P1082 = population
location_predicate = wdt + "P131"  # P131 = located in the administrative territorial entity
instance_of_predicate = wdt + "P31"  # P31 = instance of
