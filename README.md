# YelpKnowledgeGraph
**NOTE THAT THIS README IS A WORK IN PROGRESS**

Link to paper?

:::TODO:::
- Add meta introduction

## Abstract
The Yelp Open Dataset (YOD) is a subset of data about businesses, reviews, and user data from the Yelp reviews website shared in JSON format.

This dataset has been widely used especially to test models for recommendation systems (RS).

Recently, new RS have been developed to process data in the form of Collaborative Knowledge Graphs, where relationships between products and users are modelled along with contextual information, e.g., product categories, businesses locations, and social network information.

This allows for further contextual data to be integrated to provide more intelligent and personalized recommendations.

Unfortunately, to date, most methods have been tested using a poor representation of the YOD as a graph, called improperly the Yelp KG.

Among the various issues, that representation does not follow any standard and fails to link to an up-to-date open domain KG.

In this work, we overcome these issues and construct a Yelp Collaborative Knowledge Graph (the YCKG), along with a related Yelp KG ontology (containing $5$ classes and $116$ properties), and enrich it with the connections to the Schema.org ontology and Wikidata. 

In this way, this resource will support, among others, research in advanced recommendation engines that can finally adopts the full power of an open-domain KG.

Our dataset  has been designed to support $16$ core competency questions, all of which could be answered by the Yelp KG we created. 

We obtain mappings for  $291$ business categories ($23.6\%$), resulting in $94.6\%$ of all businesses having at least one of their categories mapped to a schema.org concept.

We further aligned parts of our Yelp knowledge graph with categories and locations from Wikidata. 

For the categories, a total of $564$ ($39.8\%$) of the categories are mapped with a `sameAs' relation. 

Likewise, for the locations, we correctly link the city of $96.82\%$ of businesses.

The final knowledge graph contains over $244$ million triples (with $144$ distinct predicates) for approximately $72$ million resources, with an average in-degree and out-degree of $3.35$ and $12.20$ respectively.

## Knowledge Graph Structure
:::TODO:::
- Add meta introduction

<img src="readmeFigs/YelpKGSchema.jpg" width="750" />

### Namespaces
:::TODO:::
- Add wikidata namespace
- Check that all namespaces are present

The following namespaces are used in the Yelp Open Dataset Knowledge Graph:
```ttl
@prefix schema: <https://schema.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
```

## Knowledge Graph Generation
This section is split into two ways to get the Yelp Open Dataset Knowledge Graph. You can either [download the KG from Zenodo](#zenodo), or [run the source code on your own machine](#directly-from-source). Furthermore, three versions of the KG are available, depending on preference. (1) a "clean" version of the KG that contains none of the mappings to Schema or Wikidata; (2) a version that contains the mappings to Schema, but not to Wikidata; (3) a version that contains both the mappings to Schema and to Wikidata.

### Requirements
:::TODO:::

### Zenodo
:::TODO:::

[https://zenodo.org/](https://zenodo.org/)

### Directly from Source
:::TODO:::

```command to do X```

