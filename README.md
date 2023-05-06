# The Yelp Collaborative Knowledge Graph
This is the GitHub repository associated with the paper "The Yelp Collaborative Knowledge Graph". In here, we present the abstract of the paper and provide details on the knowledge graph structure and namespaces, as well on how to obtain the knowledge graph.

## Abstract

The Yelp Open Dataset (YOD) contains data about businesses, reviews, and users from the Yelp website and is available for research purposes. This dataset has been widely used to develop and test Recommender Systems (RS), especially those using Knowledge Graphs (KGs), e.g., integrating taxonomies, product categories, business locations, and social network information. Unfortunately, researchers applied naive or wrong mappings while converting YOD in KGs, consequently obtaining unrealistic results. Among the various issues, the conversion processes usually do not follow state-of-the-art methodologies, fail to properly link to other KGs and reuse existing vocabularies. In this work, we overcome these issues by introducing Y2KG, a utility to convert the Yelp dataset into a KG. Y2KG consists of two components. The first is a dataset including (1) a vocabulary that extends Schema.org with properties to describe the concepts in YOD and (2) mappings between the Yelp entities and Wikidata. The second component is a set of scripts to transform YOD in RDF and obtain the Yelp Collaborative Knowledge Graph (YCKG). The design of Y2KG was driven by 16 core competency questions. YCKG includes 150k businesses and 16.9M reviews from 1.9M distinct real users, resulting in over 244 million triples (with 144 distinct predicates) for about 72 million resources, with an average in-degree and out-degree of 3.3 and 12.2, respectively.

## Knowledge Graph Structure
In the figure below, the structure of the YCKG is showcased. Circles represent Yelp IRIs, non-filled circles blank nodes, squares Schema.org IRIs, and diamonds Wikidata IRIs.

<img src="readmeFigs/YelpKGSchema.jpg" width="750" />

For a complete view of the YCKG will all entities and predicates, we refer to the figure found [here](/readmeFigs/FullYCKGOverview.jpg).

### Namespaces
For creating the YCKG, the following namespaces were created:
```ttl
@prefix yelpcat: <https://purl.archive.org/purl/yckg/categories#> .
@prefix yelpvoc: <https://purl.archive.org/purl/yckg/vocabulary#> .
@prefix yelpent: <https://purl.archive.org/purl/yckg/entities#> .
```
Furthermore, the following existing namespaces were also utilised:
```ttl
@prefix schema: <https://schema.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix wd: <https://www.wikidata.org/entity/> .
@prefix wdt: <https://www.wikidata.org/wiki/Property:> .
```

## Knowledge Graph Generation
This section is split into two ways to get the YCKG. You can either [download the KG from Zenodo](#zenodo), or [run the source code on your own machine](#directly-from-source). Furthermore, three versions of the KG are available, depending on preference. (1) a "clean" version of the KG that contains none of the mappings to Schema or Wikidata; (2) a version that contains the mappings to Schema, but not to Wikidata; (3) a version that contains both the mappings to Schema and to Wikidata.

### Requirements
This tool was implemented in Python 3.10.6. For packages used and their versions, see [requirements.txt](requirements.txt).

### Zenodo
The dataset is uploaded on [https://zenodo.org/](https://zenodo.org/). 
- Graph Data Triple Files
    - One sample file for each of the Yelp domains (Businesses, Users, Reviews, Tips and Checkins), containing 20 entities.
    - ```yelp_schema_mappings.nt.gz``` containing the mappings from Yelp categories to Schema things.
    - ```schema_hierarchy.nt.gz``` containing the full hierarchy of the mapped Schema things.
    - ```yelp_wiki_mappings.nt.gz``` containing the mappings from Yelp categories to Wikidata entities.
    - ```wikidata_location_mappings.nt.gz``` containing the mappings from Yelp locations to Wikidata entities.
- Graph Metadata Triple Files
    - ```yelp_categories.ttl``` contains metadata for all Yelp categories.
    - ```yelp_entities.ttl``` contains metadata regarding the dataset
    - ```yelp_vocabulary.ttl``` contains metadata on the created Yelp vocabulary and properties.
- Utility Files
    - ```yelp_category_schema_mappings.csv```. This file contains the 310 mappings from Yelp categories to Schema types. These mappings have been manually verified to be correct. 
    - ```yelp_predicate_schema_mappings.csv```. This file contains the 14 mappings from Yelp attributes to Schema properties. These mappings are manually found.
    - ```ground_truth_yelp_category_schema_mappings.csv```. 
    This file contains the ground truth, based on 200 manually verified mappings from Yelp categories to Schema things.  The ground truth mappings were used to calculate precision and recall for the semantic mappings.

### Directly from Source
To run the code yourself and obtain the YCKG, follow the following steps:
1. Download the [Yelp Open Dataset](https://www.yelp.com/dataset) and put it into a folder of your choice
2. Download the data from the Github folder [UtilityData](UtilityData) and also put it into the same folder as YOD.
   - ```schemaorg-current-https-types.csv```. This file contains the definition of all terms in, all sections of, the vocabulary, plus terms retired from the vocabulary as of Fall 2022. Is used to add the hierarchy of the mapped Schema types to the YCKG.
   - ```yelp_category_schema_mappings.csv```. This file contains the 310 mappings from Yelp categories to Schema types. These mappings have been manually verified to be correct.
3. In the terminal run

```bash
python3.10 create_YCKG.py --read_dir 'path/to/data' --write_dir 'path/to/destination' --include_schema True --include_wikidata True
```

The arguments specify the following:
- ```--read_dir```: The directory in which the data from points 1 and 2 is stored.
- ```--write_dir```: The directory in which the .nt files should be stored.
- ```--include_schema```: If True also creates the .nt files to link YCKG to Schema.
- ```--include_wikidata```: If True also creates the .nt files to link YCKG and Schema to Wikidata.
