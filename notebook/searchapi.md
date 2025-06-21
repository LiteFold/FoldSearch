RCSB PDB: Search API Documentation

Search documentation
Search API Basics
Introduction
Build Your Search
Search Services
Return Type
Query Language
Faceted Queries
Search Operators
Date Math Expressions
Search Attributes
Search Results
Dealing with Redundancy
API Clients
Examples
Migration Guides
Acknowledgements
Contact Us
Changelog
RCSB PDB Search API
This API allows searching metadata such as molecule names, sequences, and experimental details for experimental structures from the PDB and certain Computed Structure Models (CSMs).
Reference Documentation: RCSB PDB Search API Reference
Query Editor: RCSB PDB Search API Query Editor
Examples: RCSB PDB Search API Examples
Stay current with API announcements by subscribing to the RCSB PDB API mailing list:

signing in with existing google account and subscribe
or send an email to api+subscribe@rcsb.org
Introduction
The Search API accepts HTTP GET or POST requests with JSON payloads. The base URI of search endpoint is https://search.rcsb.org/rcsbsearch/v2/query. In GET method, search request should be sent as a URL-encoded query string in json parameter: https://search.rcsb.org/rcsbsearch/v2/query?json={search-request}.

Query syntax for the {search-request} is detailed in the Query Language section of this guide. See Build Your Search section for general information on how to construct the {search-request} object.

The search API is designed to return only the identifiers of relevant hits (see Return Type section for more information on the identifiers types that can be requested) and additional metadata. See Response Body section for more information. If you need to extract information on released date, macromolecules, organisms, resolution, modified residues, ligands etc., you should use RCSB Data API: https://data.rcsb.org.

Build Your Search
A search request is a complete specification of what should be returned in a result set. The search request is represented as a JSON object. The building blocks of the request are:

Context Description
return_type Required. Specifies the type of the returned identifiers, e.g. entry, polymer entity, assembly, etc. See Return Type section for more information.
query Optional. Specifies the search expression. Can be omitted if, instead of IDs retrieval, facets or count operation should be performed. In this case the request must be configured via the request_options context.
request_options Optional. Controls various aspects of the search request including pagination, sorting, scoring and faceting. If omitted, the default parameters for sorting, scoring and pagination will be applied.
request_info Optional. Specifies an additional information about the query, e.g. query_id. It's an optional property and used internally at RCSB PDB for logging purposes. When query_id is sent with the search request, it will be included into the corresponding response object.
The query context may consist of two types of clauses:
Terminal node - performs an atomic search operation, e.g. searches for a particular value in a particular field. Parameters in the terminal query clause provide match criteria for finding relevant search hits. The set of parameters differs for different search services.
Group node - wraps other terminal or group nodes and is used to combine multiple queries in a logical fashion.
The simplest query requires specifying only return_type parameter and query context. With unspecified parameters property in the query object, a query matches all documents, returning PDB IDs if the return_type property is set to "entry".

{
"query": {
"type": "terminal",
"service": "text"
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Search Services
The RCSB PDB Search API consolidates requests to heterogeneous search services. The list of available services is below:

Service Description
text Performs attribute searches against textual annotations associated with PDB structures. Refer to Structure Attributes Search page for a full list of annotations.
text_chem Performs attribute searches against textual annotations associated with PDB molecular definitions. Refer to Chemical Attributes Search page for a full list of annotations.
full_text Performs unstructured searches against textual annotations associated with PDB structures or molecular definitions. Unstructured search performs a full-text searches against multiple text attributes.
sequence This service employs the MMseqs2 software and performs fast sequence matching searches (BLAST-like) based on a user-provided FASTA sequence (with E-value or % Identity cutoffs). Following searches are available:
protein: search for protein sequences
dna: search for DNA sequences
rna: search for RNA sequences
seqmotif Performs short motif searches against nucleotide or protein sequences, using three different types of input format:
simple (e.g., CXCXXL)
prosite (e.g., C-X-C-X(2)-[LIVMYFWC])
regex (e.g., CXCX{2}[LIVMYFWC])
structure Performs fast searches matching a global 3D shape of assemblies or chains of a given entry (identified by PDB ID), in either strict (strict_shape_match) or relaxed (relaxed_shape_match) modes, using a BioZernike descriptor strategy.
strucmotif Performs structure motif searches on all available PDB structures.
chemical
Enables queries of small-molecule constituents of PDB structures, based on chemical formula and chemical structure. Both molecular formula and formula range searches are supported. Queries for matching and similar chemical structures can be performed using SMILES and InChI descriptors as search targets. Graph and chemical fingerprint searches are implemented using tools from the OpenEye Chemical Toolkit.

Descriptor Matching Criteria:

The following graph matching searches use a fingerprint prefilter so these are designed to find only similar molecules. These graph matching comparisons include:

graph-exact: atom type, formal charge, bond order, atom and bond chirality, aromatic assignment, valence degree, and atom hydrogen count are used as matching criteria for this search type. Graph matching is performed on the subset of molecules satisfying a fingerprint screening search. Results will include isomorphic and substructure matches within this screened subset.
graph-strict: atom type, formal charge, bond order, atom and bond chirality, aromatic assignment, ring membership, and valence degree are used as matching criteria for this search type. Graph matching is performed on the subset of molecules satisfying a fingerprint screening search. Results will include isomorphic and substructure matches within this screened subset.
graph-relaxed: atom type, formal charge and bond order are used as matching criteria for this search type. Graph matching is performed on the subset of molecules satisfying a fingerprint screening search. Results will include isomorphic and substructure matches within this screened subset.
graph-relaxed-stereo: atom type, formal charge, bond order, atom and bond chirality are used as matching criteria for this search type. Graph matching is performed on the subset of molecules satisfying a fingerprint screening search. Results will include isomorphic and substructure matches within this screened subset.
fingerprint-similarity: Tanimoto similarity is used as the matching criteria for molecular fingerprints. Matches include molecules with scores exceeding 0.6 for TREE type fingerprints or 0.9 for MACCS type fingerprints.
The following graph matching searches perform an exhaustive substructure search with no pre-screening. These substructure graph matching comparisons include:

sub-struct-graph-exact (atom type, formal charge, aromaticity, bond order, atom/bond stereochemistry, valence degree, atom hydrogen count)
sub-struct-graph-strict (atom type, formal charge, aromaticity, bond order, atom/bond stereochemistry, ring membership, valence degree)
sub-struct-graph-relaxed (atom type, formal charge, bond type)
sub-struct-graph-relaxed-stereo (atom type, formal charge, bond type, atom/bond stereochemistry)
Return Type
The search can return one of the following result types:

Type Description
entry Returns a list of PDB IDs.
assembly Returns a list of PDB IDs appended with assembly IDs in the format of a [pdb_id]-[assembly_id], corresponding to biological assemblies.
polymer*entity Returns a list of PDB IDs appended with entity IDs in the format of a [pdb_id]*[entity_id], corresponding to polymeric molecular entities.
non*polymer_entity Returns a list of PDB IDs appended with entity IDs in the format of a [pdb_id]*[entity_id], corresponding to non-polymeric entities (or ligands).
polymer_instance Returns a list of PDB IDs appended with asym IDs in the format of a [pdb_id].[asym_id], corresponding to instances of certain polymeric molecular entities, also known as chains. Note, that asym_id in the instance identifier corresponds to the \_label_asym_id from the mmCIF schema (assigned by the PDB). It can differ from \_auth_asym_id (selected by the author at the time of deposition).
mol_definition Returns a list of molecular definition identifiers that include:
Chemical component entries identified by the alphanumeric code, COMP ID: e.g. ATP, ZN
BIRD entries identified by BIRD ID, e.g. PRD_000154
Query Language
The Search API provides a full query DSL (domain-specific language) based on JSON to define queries.

Basic Search
The query language allows to perform unstructured (basic) searches. An unstructured query refers to the search of textual annotation associated with PDB structures when the field name is unknown. Such query will search across all fields, available for search, and return a hit if match happens in any field.

To perform an unstructured search, you should send the parameters object without an explicit attribute property:

{
"query": {
"type": "terminal",
"service": "full_text",
"parameters": {
"value": "thymidine kinase"
}
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

By default, all terms are optional, as long as one term matches. The query thymidine kinase is translated as thymidine OR kinase. You can wrap the input value with a double-quote mark to change boolean logic to AND, i.e. "thymidine kinase".
Complex boolean queries in the basic search can be built with following operators:

- signifies AND operation
  | signifies OR operation

* negates a single token
  " wraps a number of tokens to signify a phrase for searching
  ( and ) signify precedence
  For example, using a interferon + response + factor query string is equivalent to running interferon AND response AND factor search.

{
"query": {
"type": "terminal",
"service": "full_text",
"parameters": {
"value": "interferon + response + factor"
}
},
"return_type": "entry"
}
open in editortry it out
You can use ( and ) to signify precedence. For example, searching with a query string isopeptide + ( collagen | fibrinogen ) returns structures that contain isopeptide AND either collagen OR fibrinogen.

{
"query": {
"type": "terminal",
"service": "full_text",
"parameters": {
"value": "isopeptide + ( collagen | fibrinogen )"
}
},
"return_type": "entry"
}
open in editortry it out
Attribute Search
Attribute query allows searching for terms with relation to a specific attribute. To perform an attribute search, you should send the parameters object with an explicit attribute property set to a field name, value property set to a search term, and operator property set to a search operator.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "exptl.method",
"operator": "exact_match",
"value": "ELECTRON MICROSCOPY"
}
},
"return_type": "entry"
}
open in editortry it out
Refer to the Examples section for more examples.

When using attribute search, you must observe the following rules:

The field must be a valid field name listed in Structure Attributes Search or Chemical Attributes Search.
The operator must be compatible with the field. Full list of the operators is available in the Search Operators section.
The values entered must match the type of the field and be compatible with the operator. Date values should be specified in ISO 8601 formats:
Date: YYYY-mm-DD
Date and Time: YYYY-mm-DD'T'HH:MM:SS'Z', where the 'Z' means UTC
Negation
To perform negation on the operator, the negation property should be set to true in the query parameters object. The following search returns non-protein polymeric entities:

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"negation": true,
"value": "Protein",
"attribute": "entity_poly.rcsb_entity_polymer_type"
}
},
"return_type": "polymer_entity"
}
open in editortry it out
Refer to the Examples section for more examples.

Case-Sensitive Search
By default, searches performed using exact match operators are case-insensitive. You can make your search case-sensitive by setting the case_sensitive property in the query parameters object to true. This option can be useful when capitalization rules help convey additional information. For example, gene symbols can differ in capitalization between homologous from different species, i.e. human genes are always upper case.

The following search returns human kinases encoded by the ABL1 gene. It excludes results where the case doesn't match, such as non-receptor tyrosine-protein kinase from mouse encoded by the Abl1 gene.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_entity_source_organism.rcsb_gene_name.value",
"operator": "exact_match",
"value": "ABL1",
"case_sensitive": true
}
},
"return_type": "polymer_entity"
}
open in editortry it out
Refer to the Examples section for more examples.

Boolean Expressions
The query language supports two boolean operators: AND and OR. Boolean operators should be added to the group node as logical_operator property. The group nodes can be used to logically combine search expressions (terminal nodes) or other group nodes:

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "group",
"logical_operator": "or",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "Homo sapiens",
"attribute": "rcsb_entity_source_organism.taxonomy_lineage.name"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "Mus musculus",
"attribute": "rcsb_entity_source_organism.taxonomy_lineage.name"
}
}
]
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "greater",
"value": "2019-08-20",
"attribute": "rcsb_accession_info.initial_release_date"
}
}
]
},
"return_type": "polymer_entity"
}
open in editortry it out
Refer to the Examples section for more examples.

Scoring Strategy
You can customize how scores from different services impact the final relevancy ranking of your search results by setting a scoring_strategy in the request_options context. Following scoring strategies are available: combined (default), sequence, seqmotif, strucmotif, structure, chemical, and text. For example, you might want to boost search results based on the relevance score produced by sequence search service, then sequence scoring strategy should be used.

The final relevancy score is calculated as weighted sum of normalized scores produced by different search services (all search result scores are rescaled to the interval [0, 1], 0 still means it met the criteria of the search). When combined strategy is used, equal weights are applied. For other strategies, higher weight is used for select service scores making their contribution to the final score bigger and therefore promoting ranking that is influenced by select service.

Sorting
Sorting is determined by the sort object in the request_options context. It allows you to add one or more sorting conditions to control the order of the search result hits. The sort operation is defined on a per field level, with special field name for score to sort by score (the default).

Structure Attributes Search and Chemical Attributes Search pages to find all searchable attributes. Any attribute listing exact_match or equals operators can be used for sorting.

By default sorting is done in descending order ("desc"). The sort can be reversed by setting direction property to "asc". This example demonstrates how to sort the search results by release date:

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "struct.title",
"operator": "contains_phrase",
"value": "\"hiv protease\""
}
},
"request_options": {
"sort": [
{
"sort_by": "rcsb_accession_info.initial_release_date",
"direction": "desc"
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to the Examples section for more examples.

Pagination
By default, only first 10 hits are included in the search result list. Pagination can be configured by the start and rows parameters of the paginate object in the request_options context.

Note that the maximum number of hits that can be retrieved in a single pagination request, with start and rows, is 10,000.
{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity.formula_weight",
"operator": "greater",
"value": 500
}
},
"request_options": {
"paginate": {
"start": 0,
"rows": 100
}
},
"return_type": "polymer_entity"
}
open in editortry it out
To retrieve all hits use the return_all_hits parameter in the request_options context. Please note that returning all hits is generally not desirable and may be the source of performance issues.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_entry_info.selected_polymer_entity_types",
"operator": "exact_match",
"value": "Nucleic acid (only)"
}
},
"request_options": {
"return_all_hits": true
},
"return_type": "entry"
}
open in editortry it out
Refer to the Examples section for more examples.

Counting Results
By default, the search results contains a list of matched identifiers and additional metadata. See Search Results for more details. The return_counts flag in the request_options context allows you to execute a search query and get back only the number of matches for that query. The following query returns a number of current structures in the PDB archive:

{
"query": {
"type": "terminal",
"service": "text"
},
"request_options": {
"return_counts": true
},
"return_type": "entry"
}
open in editortry it out
Refer to the Examples section for more examples.

Include Computed Models
RCSB PDB has integrated Computed Structure Models from AlphaFold DB and ModelArchive. To include Computed Structure Models into your search results, add results_content_type parameter to the request_options context. This parameter allows to specify the content type filter that can include experimental, computational structures or both.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_uniprot_protein.name.value",
"operator": "exact_match",
"value": "Free fatty acid receptor 2"
}
},
"return_type": "entry",
"request_options": {
"results_content_type": [
"computational",
"experimental"
]
}
}
open in editortry it out
Refer to the Examples section for more examples.

Faceted Queries
Faceted queries (or facets) provide you with the ability to group and perform calculations and statistics on PDB data by using a simple search query. Facets are the arrangement of search results into categories (buckets) based on the requested field values.

If the facets property is specified in the request_options context, the search results are presented along with numerical counts of how many matching IDs were found for each term requested in the facets. If the query context is omitted in the search request with facets specified, the response will contain only the facet counts.

This example calculates the breakdown by experimental method of PDB structures, released after 2019-08-20:

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"operator": "greater",
"value": "2019-08-20",
"attribute": "rcsb_accession_info.initial_release_date"
}
},
"request_options": {
"facets": [
{
"name": "Methods",
"aggregation_type": "terms",
"attribute": "exptl.method"
}
]
},
"return_type": "entry"
}
open in editortry it out
By default, searches containing a faceted query return both search hits and aggregation results. To return only aggregation results, set rows to 0 in the pagination context:

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"operator": "greater",
"value": "2019-08-20",
"attribute": "rcsb_accession_info.initial_release_date"
}
},
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Methods",
"aggregation_type": "terms",
"attribute": "exptl.method"
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Terms Facets
Terms faceting is a multi-bucket aggregation where buckets are dynamically built - one per unique value. For each bucket terms faceting counts the documents (entry, polymer_entity, etc.) that contain a given value in a given field. For example, you can run the terms aggregation on the field rcsb_primary_citation.rcsb_journal_abbrev which holds the abbreviated name of a journal associated with an entry. In return, we have buckets for each journal, each with their PDB entry counts.

You can specify a threshold value for a count associated with a bucket for that bucket to be returned. Use min_interval_population parameter, e.g. in this example only journals associated with at least 1000 entries are returned:

You can also control the returned number of buckets using max_num_intervals parameter (up to 65536 limit). Larger values of max_num_intervals use more memory to compute and, push the whole aggregation close to the limit. You’ll know you’ve gone too large if the request fails with a message about max_buckets.

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Journals",
"aggregation_type": "terms",
"attribute": "rcsb_primary_citation.rcsb_journal_abbrev",
"min_interval_population": 1000
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Histogram Facets
Histogram faceting is a multi-bucket aggregation that can be applied on numeric values. It builds fixed size (a.k.a. interval) buckets over the values. For example, for the rcsb_polymer_entity.formula_weight field that holds a formula mass (KDa) of the entity, we can configure this aggregation to build buckets with interval 50 KDa:

You can use the min_interval_population parameter to request buckets with a higher or equal count associated with it.

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Formula Weight",
"aggregation_type": "histogram",
"attribute": "rcsb_polymer_entity.formula_weight",
"interval": 50,
"min_interval_population": 1
}
]
},
"return_type": "polymer_entity"
}
open in editortry it out
Refer to Examples section for more examples.

Date Histogram Facets
This multi-bucket aggregation is similar to the histogram aggregation, but it can only be used with date values. Calendar-aware intervals are configured with the interval parameter. For example, we can configure this aggregation to build buckets with 1 year intervals:

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Release Date",
"aggregation_type": "date_histogram",
"attribute": "rcsb_accession_info.initial_release_date",
"interval": "year",
"min_interval_population": 1
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Range Facets
A multi-bucket aggregation that enables the user to define a set of numeric ranges - each representing a bucket. Note that this aggregation includes the from value and excludes the to value for each range. Omitted from or to parameters creates a bucket with min or max boundaries. Example:

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Resolution Combined",
"aggregation_type": "range",
"attribute": "rcsb_entry_info.resolution_combined",
"ranges": [
{
"to": 2
},
{
"from": 2,
"to": 2.2
},
{
"from": 2.2,
"to": 2.4
},
{
"from": 4.6
}
]
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Date Range Facets
This multi-bucket aggregation is similar to the range aggregation but dedicated for date values. The main difference between this aggregation and the normal range aggregation is that the from and to values can be expressed in date math expressions. Example:

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Release Date",
"aggregation_type": "date_range",
"attribute": "rcsb_accession_info.initial_release_date",
"ranges": [
{
"to": "2020-06-01||-12M"
},
{
"from": "2020-06-01",
"to": "2020-06-01||+12M"
},
{
"from": "2020-06-01||+12M"
}
]
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Cardinality Facets
Cardinality faceting is single-value metrics aggregation that calculates a count of distinct values returned for a given field. For example, you can count unique source organism name assignments in the PDB archive:

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Organism Names Count",
"aggregation_type": "cardinality",
"attribute": "rcsb_entity_source_organism.ncbi_scientific_name"
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Filter Facets
As its name suggests, the filter aggregation helps you filter documents that contribute to bucket count. In the example below, we are filtering only protein chains which adopt 2 different beta propeller arrangements according to the CATH classification:

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"filter": {
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"attribute": "rcsb_polymer_instance_annotation.type",
"value": "CATH"
}
},
"facets": [
{
"filter": {
"type": "terminal",
"service": "text",
"parameters": {
"operator": "in",
"value": [
"2.140.10.30",
"2.120.10.80"
],
"attribute": "rcsb_polymer_instance_annotation.annotation_lineage.id"
}
},
"facets": [
{
"name": "CATH Domains",
"min_interval_population": 1,
"attribute": "rcsb_polymer_instance_annotation.annotation_lineage.id",
"aggregation_type": "terms"
}
]
}
]
}
]
},
"return_type": "polymer_instance"
}
open in editortry it out
Refer to Examples section for more examples.

Multi-Dimensional Facets
Complex, multi-dimensional aggregations are possible as in the example below:

{
"request_options": {
"paginate": {
"rows": 0
},
"facets": [
{
"name": "Experimental Method",
"aggregation_type": "terms",
"attribute": "rcsb_entry_info.experimental_method",
"facets": [
{
"name": "Polymer Entity Types",
"aggregation_type": "terms",
"attribute": "rcsb_entry_info.selected_polymer_entity_types"
},
{
"name": "Release Date",
"aggregation_type": "date_histogram",
"attribute": "rcsb_accession_info.initial_release_date",
"interval": "year"
}
]
}
]
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Search Operators
Search operators are commands that help you make your search more specific and focused. The following operators can be used to perform a field search:

Exact Match Operators
Exact match operators indicate that the input value should match a field value exactly (including whitespaces, special characters and case).

exact_match
You can use the exact_match operator to find exact occurrences of the input value. Comparisons with exact_match operator are case-insensitive by default. See the Case-Sensitive Search paragraph of the Attribute Search section to learn how to configure case-sensitive exact searches.

A single value input is required for this operator and must be a string.

in
The in operator allows you to specify multiple values in a single search expression. It returns results if any value in a list of input values matches. It can be used instead of multiple OR conditions. Comparisons with in operator are case-sensitive.

An input value is required for this operator and it must be a list of strings, numbers or dates.

Full-Text Operators
The full-text operators enable you to perform linguistic searches against text data by operating on words and phrases. The input text is analyzed before performing a search. The analysis includes following transformations:

Most punctuation is removed
The remaining content is broken into individual words, called tokens
Tokens are lowercased which makes search case-insensitive
The standard grammar based tokenization is used to break input text into tokens. Refer to the Unicode Text Segmentation documentation for more information on tokenization rules.

contains_words
The contains_words operator performs a full-text search by operating on words in provided text. After text is broken into tokens, more basic queries are constructed and OR boolean logic used to interpret the query. For example, "actin-binding protein" will be interpreted as "actin" OR "binding" OR "protein". The search will return results if any of these tokens match. This operator can match multiple tokens in any order.

A single value input is required for this operator and it must be a string.

contains_phrase
The contains_phrase operator performs a full-text search by operating on phrases. The operator will require the following criteria fulfilled in order to return results:

All the tokens must appear in the field
They must have the same order as in the input text
For example, "actin-binding protein" will be interpreted as "actin" AND "binding" AND "protein" occurring in a given order.

A single value input is required for this operator and it must be a string.

Comparison Operators
greater, less, greater_or_equal, less_or_equal, equals operators match fields whose values are larger, smaller, larger or equal, smaller or equal to the given input value.

A single value input is required for this operator and it must be a number or date.

Range Operator
The range operator can be used to match values within a provided range.

A single value input is required for this operator and it must be an object as follows:

{
"from": "[number|date]",
"include_lower": "[boolean]",
"to": "[number|date]",
"include_upper": "[boolean]"
}
By default, lower and upper bounds are excluded. They can be included by setting include_lower and include_upper to true respectively. An inclusive bound means that the boundary point itself is included in the range as well, while an exclusive bound means that the boundary point is not included in the range.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_accession_info.initial_release_date",
"operator": "range",
"value": {
"from": "2019-01-01",
"to": "2019-06-30"
}
}
},
"return_type": "entry"
}
open in editortry it out
Refer to Examples section for more examples.

Exists Operator
The exists is a logical operator that allows you to check whether a given field contains any value. To be deemed as non-existent the value must be null or []. The following values will indicate the field does exist:

Empty strings, such as " " or "-"
Arrays containing null and another value, such as [null, "foo"]
The operator doesn't require a value.

Date Math Expressions
Comparison and range operators support using date math expression. The expression starts with an "anchor" date, which can be: a) now or b) a date string (in the applicable format) ending with ||. The anchor can then be followed by a math expression, supporting + and -, e.g. "2020-06-01||-12M", "now-1w".

The units supported are:

y (year)
M (month)
w (week)
Search Attributes
The attributes available for search include the annotations described by mmCIF dictionary, annotations coming from external resources and attributes added by RCSB PDB. Both internal additions to the mmCIF dictionary and external resources annotations are prefixed with rcsb\_.

Refer to the Structure Attributes Search and Chemical Attributes Search pages for a full list of the attributes that are available for text searches.

Search Results
The HTTP Status 200 (OK) status code indicates that the search API request has been processed successfully and that server returns search results data. The response data is formatted in JSON and its structure is determined by parameters in the query. Query parameters can be used to structure the result set in the following ways:

Specify the granularity of the returned identifiers. See Return Type.
Order results. See Sorting.
Limit the number of hits in the results (10 by default). See Pagination.
Include only the results count. See Counting Results.
Include search facets. See Requesting Facets.
Response Body
The search response body provides details about the search execution itself as well as an array of the individual search hits. Following information is available in the search results response body:

Name Description
query_id Required. Unique query ID assigned to the request or passed as a query parameter.
result_type Required. Specifies the granularity of the returned identifiers requested in the query. See Return Type.
total_count Required. The total number of matched identifiers.
explain_metadata Optional. Contains details on the query execution time (in milliseconds).
result_set Optional. Search results set is returned as PDB identifiers and accompanying metadata.
group_set Optional. Search results are returned as groups.
facets Optional. Facets array contains search facets for requested attributes.
An example of search response is shown below:

{
"query_id": "ce0e1f8a-2a66-4e3f-8b8b-7ecdb1e3458d",
"result_type": "entry",
"total_count": 2,
"result_set": [
{
"identifier": "2V01",
"score": 0.719
},
{
"identifier": "3CLN",
"score": 0.813
}
]
}
Results Set
Results set is an array of objects representing search hits. Each hit contains the matching identifier, score, and metadata produced by search services.

Result Identifiers
While a search query might include a large number of attributes, only the matching PDB identifiers, representing a desired level of granularity, are included in the result set. Following notation is used for PDB identifiers:

[pdb_id] - for PDB entries (e.g. 4HHB)
[pdb_id]\_[entity_id] - for polymer, branched, or non-polymer entities (e.g. 4HHB_1)
[pdb_id].[asym_id] - for polymer, branched, or non-polymer entity instances (e.g. 4HHB.A)
[pdb_id]-[assembly_id] - for biological assemblies (e.g. 4HHB-1)
Relevancy Score
The final relevancy score is calculated as weighted sum of normalized scores produced by different search services. By default, scores from all services are weighted equally. See Scoring Strategy section for more details on how to configure scoring. The higher the score, the more relevant result hit is.

Service Metadata
Different search services produce different metadata and use different scoring metrics. Set the results verbosity level to verbose return the additional metadata and raw scores reported as described below:

Name Description
node_id Required. Distinct numeric ID is assigned to results produced by each search service.
original_score Required. The original (raw) score produced by a search service chosen as relevance score for this service. For example, the bit score of the alignment is chosen as raw relevance score for a sequence search service.
norm_score Required. The original score transformed onto a scale between 0 and 1 using min-max normalization algorithm (higher means more significant).
match_context Optional. Additional metadata produced by search services. Match context will be included only for select return types. For example, is sequence search was performed and polymer_entity is specified as return type, the results will include matching_context with additional metadata such as sequence identity, E-value, bit-score values and the residue boundary positions of the matching sequence. The matching_context will not be included if same search is performed, but the return type is set to entry or assembly.
The following snippet shows an example of search results for a query that combines 4 different search services. Here, the search results set contains one search hit at the granularity of PDB entry:

{
"result_set": [
{
"identifier": "6W2A",
"score": 1.998,
"services": [
{
"service_type": "text",
"nodes": [
{
"node_id": 21049,
"original_score": 8.183,
"norm_score": 1
}
]
},
{
"service_type": "sequence",
"nodes": [
{
"node_id": 2819,
"original_score": 330,
"norm_score": 0.21
}
]
},
{
"service_type": "structure",
"nodes": [
{
"node_id": 12876,
"original_score": 60.825,
"norm_score": 0.608
}
]
},
{
"service_type": "chemical",
"nodes": [
{
"node_id": 11162,
"original_score": 1,
"norm_score": 1
}
]
}
]
}
]
}
Results Verbosity Level
By default, search results are returned with additional metadata (see Search Results for more details). Results verbosity level can be adjusted by setting the results_verbosity parameter in the request_options context. The results' verbosity levels from the most verbose to the least are as follows:

verbose - every search hit is returned in a format described in Result Identifiers with all metadata items set
minimal (default) - every search hit is returned in a format described in Result Identifiers with only a relevancy score set
compact - every search hit is returned as a simple string, e.g. "4HHB", with no additional metadata
{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"operator": "equals",
"value": 4,
"attribute": "rcsb_entry_info.polymer_entity_count_RNA"
}
},
"request_options": {
"results_verbosity": "compact"
},
"return_type": "entry"
}
open in editortry it out
Empty Results
The HTTP Status 204 (No Content) status code indicates that the search API request has been processed successfully but no search hits were found.

Dealing with Redundancy
The PDB archive includes multiple structures of same molecule, providing snapshots of the structure, interactions, and functions of these particular molecules which leads to redundancy. For example, the same protein studied in different experimental conditions or with different ligands bound. This leads to data redundancy that may present some challenges in bioinformatics analyses. It is helpful to be able to remove redundancy and group search results as this helps ensuring that similar and homologous proteins that appear in high numbers in a set of results do not introduce undesirable biases. Also, as the size of the PDB continues to grow, reducing redundancy helps when one seeks to obtain smaller datasets of distinct representatives.

Redundancy occurs at many levels (such as the level of sequence or structure similarity), and different grouping methods can be applied to PDB data in order to provide a non-redundant view.

Group By Parameters
To enable results grouping, the group_by parameters must be defined in the request_options context. Different grouping methods are available for a given Return Type:

Return Type Grouping Options
entry
matching_deposit_group_id - grouping on the basis of common identifier for a group of entries deposited as a collection. Such entries enter the PDB archive via GroupDep system that allows for parallel deposition of 10s–100s of related structures (typically the same protein with different bound ligands).
polymer_entity
sequence_identity - grouping on the basis of protein sequence clusters that meet a predefined identity threshold. Six levels of sequence identity are defined: 100%, 95%, 90%, 70%, 50%, 30%. Mutual sequence identity is determined by MMseqs2 software.
matching_uniprot_accession - grouping on the basis of common UniProt accession. UniProtKB assigns a unique accession for each protein products encoded by one gene in a given species.
Group By Return Type
The group_by_return_type parameter in the request_options context controls the form in which the grouped results are returned. Following options are available:

representatives (default) - a single representative is selected from each group and a flat list of representatives is returned in the main results format. Representative is selected as a top ranked group member. The ranking criteria is controlled by the ranking_criteria_type parameter (see Group Members Ranking).
groups - search results are divided into groups and and each group is returned with all associated search hits (members of that group that satisfy given search constraints).
Return Grouped Results
It can be useful to study the variability among similar (redundant) search hits. You can use the group_by parameters in combination with the group_by_return_type parameter set to groups to return results as groups of similar objects. Few examples are listed below:

Group By Sequence Identity
This example groups together identical human sequences from high-resolution (1.0-2.0Å) structures determined by X-ray crystallography. Among the resulting groups, there is a cluster of human glutathione transferases in complex with different substrates.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "Homo sapiens",
"attribute": "rcsb_entity_source_organism.taxonomy_lineage.name"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "exptl.method",
"operator": "exact_match",
"value": "X-RAY DIFFRACTION"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_entry_info.resolution_combined",
"operator": "range",
"value": {
"from": 1,
"include_lower": true,
"to": 2,
"include_upper": true
}
}
}
]
},
"request_options": {
"results_verbosity": "minimal",
"group_by": {
"aggregation_method": "sequence_identity",
"similarity_cutoff": 100,
"ranking_criteria_type": {
"sort_by": "entity_poly.rcsb_sample_sequence_length",
"direction": "desc"
}
},
"group_by_return_type": "groups"
},
"return_type": "polymer_entity"
}
open in editortry it out
Group By UniProt Accession
This example demonstrates how to use matching_uniprot_accession grouping to get distinct Spike protein S1 proteins released from the beginning of 2020 with. Here, all entities are represented by distinct groups of SARS-CoV, SARS-CoV-2 and Pangolin coronavirus spike proteins.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity.pdbx_description",
"operator": "contains_phrase",
"value": "Spike protein S1"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_accession_info.initial_release_date",
"operator": "greater",
"value": "2020-01-01"
}
}
]
},
"request_options": {
"results_verbosity": "minimal",
"group_by": {
"aggregation_method": "matching_uniprot_accession",
"ranking_criteria_type": {
"sort_by": "coverage"
}
},
"group_by_return_type": "groups"
},
"return_type": "polymer_entity"
}
open in editortry it out
Although it’s true that a search hit will only appear once within a grouped set of search hits, it’s important to note that in some cases multiple groups can contain the same search hit. For example, when results are grouped by the UniProt accession, chimeric entities will appear in multiple groups.

Remove Redundant Results
It can be useful to remove redundant search hits from your results. You can use the group_by parameters in combination with the group_by_return_type parameter set to representatives to return only a single representative from each of resulting groups. For example, you may want to remove similar sequences with specific levels of mutual sequence identity. Non-redundant result set will consist solely of representative search hits from the original redundant search results that satisfy given search constraints.

This example shows how to retrieve a set of polymer entities from protein-protein complexes with the following constraints:

Must be from a protein-protein complex, not a single protein
Complexes must consist of proteins only
Experimental Method: X-ray or EM
Resolution: <= 2 Angstrom
R-observed <= 0.2
Sequence identity cutoff to remove redundancy: 30%
{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "greater_or_equal",
"value": 2,
"attribute": "rcsb_assembly_info.polymer_entity_instance_count_protein"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_entry_info.selected_polymer_entity_types",
"operator": "exact_match",
"value": "Protein (only)"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "exptl.method",
"operator": "in",
"value": [
"X-RAY DIFFRACTION",
"ELECTRON MICROSCOPY"
]
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "less_or_equal",
"value": 2,
"attribute": "rcsb_entry_info.resolution_combined"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "less_or_equal",
"value": 0.2,
"attribute": "refine.ls_R_factor_obs"
}
}
]
},
"request_options": {
"results_verbosity": "minimal",
"group_by": {
"aggregation_method": "sequence_identity",
"similarity_cutoff": 30
},
"group_by_return_type": "representatives"
},
"return_type": "polymer_entity"
}
open in editortry it out
Group Members Ranking
Group members ranking is designed to order the search hits in each of the resulting groups to present most relevant, useful hits first so that you can more easily find what you’re looking for.

The ranking system is made up of a series of options:

ranking by member attribute - this option works in the same way as Sorting. You can use this option to order group members by any property that is available for sorting, for example, resolution, release date, etc.
score (default) - this option orders groups members in a way that puts the most relevant for a given search query hits on top.
ranking options specific to aggregation method - these options are predefined for each aggregation method and typically involve pre-computation based on certain metrics.
For example, you can search for rhodopsins and rhodopsin-like proteins, request all proteins related by sharing at least 50% sequence identity to be grouped and order polymer entities within each group by sequence similarity score:

{
"query": {
"type": "terminal",
"service": "sequence",
"parameters": {
"sequence_type": "protein",
"value": "MNGTEGPNFYVPFSNKTGVVRSPFEAPQYYLAEPWQFSMLAAYMFLLIMLGFPINFLTLYVTVQHKKLRTPLNYILLNLAVADLFMVFGGFTTTLYTSLHGYFVFGPTGCNLEGFFATLGGEIALWSLVVLAIERYVVVCKPMSNFRFGENHAIMGVAFTWVMALACAAPPLVGWSRYIPEGMQCSCGIDYYTPHEETNNESFVIYMFVVHFIIPLIVIFFCYGQLVFTVKEAAAQQQESATTQKAEKEVTRMVIIMVIAFLICWLPYAGVAFYIFTHQGSDFGPIFMTIPAFFAKTSAVYNPVIYIMMNKQFRNCMVTTLCCGKNPLGDDEASTTVSKTETSQVAPA",
"identity_cutoff": 0.3,
"evalue_cutoff": 0.1
}
},
"request_options": {
"results_verbosity": "minimal",
"group_by": {
"aggregation_method": "sequence_identity",
"similarity_cutoff": 50,
"ranking_criteria_type": {
"sort_by": "score",
"direction": "asc"
}
},
"group_by_return_type": "groups"
},
"return_type": "polymer_entity"
}
open in editortry it out
Examples of ranking options specific to aggregation method are detailed below:

Ranking Options For UniProt Groups
coverage the percent coverage of the UniProt sequence by the PDB polymer entity sequence
Faceting Upon Grouped Results
By default, facet counts are based upon the original query results, not the grouped results. This means that whether or not you turn grouping on for a query, the facet counts will be the same.

To return non-redundant facet counts the group_by_return_type parameter must be set to representatives.

Sorting Grouped Results
An important aspect is the way sorting interacts with grouping. By default, all groups are sorted based upon the number of search hits in the group (in descending order by default). You can reverse the order in which groups are sorted. Inside each group, the search hits are sorted based on the ranking score. The type of the ranking score is specified by the ranking_criteria_type parameter.

Another important difference is that multi-sort operations are not enabled for grouped results.

Paging Grouped Results
The Pagination section describes how the Search API uses rows parameter to determine how many search hits to return for a search query. When grouped results are requested, this parameter is putting a limit on how many groups to return. When using start parameter with grouped results, it controls paging through available groups. There is no paging through the results within a group, all search hits per group are returned.

Counting Grouped Results
The Counting Results section of this guide describes the parameter that allows returning only the total count of hits returned by the query. When using it with grouped results, it returns a total count of all resulting groups or representatives.

API Clients
Python
The rcsb-api package provides a Python interface to the RCSB PDB Search and Data APIs (an overview has been published in Journal for Molecular Biology). Use the rcsbapi.search module to fetch lists of PDB IDs corresponding to advanced query searches, and the rcsbapi.data module to fetch data about a given set of structure IDs. RCSB PDB maintains the current version of this package on GitHub.

You can find example use cases demonstrating how to utilize this package in scripting workflows in the py-rcsb-api GitHub repository. These examples provide practical implementations of common tasks, helping users understand how to integrate the package into their own applications. The notebooks serve as a reference for building custom workflows using RCSB resources.

Examples
This section demonstrates how to use the RCSB PDB Search API to perform complex searches.

Biological Assembly Search
This query finds symmetric dimers having a twofold rotation with the DNA-binding domain of a heat-shock transcription factor.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "C2",
"attribute": "rcsb_struct_symmetry.symbol"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "Global Symmetry",
"attribute": "rcsb_struct_symmetry.kind"
}
},
{
"type": "terminal",
"service": "full_text",
"parameters": {
"value": "\"heat-shock transcription factor\""
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "greater_or_equal",
"value": 1,
"attribute": "rcsb_entry_info.polymer_entity_count_DNA"
}
}
]
},
"return_type": "assembly"
}
open in editortry it out
X-Ray Structures Search
This query finds PDB structures of virus's thymidine kinase with substrate/inhibitors, determined by X-ray crystallography at a resolution better than 2.5 Å.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "full_text",
"parameters": {
"value": "\"thymidine kinase\""
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "Viruses",
"attribute": "rcsb_entity_source_organism.taxonomy_lineage.name"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "X-RAY DIFFRACTION",
"attribute": "exptl.method"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "less_or_equal",
"value": 2.5,
"attribute": "rcsb_entry_info.resolution_combined"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "greater",
"attribute": "rcsb_entry_info.nonpolymer_entity_count",
"value": 0
}
}
]
},
"return_type": "entry"
}
open in editortry it out
Protein Sequence Search
In this example, using sequence search, we find macromolecular PDB entities that share 90% sequence identity with GTPase HRas protein from Gallus gallus (Chicken).

{
"query": {
"type": "terminal",
"service": "sequence",
"parameters": {
"evalue_cutoff": 1,
"identity_cutoff": 0.9,
"sequence_type": "protein",
"value": "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHQYREQIKRVKDSDDVPMVLVGNKCDLPARTVETRQAQDLARSYGIPYIETSAKTRQGVEDAFYTLVREIRQHKLRKLNPPDESGPGCMNCKCVIS"
}
},
"request_options": {
"scoring_strategy": "sequence"
},
"return_type": "polymer_entity"
}
open in editortry it out
3D-shape Search
This example demonstrates how structure search can be used to find PDB structures of calmodulin with conformational changes upon Ca2+ binding. Calmodulin (CaM) protein has two homologous globular domains connected by a flexible linker. Ca2+ binding to each globular domain causes a change from a “closed” to an “open” conformation. This query finds calmodulin structures in “open” conformation.

As a structure query input parameter we will use the crystal structure of Ca2+-loaded calmodulin (PDB entry 1CLL). This query is combined with the text search for CA chemical component ID. Note: if you leave out the query clause matching Ca2+ ions, you will also get calmodulin structures in complex with other metals (e.g. strontium in 4BW7).

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text_chem",
"parameters": {
"operator": "exact_match",
"value": "CA",
"attribute": "rcsb_chem_comp_container_identifiers.comp_id"
}
},
{
"type": "terminal",
"service": "structure",
"parameters": {
"value": {
"entry_id": "1CLL",
"assembly_id": "1"
},
"operator": "strict_shape_match"
}
}
]
},
"return_type": "entry"
}
open in editortry it out
Free Ligand Search
Ligands are considered “free ligands” when they interact non-covalently with macromolecules. This example shows how to find non-polymeric entities of ATP molecule that is found as “free ligand”.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_nonpolymer_instance_annotation.comp_id",
"operator": "exact_match",
"value": "ATP"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_nonpolymer_instance_annotation.type",
"operator": "exact_match",
"value": "HAS_NO_COVALENT_LINKAGE"
}
}
]
},
"return_type": "non_polymer_entity",
"request_options": {
"results_verbosity": "compact"
}
}
open in editortry it out
Sequence Motif Search
A sequence motif search finds macromolecular PDB entities that contain a specific sequence motif. This examples retrieves occurrences of the His2/Cys2 Zinc Finger DNA-binding domain as represented by its PROSITE signature.

{
"query": {
"type": "terminal",
"service": "seqmotif",
"parameters": {
"value": "C-x(2,4)-C-x(3)-[LIVMFYWC]-x(8)-H-x(3,5)-H.",
"pattern_type": "prosite",
"sequence_type": "protein"
}
},
"return_type": "polymer_entity"
}
open in editortry it out
Chemical Similarity Search
This example demonstrates how to find molecular definitions chemically similar to Tylenol defined by the InChI string. Note, that the parameter match_type="graph-strict" does not imply exact structure match and you are getting acetaminophen molecules (TYL) together with methoxy (T9V) and ethoxy (N4E) analogs in the result set.

{
"query": {
"type": "terminal",
"service": "chemical",
"parameters": {
"value": "InChI=1S/C8H9NO2/c1-6(10)9-7-2-4-8(11)5-3-7/h2-5,11H,1H3,(H,9,10)",
"type": "descriptor",
"descriptor_type": "InChI",
"match_type": "graph-strict"
}
},
"return_type": "mol_definition"
}
open in editortry it out
Search by UniProt Accession
This example shows how to search for PDB entities using associated UniProt accession code.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "P69905",
"attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "UniProt",
"attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_name"
}
}
]
},
"return_type": "polymer_entity"
}
open in editortry it out
Structure Motif Search
A structure motif search finds macromolecular PDB assemblies that contain a specific arrangement of a small number of residues in a certain geometric arrangement (e.g. residue that constitute the catalytic center or a binding site). This examples retrieves occurrences of the enolase superfamily, a group of proteins diverse in sequence and structure that are all capable of abstracting a proton from a carboxylic acid. Position-specific exchanges are crucial to represent this superfamily accurately.

{
"query": {
"type": "terminal",
"service": "strucmotif",
"parameters": {
"value": {
"entry_id": "2mnr",
"residue_ids": [
{
"label_asym_id": "A",
"label_seq_id": 162
},
{
"label_asym_id": "A",
"label_seq_id": 193
},
{
"label_asym_id": "A",
"label_seq_id": 219
},
{
"label_asym_id": "A",
"label_seq_id": 245
},
{
"label_asym_id": "A",
"label_seq_id": 295
}
]
},
"rmsd_cutoff": 2,
"exchanges": [
{
"residue_id": {
"label_asym_id": "A",
"label_seq_id": 162
},
"allowed": [
"LYS",
"HIS"
]
},
{
"residue_id": {
"label_asym_id": "A",
"label_seq_id": 245
},
"allowed": [
"GLU",
"ASP",
"ASN"
]
},
{
"residue_id": {
"label_asym_id": "A",
"label_seq_id": 295
},
"allowed": [
"HIS",
"LYS"
]
}
]
}
},
"return_type": "assembly"
}
open in editortry it out
Combining Search Services
This example shows how to compose text, sequence, structure, and chemical queries employing the Boolean operator AND. The search yields structures (entries) matching all criteria, including co-crystal structures with the desired bound inhibitor, matching the SMILES string for a small-molecule inhibitor designated 7J (QYS).

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"value": "Coronaviridae",
"attribute": "rcsb_entity_source_organism.taxonomy_lineage.name"
}
},
{
"type": "terminal",
"service": "sequence",
"parameters": {
"evalue_cutoff": 1,
"identity_cutoff": 0.5,
"sequence_type": "protein",
"value": "SLSGFRKMAFPSGKVEGCMVQVTCGTTTLNGLWLDDTVYCPRHVICTAEDMLNPNYEDLLIRKSNHSFLVQAGNVQLRVIGHSMQNCLLRLKVDTSNPKTPKYKFVRIQPGQTFSVLACYNGSPSGVYQCAMRPNHTIKGSFLNGSCGSVGFNIDYDCVSFCYMHHMELPTGVHAGTDLEGKFYGPFVDRQTAQAAGTDTTITLNVLAWLYAAVINGDRWFLNRFTTTLNDFNLVAMKYNYEPLTQDHVDILGPLSAQTGIAVLDMCAALKELLQNGMNGRTILGSTILEDEFTPFDVVRQCSGVTEG"
}
},
{
"type": "terminal",
"service": "structure",
"parameters": {
"value": {
"entry_id": "6LU7",
"assembly_id": "1"
},
"operator": "relaxed_shape_match"
}
},
{
"type": "terminal",
"service": "chemical",
"parameters": {
"value": "CC(C)C[C@H](<NC(=O)OCC1CCC(F)(F)CC1>)C(=O)N[C@@H](C[C@@H]2CCNC2=O)[C@@H](O)[S](O)(=O)=O",
"type": "descriptor",
"descriptor_type": "SMILES",
"match_type": "graph-relaxed-stereo"
}
}
]
},
"return_type": "entry"
}
open in editortry it out
Sequence Cluster Statistics
This example shows how to get the number of distinct protein sequences in the PDB archive.

{
"request_options": {
"facets": [
{
"filter": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "exact_match",
"attribute": "rcsb_polymer_entity_group_membership.aggregation_method",
"value": "sequence_identity"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"operator": "equals",
"attribute": "rcsb_polymer_entity_group_membership.similarity_cutoff",
"value": 100
}
}
]
},
"facets": [
{
"name": "Distinct Protein Sequence Count",
"aggregation_type": "cardinality",
"attribute": "rcsb_polymer_entity_group_membership.group_id"
}
]
}
],
"paginate": {
"start": 0,
"rows": 0
}
},
"return_type": "polymer_entity"
}
open in editortry it out
Newly Released Structures
This example shows how to get a list of all PDB ID for this week's newly released structures.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_accession_info.initial_release_date",
"operator": "greater",
"value": "now-1w"
}
},
"request_options": {
"return_all_hits": true
},
"return_type": "entry"
}
open in editortry it out
Membrane Proteins
This example shows how to get a list of PDB ID of entries that are annotated as membrane protein by at least one relevant external resource.

{
"query": {
"type": "group",
"logical_operator": "or",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity_annotation.type",
"operator": "exact_match",
"value": "PDBTM"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity_annotation.type",
"operator": "exact_match",
"value": "MemProtMD"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity_annotation.type",
"operator": "exact_match",
"value": "OPM"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity_annotation.type",
"operator": "exact_match",
"value": "mpstruc"
}
}
]
},
"return_type": "entry"
}
open in editortry it out
Symmetry and Enzyme Classification
This example shows how to get assembly counts per symmetry types, further broken down by Enzyme Classification (EC) classes. The assemblies are first filtered to homo-oligomers only.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_assembly_info.polymer_entity_count",
"operator": "equals",
"value": 1
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_assembly_info.polymer_entity_instance_count",
"operator": "greater",
"value": 1
}
}
]
},
"request_options": {
"facets": [
{
"filter": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_struct_symmetry.kind",
"operator": "exact_match",
"value": "Global Symmetry"
}
},
"facets": [
{
"aggregation_type": "terms",
"name": "sym_symbol_terms",
"attribute": "rcsb_struct_symmetry.symbol",
"facets": [
{
"aggregation_type": "terms",
"name": "ec_terms",
"attribute": "rcsb_polymer_entity.rcsb_ec_lineage.id"
}
]
}
]
}
],
"paginate": {
"start": 0,
"rows": 0
}
},
"return_type": "assembly"
}
open in editortry it out
Computed Structure Models
This example shows how to find PDB structures and Computed Structure Models for a given UniProt sequence.

{
"query": {
"type": "group",
"logical_operator": "and",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
"operator": "exact_match",
"value": "Q5VSL9"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_name",
"operator": "exact_match",
"value": "UniProt"
}
}
]
},
"return_type": "entry",
"request_options": {
"results_content_type": [
"computational",
"experimental"
]
}
}
open in editortry it out
Structure Search with Custom Data
This example showcases how to search with structures not deposited in the PDB archive by pointing to external URLs such as predictions from AlphaFold DB, ModelArchive, or SWISS-MODEL. Any publicly available URL can be referenced. This feature can be used for structure (3D-shape) and strucmotif (structure motif) searches. Required inputs are the file location (url) and format ('cif' or 'bcif' for BinaryCIF). Gzipped content is supported as well.

{
"query": {
"type": "terminal",
"service": "structure",
"parameters": {
"value": {
"url": "https://alphafold.ebi.ac.uk/files/AF-Q8VCK6-F1-model_v4.cif",
"format": "cif"
},
"operator": "relaxed_shape_match"
}
},
"return_type": "assembly"
}
open in editortry it out
Integrative Structures
Search API delivers integrative structures alongside the experimental structures. IHMs combine data from multiple experimental methods (e.g., X-ray crystallography, cryo-EM, NMR, SAXS, crosslinking MS, etc.) to produce structural models. IHMs expand structural coverage to systems difficult to solve using a single method, such as macromolecular machines and dynamic complexes.

The rcsb_entry_info.structure_determination_methodology field indicates the methodology used to determine the structure. Its value determines whether the structure is:

experimental - determined using experimental techniques such as X-ray crystallography, NMR, cryo-EM, etc
integrative - determined using a combination of experimental and computational methods
computational (predicted) - generated purely through computational prediction methods, without direct experimental data
Use this field to distinguish between different types of structure determination approaches in your searches.

Find all IHM entries currently released in the PDB archive.

{
"query": {
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_entry_info.structure_determination_methodology",
"operator": "exact_match",
"value": "integrative"
}
},
"request_options": {
"results_verbosity": "compact",
"return_all_hits": true
},
"return_type": "entry"
}
open in editortry it out
Find all IHM entries of human proteins that use crosslinking mass spectrometry as part of the modeling process.

{
"query": {
"type": "group",
"nodes": [
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_ihm_dataset_list.name",
"operator": "exact_match",
"value": "Crosslinking-MS data"
}
},
{
"type": "terminal",
"service": "text",
"parameters": {
"attribute": "rcsb_entity_source_organism.ncbi_scientific_name",
"operator": "exact_match",
"value": "Homo sapiens"
}
}
],
"logical_operator": "and"
},
"return_type": "entry",
"request_options": {
"results_verbosity": "compact",
"return_all_hits": true
}
}
open in editortry it out
Migration Guides
Migrating from Legacy Search API
Applications written on top of the Legacy Search APIs no longer work because these services have been discontinued. This migration guide describes the necessary steps to convert applications from using Legacy Search API Web Service to a new RCSB Search API.

Migrating from v1 to v2
The following guide will help you migrate from API v1 to v2. This page contains information you need to know when migrating from deprecated API version v1 to a newer version v2.

Acknowledgements
To cite this service, please reference:

Rose, Y., Duarte, J. M., Lowe, R., Segura, J., Bi, C., Bhikadiya, C., ... & Westbrook, J. D. (2021). RCSB Protein Data Bank: architectural advances towards integrated searching and efficient access to macromolecular structure data from the PDB archive. Journal of molecular biology, 433(11), 166704. DOI: 10.1016/j.jmb.2020.11.003
Bittrich, S., Bhikadiya, C., Bi, C., Chao, H., Duarte, J. M., Dutta, S., ... & Rose, Y. (2023). RCSB Protein Data Bank: Efficient Searching and Simultaneous Access to One Million Computed Structure Models Alongside the PDB Structures Enabled by Architectural Advances. Journal of Molecular Biology, 167994. DOI: 10.1016/j.jmb.2023.167994
Related publications:

Berman, H. M., Westbrook, J., Feng, Z., Gilliland, G., Bhat, T. N., Weissig, H., ... & Bourne, P. E. (2000). The protein data bank. Nucleic acids research, 28(1), 235-242. DOI: 10.1093/nar/28.1.235
Burley, S. K., Berman, H. M., Bhikadiya, C., Bi, C., Chen, L., Di Costanzo, L., ... & Zardecki, C. (2019). RCSB Protein Data Bank: biological macromolecular structures enabling research and education in fundamental biology, biomedicine, biotechnology and energy. Nucleic acids research, 47(D1), D464-D474. DOI: 10.1093/nar/gky1004
Burley, S. K., Bhikadiya, C., Bi, C., Bittrich, S., Chao, H., Chen, L., ... & Zardecki, C. (2023). RCSB Protein Data Bank (RCSB. org): delivery of experimentally-determined PDB structures alongside one million computed structure models of proteins from artificial intelligence/machine learning. Nucleic Acids Research, 51(D1), D488-D508. DOI: 10.1093/nar/gkac1077
Contact Us
Contact info@rcsb.org with questions or feedback about this service.

Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

[2.11.0] - 2025-06-05
RO-4713: Remove "Sort by Group Size" feature
[2.10.0] - 2025-06-05
Elastic secret credentials are now passed via environment variables
[2.9.2] - 2025-05-20
RO-4702: fix mismatch between representative selection and ranking criteria
[2.9.1] - 2025-05-15
Integrative structures support
[2.9.0] - 2025-05-09
Enable grouping on non-polymeric entities by chemical component ID
[2.8.2] - 2024-09-05
Fix schema documentation
[2.8.1] - 2024-09-05
Fix NPE on empty result set
[2.8.0] - 2024-09-04
RO-3931: use dedicated ID mapper service instead of in-memory data
[2.7.1] - 2024-09-04
Automated release
[2.7.0] - 2024-08-21
RO-4334: remove dependency on in-memory data for in-app sorting of structure and chemical IDs
[2.6.27] - 2024-08-21
Automated release
[2.6.26] - 2024-08-16
Add support for parsing aggregation results from 'terms' aggregation on floating-point numbers
[2.6.25] - 2024-08-13
Remove explicit dependencies that were only needed due to our custom ES client
[2.6.24] - 2024-08-08
Enable Tomcat server’s internal logs
[2.6.23] - 2024-07-30
Include changelog in artifact
[2.6.22] - 2024-07-15
Cleanup after removal of patched ES client
[2.6.21] - 2024-07-03
Remove pathed ES client
[2.6.20] - 2024-07-02
Minimize the number of parallel requests made to ES during app initialization
[2.6.19] - 2024-05-29
Seqmotif search: Propagate 422 from service
[2.6.18] - 2024-05-24
Shape search: Propagate 404 from service as 404 to users
[2.6.17] - 2024-05-16
Seqmotif search: Stop treating timed out responses as empty result set
[2.6.16] - 2024-05-15
RO-4280: Enable long GET queries
[2.6.15] - 2024-05-09
Conversion to Spring-boot app
[2.6.14] - 2024-04-03
Breaking free of RCSB nexus
[2.6.13] - 2024-04-03
RO-3669: use a single merged index with experimental and computed structures
[2.6.12] - 2024-03-18
Permit syntax that seqmotif search service now allows
[2.6.11] - 2024-03-18
Update "free ligand" query
[2.6.5] - 2024-02-13
RO-3669: use single merged indices with experimental and computed structures
[2.6.3] - 2024-01-12
RO-4165: fix parsing aggregation for numeric fields
[2.6.2] - 2023-12-21
RO-4103: fix normalization for scores returned by ES
[2.6.1] - 2023-12-20
RO-4138: fix missing hits in members ranking
RO-4142: fix 500 error for for pLDDT sorting
RO-4143: fix "free ligand" example
[2.6.0] - 2023-11-30
Second attempt to roll out the Elasticsearch v8
[2.5.11] - 2023-11-21
ES v8 release
[2.5.10] - 2023-11-17
ES v8 release
[2.5.6] - 2023-11-01
Fix query translation logic for nested cases
[2.5.5] - 2023-10-26
RO-4091: listing enum values on attribute search documentation page
[2.5.1] - 2023-08-05
Fixed
issue with nested sorting
[2.5.0] - 2023-08-04
Fixed
RO-2485: issue with combining attributes coming from nested documents
[2.4.11] - 2023-08-03
Fixed
RO-3998: add validation to reject request with page size bigger than configured limit
[2.4.8] - 2023-07-13
Fixed
RO-3967: improved validation for service parameters missmatch
[2.4.8] - 2023-05-22
Fixed
Update tutorial
[2.4.7] - 2023-05-11
Fixed
RO-3836: remove unnecessary validation check from sequence search validation
[2.4.0] - 2023-03-07
Added
RO-3799: expose target_search_space parameter for structure search
[2.3.13] - 2023-03-07
Fixed
RO-3806: Improve error messages for 400s when query is executed
[2.3.11] - 2023-03-03
Fixed
RO-3806: propagate error messages of bad request for structure and strucmotif queries
[2.3.7] - 2023-02-02
Fixed
RO-3634 Search result sub-sorting (alphabetical) on UI is reversed
[2.3.6] - 2023-01-31
Fixed
ID mapper bugfix: instance to entry mapping
[2.3.5] - 2023-01-31
Fixed
Hotfix:
adding filter to count request
avoid duplicates when experimental and computational structures are requested
[2.3.4] - 2023-01-27
Fixed
RO-3623: Fixed issue with translation from chemical component to structure identifiers
[2.3.3] - 2023-01-17
RO-3666: adding filter for computed models index
[2.3.2] - 2023-01-12
Fixed
RO-3673: Refinement/Drilldown menu doesn't show when grouping results
[2.3.1] - 2022-11-28
Fixed
improve error handling when searching by URL
[2.3.0] - 2022-10-07
Added
add search by URL for structure and strucmotif services
[2.2.2] - 2022-09-28
Fixed
HELP-19026: remove Spencer Bliven's rcsbsearch client from the documentation (until it is migrated to v2)
[2.2.1] - 2022-09-02
Fixed
RO-3567: clearer documentation of score normalization and the meaning of scores of 0
[2.2.0] - 2022-08-31
Added
Support of Computed Structure Models (CSM)
[2.1.4] - 2022-07-28
Fixed
RO-3223: handling of modified residues in strucmotif service (some uncommon exchanges enum values were changed)
[2.1.3] - 2022-07-22
Fixed
HELP-18857: fixed inconsistencies in the documentation
[2.1.2] - 2022-07-07
Fixed
Query editor autocompletion based on the Search API request schemas: workaround to enable completion for snippets defines with self-references
[2.1.1] - 2022-06-30
Fixed
RO-2983: Adapt to database name change in sequence motif API
[2.1.0] - 2022-06-24
Added
Added JSON Schema specification for suggest API response
RO-3298: New sequence_type API parameter for sequence and seqmotif search queries. It's meant to replace the target parameter in the future
RO-2539: Added support for schema autocompletion in the editors
Decrease ID mapper memory footprint (by using String[] instead of Set)
Fixed
Update dependencies:
Jackson 2.13.3
Swagger 2.2.0
Log4j 2.17.2
jsonschema2pojo 1.1.1
Introduce folder organisation for JSON schema files
[2.0.1] - 2022-04-20
Added
New tutorial example that shows how to get assembly count per symmetry type with a further breakdown by EC classes
[2.0.0] - 2022-04-13
Breaking Changes
The range_closed operator is deprecated (RO-3091)
The range operator no longer accepts an array of values as an input (RO-3091)
Breaking changes in strucmotif query parameters (RO-3134):
whitelist is renamed to allowed_structures
blacklist is renamed to excluded_structures
empty arrays are disallowed
File upload parameters for structure and strucmotif queries have changed (RO-3144):
file is renamed to data
file_format is renamed to format
gzipped is removed
ccp4 format is no loner supported
The pager parameter in request_options is renamed to paginate
The filter parameter is removed from Terms Facet, Histogram Facet, Date Histogram Facet, Range Facet, Date Range Facet, and Cardinality Facet
The search query syntax in the filter context of the Filter Facet fully supports boolean operations
Following parameters were removed from the faceted (aggregated) search queries (RO-3094):
max_num_intervals is removed from Histogram Facet, Date Histogram Facet, Range Facet, Date Range Facet
min_interval_population is removed from Range Facet, Date Range Facet
min_interval_population default is changed from 0 to 1 (RO-3120)
Search response for faceted (aggregated) search queries has changed (RO-3090):
drilldown is renamed to facets
groups is renamed to buckets
attribute is renamed to name
distinct_count is renamed to value (cardinality facet response)
The default value for results_verbosity parameter was changed from verbose to minimal
Added
Search API v1 to v2 migration guide (RO-3134)
RO-3038: new name parameter is added to the faceted queries to allow setting an aggregation name
[1.13.7] - 2022-04-08
Added
Documentation: API mailing list instructions
[1.13.6] - 2022-04-01
Fixed
Get groups data from a single index
[1.13.5] - 2022-03-18
Fixed
RO-3114: respect schema defaults for current and unreleased queries
sync up request_options parameters between current and unreleased queries
[1.13.4] - 2022-03-11
Fixed
RO-3108: max_num_intervals and precision_threshold defaults come from API schema
[1.13.3] - 2022-03-04
Fixed
RO-3104: improved validation of API requests
Suggester: disallow reserved characters in the input value
[1.13.2] - 2022-02-25
Fixed
RO-3053: more general validation of numeric values
RO-3052: implement sorting on attributes that are inside a nested object
Improved request validation
[1.13.1] - 2022-02-04
Added
Adding dynamic ranges to numeric attributes with nested context metadata
Fixed
Allow strucmotif queries with 2 residues
[1.13.0] - 2022-01-20
Fixed
Upgraded to Java 11
[1.12.3] - 2022-01-05
Fixed
RO-2976: increase the size of the highlighted fragment in characters and revert type to fvh
Upgraded log4j to 2.17.1 to avoid log4shell vulnerability
[1.12.2] - 2021-12-22
Fixed
Upgraded log4j to 2.17.0 to avoid log4shell vulnerability
[1.12.1] - 2021-12-14
Fixed
Upgraded log4j to 2.16.0 to avoid log4shell vulnerability
[1.12.0] - 2021-12-10
Added
API: support for grouping operations
Fixed
RO-2922: change structure to molecular definition mappings to respect entity type
[1.11.5] - 2021-11-23
Fixed
RO-2920: add highlighter type as an API parameter, set default value to 'plain'
missing spinner DOM element for suggester and unreleased search query editor pages
[1.11.4] - 2021-10-08
Fixed
RO-2893: adding additional sort by ID parameter to make sure elements with same ranking maintain the same resulting order
[1.11.3] - 2021-10-01
Fixed
Restrict allowed input length limit for suggester endpoint to 500 characters
[1.11.2] - 2021-10-01
Fixed
Update documentation
[1.11.1] - 2021-09-29
Fixed
RO-2893: Search API pagination is not working correctly when sorting by score and many results have the same score.
[1.11.0] - 2021-09-24
Breaking Changes
API: removed return_service_metadata option, now it should be configured by setting results_verbosity parameter to minimal
API: explain_meta_data renamed to explain_metadata in the results object (is no longer added by default)
Added
API: results_verbosity request option to control the results format and how much metadata to return
API: return_explain_metadata request option to include or exclude explain_metadata object from the results object
Fixed
Strucmotif: Report illegal queries detected at runtime with 400 (bad request) status code
400 responses reported by search services are now reported as is (rather than getting wrapped in 500 responses)
Sequence search validator: disallow sequence type / target database mismatch
Suggester Resource: validate input values - disallow inputs longer than 1000 character (imposed by a limit set in Lucene that permits a recursive function to run only 1000 times before it quits)
Query Resource: return 400 on empty query parameter
[1.10.8] - 2021-09-17
Added
Cancelling running queries if the server did not receive complete results within the time that it was prepared to wait
Fixed
Bug: fixed out of bounds exception for complete suggester
Bug: return 204 when requested pagination boundaries lies outside of the returned result set
[1.10.7] - 2021-09-14
Fixed
Update version and configuration of maven-war-plugin
Return HTTP 400 instead of 500 when unable to parse JSON query
Improved logging
[1.10.6] - 2021-09-13
Fixed
RO-131: Use sentence boundary analysis as a default highlighter configuration. Sentence boundary analysis allows selection with correct interpretation of periods within numbers and abbreviations, and trailing punctuation marks such as quotation marks and parentheses.
[1.10.5] - 2021-09-08
Fixed
Logging results count returned by an individual service
[1.10.4] - 2021-09-03
Fixed
Improvement: handling timeout exceptions and return HTTP 408 Request Timeout
[1.10.3] - 2021-08-26
Fixed
Metadata Service: add missing schema for current entry repository holdings
[1.10.2] - 2021-08-16
Fixed
Bug: safe-guard against null arguments during logging
[1.10.1] - 2021-08-10
Fixed
Bug: filter mixed return type from structure search service
Improvement: explicit structure and strucmotif schema snippets
[1.10.0] - 2021-08-06
Breaking Changes
Strucmotif service:
Removed the now non-functional score_cutoff and scoring_strategy properties from request schema
Use rmsd_cutoff to specify the maximum (RMSD) score
Separated entry and file upload functionality by removing overloaded data property
Separated into entry_id that allows query definition based on a structure in the archive
Add file + file_format + gzipped that allows upload of a custom Base64-encoded structure, supported formats are: bcif, cif
Added
Meta: Expose changelog to the public (RO-2849)
Strucmotif: Service now provides RMSD scores, transformation, and matched residue types (RO-2797)
Strucmotif: Validation limited to 16 exchanges total
Structure/strucmotif search: Allow structure upload via file + file_format + gzipped (RO-2770)
[1.9.2] - 2021-08-05
Added
Enable Elasticsearch client sniffing to keep the state of the cluster in sync with the client’s connection pool
[1.9.1] - 2021-08-03
Added
Request option to exclude service metadata from search results
Fixed
Bug: fixed range operator validation for numeric values
Bug: fixed tracking query ID by the scientific search providers
Improvement: validation for pagination options - only positive integers
Improvement: query service results post-processing implementation
[1.9.0] - 2021-07-29
Added
RO-2598: Support for Molecular Definitions search and return type
[1.8.1] - 2021-06-18
Added
RO-51: deduplicate full-text suggestions
RO-2397: add context info to suggestions
Fixed
Documentation: membrane proteins search example
Removed
Remove deprecated final.html, stats.html, suggest.html files
[1.8.0] - 2021-06-11
Fixed
Search API accepts both date and date-time formats
Added
RO-474: case-insensitive search by default, "case_sensitive" parameter for case-sensitive searches
Documentation and examples for faceted aggregations
[1.7.20] - 2021-06-07
Fixed
HELP-17071: relax text service validation to use comparison operators with date math expresion
Update documentation
[1.7.19] - 2021-06-02
Added
API Query Editor: format and compact query representation
Fixed
Elasticsearch client version upgrade
Improved suggester requests validation
API Query Editor: refactor suggester and unreleased editors
[1.7.18] - 2021-05-28
Fixed
Update Search API Query Editor look and feel
[1.7.17] - 2021-04-27
Added
HELP-16899: more documentation for sort by various attributes operation
HELP-16904, HELP-16835: documenting complex boolean queries in the basic search
documentation: clarifying asym_id in the instance identifier (\_label_asym_id, not \_auth_asym_id)
HELP-16761: comment on using data API to retrieve data
[1.7.16] - 2021-03-19
Added
Support New stats page: growth of entities accounting for redundancy - RO-2344
Added es.cardinality.precision.threshold in the properties file.
Moved es.alternative.max.num.interval.stats in the properties file.
[1.7.15] - 2021-03-10
Added
Add missing dependencies when running on Java 11 - HELP-16724
[1.7.14] - 2021-03-08
Added
Added two new -exact search options for chemical descriptor matching - HELP-16411
[1.7.13] - 2021-03-05
Fixed
avoid line-breaks in payload logs
support parsing aggregation response produced by terms aggregation on integer typed attribute (e.g. rcsb_cluster_membership.cluster_id)
[1.7.12] - 2021-02-19
Fixed
Strucmotif: Validate at most 4 exchanges per position - RO-2581
Strucmotif: Validate at most 10 residues
[1.7.11] - 2021-02-12
Added
Sequence clusters statistics example
[1.7.10] - 2021-02-09
Added
Note to the tutorial about the Spencer's python package
[1.7.9] - 2021-02-01
Fixed
Query editor: search URL doesn't get updated when search runs - RO-2527
[1.7.8] - 2021-01-28
Added
Add support for chemical substructure search to arches - RO-2509
[1.7.7] - 2021-01-19
Added
Make the query editor as part of the search.rcsb.org tutorial site
[1.7.6] - 2021-01-18
Fixed
stop inverting strucmotif scores
[1.7.5] - 2021-01-14
Fixed
fix "Contact Us" e-mail on API reference page
[1.7.4] - 2020-12-23
Fixed
Fixing bug: added an aggregation rule for filter and nested aggregation share a common ancestor
[1.7.3] - 2020-12-22
Fixed
Fixing bug: duplicated service metadata in the results
Boosting weights according to the scoring strategy
Added
Scoring strategy and search results documentation
Scoring strategy: 'chemical' option
[1.7.2] - 2020-12-11
Fixed
Strucmotif search service to use assembly return_type
Normalization will not be applied to MatchContext of strucmotif searches
[1.7.1] - 2020-12-10
Added
Alive endpoint checks Elasticsearch health - RO-2449
[1.7.0] - 2020-11-16
Added
Strucmotif search service - RO-2349
Fixed
OR/AND merging implementations were inefficient (quadratic). It was causing time outs for large id sets - RO-2462
Now suggest input is trimmed. It was causing some 500s and some artifacts in highlighting - RO-2463
[1.6.7] - 2020-11-06
Fixed
Revised the query request validation of having "pager" and "return_counts" present at the same time.
[1.6.6] - 2020-10-09
Fixed
Now app config file is not read at query time for every query, but only once at app init
[1.6.5] - 2020-10-06
Added
Search API migration guide
[1.6.4] - 2020-10-02
Fixed
Structure service now converts 404 to 204 - RO-59
[1.6.3] - 2020-09-21
Fixed
ID mapping for chemical components
Added
Search API tutorial: combined search example
[1.6.2] - 2020-08-31
Fixed
Unreleased entry query editor
[1.6.1] - 2020-08-27
Added
Search API tutorial: search by UniProt accession example
Fixed
Return 400 Bad Request on missing query parameter instead of 500 Server Error
[1.6.0] - 2020-08-05
Added
Branched entity and entity instance schemas to the global schema
Fixed
Bug in query editor initialization
[1.5.0] - 2020-07-31
Added
Support for more expressive range operator - BACK-443
Documentation improvements: adding description of search operators and date math expressions - BACK-439
[1.4.0] - 2020-07-21
Added
The sequence service match context output now includes the local sequence alignment
[1.3.0] - 2020-07-14
Added
New API request option to return all hits as a result set
[1.2.1] - 2020-07-09
Added
Polymeric PRDs to ID mapping tool
[1.2.0] - 2020-07-06
Added
Chemical search service - BACK-393
Unreleased entries search - BACK-375
Date math expressions in query and aggregation - BACK-418
Make "node_id" optional
[1.1.2] - 2020-06-24
Fixed
Fixed null value exception when combining query results from text service query and other service type query.
[1.1.1] - 2020-06-08
Added
Documentation page listing attributes available for search
[1.1.0] - 2020-05-28
Added
Sequence motif service type - BACK-387
Context match output for sequence, sequence motif and shape - BACK-396
Public tutorial at index.html - BACK-406
Queries can be submitted via POST as well as GET now - BACK-401
Fixed
Validation for missing 'parameters' in services other than text
[1.0.0] - 2020-04-08
First public release.

shell
