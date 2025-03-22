from typing import List

from SPARQLWrapper import SPARQLWrapper, JSON


def build_query(name: str) -> str:
    return f"""
SELECT ?person
WHERE 
{{
  ?person rdfs:label "{name}"@en .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }} 
}}
    """


def make_query(query: str):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query=query)
    sparql.setReturnFormat(JSON)

    # Run the query
    result = sparql.query()
    converted_result = result.convert()

    results = converted_result["results"]
