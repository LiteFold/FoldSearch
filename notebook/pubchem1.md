An official website of the United States government

Here is how you know
NIH National Library of Medicine NCBI
PubChem
About
Docs
Submit
Contact
Search PubChem
PubChem
PUG REST Tutorial
(Documentation)

TOP
Search Documents
Submit search
About
News

Citation Guidelines
Publications
Tutorials
Data Organization

Data Sources

Search and Tools

Submissions

Downloads
Programmatic Access

PUG REST
PUG REST Tutorial
PUG View
PUG SOAP
PUG SOAP Reference
Power User Gateway (PUG)
Auto-Complete Search Service
Dynamic Request Throttling
Widgets

RDF

Glossary
Data Specification

Statistics
Archive
Docs
Programmatic Access
PUG REST Tutorial
The purpose of this document is to explain how PubChem’s PUG REST service is structured, with a variety of usage cases as illustrations, to help new users learn how the service works and how to construct the URLs that are the interface to this service. PUG stands for Power User Gateway, which encompasses several variants of methods for programmatic access to PubChem data and services. This REST-style interface is intended to be a simple access route to PubChem for things like scripts, javascript embedded in web pages, and 3rd party applications, without the overhead of XML, SOAP envelopes, etc. that are required for other versions of PUG. PUG REST also provides convenient access to information on PubChem records that is not possible with any other service.

Additional information of PUG REST can also be found in the following papers:

Kim S, Thiessen PA, Cheng T, Yu B, Bolton EE. An update on PUG-REST: RESTful interface for programmatic access to PubChem. Nucleic Acids Res. 2018 July 2; 46(W1):W563-570. doi:10.1093/nar/gky294.
[PubMed PMID: 29718389] [PubMed Central ID: PMC6030920] [Free Full Text]
Kim S, Thiessen PA, Bolton EE, Bryant SH. PUG-SOAP and PUG-REST: web services for programmatic access to chemical information in PubChem. Nucleic Acids Res. 2015 Jul 1; 43(W1):W605-W611. doi: 10.1093/nar/gkv396.
[PubMed PMID: 25934803] [PubMed Central PMCID: PMC4489244] [Free Full Text]
Kim S, Thiessen PA, Bolton EE. Programmatic Retrieval of Small Molecule Information from PubChem Using PUG-REST. In Kutchukian PS, ed. Chemical Biology Informatics and Modeling. Methods in Pharmacology and Toxicology. New York, NY: Humana Press, 2018, pp. 1-24. doi:10.1007/7653_2018_30.
[Full Text]
Some other documents that may be useful are:

A more technical and complete PUG REST specification document, but that is a little harder to read: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
The original purely XML-based PUG: https://pubchem.ncbi.nlm.nih.gov/docs/power-user-gateway
PUG SOAP, for applications that have built-in SOAP handlers, or programming languages with an API generated from a SOAP WSDL: https://pubchem.ncbi.nlm.nih.gov/docs/pug-soap
PUG REST is mainly designed to give small bits of information on one or more PubChem records. Users may also be interested in PUG View (https://pubchem.ncbi.nlm.nih.gov/docs/pug-view), which provides more complete but longer summary reports on individual PubChem records.

PUG REST is actively maintained and updated, so check this page for new features. For comments, help, or to suggest new functionality or topics for this tutorial, please contact pubchem-help@ncbi.nlm.nih.gov.

USAGE POLICY: Please note that PUG REST is not designed for very large volumes (millions) of requests. We ask that any script or application not make more than 5 requests per second, in order to avoid overloading the PubChem servers. To check additional request volume limitations, please read this document on dynamic request throttling. If you have a large data set that you need to compute with, please contact us for help on optimizing your task, as there are likely more efficient ways to approach such bulk queries.

503 HTTP STATUS CODE: Please note that this status code may be returned when the server is temporarily unable to service your request due to maintenance downtime or capacity problems. (Please try again later.) Please also note that an HTML document may be returned.

How PUG REST Works
The fundamental unit upon which PUG REST is built is the PubChem identifier, which comes in three flavors – SID for substances, CID for compounds, and AID for assays. The conceptual framework of this service, that uses these identifiers, is the three-part request: 1) input – that is, what identifiers are we talking about; 2) operation – what to do with those identifiers; and 3) output – what information should be returned. The beauty of this design is that each of these three parts of the request is (mostly) independent, allowing a combinatorial expansion of the things you can do in a single request. Meaning that, for example, any form of input that specifies some group of CIDs can be combined with any operation that deals with CIDs, and any output format that’s relevant to the chosen operation. So instead of a list of separate narrowly defined service requests that are supported, you can combine these building blocks in many ways to create customized requests.

PUG REST Design

For example, this service supports input of chemical structure by SMILES. It supports output of chemical structure as images in PNG format. You can combine these two into a visualization request for a SMILES string – in this case, whether or not that particular chemical is even in the PubChem database at all! And it’s something you can almost type manually into a web browser:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/CCCCBr/PNG

Or, combine input by chemical name with InChI property retrieval, and you have a simple name-to-InChI service in a single request:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/vioxx/property/InChI/TXT

The possibilities are nearly endless, and more importantly, the action of the service is simple to understand from the URL alone, without needing any extra programming, XML parsing, etc. And at the same time, more complex data handling is available for programmers who want rigorous schema-based XML communications, or who want to use JSON data to embed functionality in a web page via JavaScript.

Input: Design of the URL
PUG REST is entirely based on HTTP (or HTTPS) requests, and most of the details of the request are encoded directly in the URL path – which is what makes the service RESTful (informally anyway, as it does not adhere strictly to REST principles, which are beyond the scope of this discussion). Continuing with the last example above, let’s examine the structure of the URL, which is divided into the three main parts of input, operation, and output, in an ordered sequence that will sometimes be referred to in this document as the URL path:

https://pubchem.ncbi.nlm.nih.gov/rest/pug /compound/name/vioxx /property/InChI /TXT
prolog input operation output
Taking each section individually, first we have the prolog – the HTTP address of the service itself, which is common to all PUG REST requests. The next part is the input, which in this case says “I want to look in the PubChem Compound database for records that match the name ‘vioxx’.” Note that there some subtleties here, in that the name must already be present in the PubChem database, and that a name may refer to multiple CIDs. But the underlying principle is that we are specifying a set of CIDs based on a name; at the time of writing, there is only one CID with this name. The next section is the operation, in this case “I want to retrieve the InChI property for this CID.” And finally the output format specification, “I want to get back plain text.”

Some requests may use optional parameters, things after the ‘?’ at the end of the URL path. PUG REST can accept by URL-encoded arguments and/or HTTP POST some types of inputs that cannot be put into a URL path, such as InChI strings, or certain types of SMILES that contain special characters that conflict with URL syntax, or multi-line SDF files. There is a separate section towards the end of this document that explains this process in more detail. There are some additional complexities to the HTTP protocol details that aren’t covered here – see the specification document for more information.

Output: What You Get Back
The results of most operations can be expressed in a variety of data formats, though not all formats are relevant to all operations, meaning for example you can’t get back a list of CIDs in SDF format, or a chemical structure in CSV format. It is your choice which format to use, and will likely depend on the context of the requests; a C++ application may wish to use XML that is automatically parsed into class objects based on the schema, while a JavaScript applet in a web page would more naturally use JSON to have convenient access to the result data. Plain text (TXT) output is limited to certain cases where all output values are of the same simple type, such as a list of chemical name synonyms or SMILES strings. The available output formats are listed below.

Output Format Description
XML standard XML, for which a schema is available
JSON JSON, JavaScript Object Notation
JSONP JSONP, like JSON but wrapped in a callback function
ASNB standard binary ASN.1, NCBI’s native format in many cases
ASNT NCBI’s human-readable text flavor of ASN.1
SDF chemical structure data
CSV comma-separated values, spreadsheet compatible
PNG standard PNG image data
TXT plain text
Error Handling
If there is a problem with a request, PUG REST will usually return some sort of human-readable message indicating what went wrong – whether it’s an invalid input, or nothing was found for the given query, or the request was too broad and took too long to complete (more than 30 seconds, the NCBI standard time limit on web service requests), etc. See the specification document for more detail on result and HTTP status codes.

Special Characters in the URL
Most PUG REST URLs can be written as a simple URL "path" with elements separated by the '/' character. But some inputs, like SMILES (with stereochemistry) and InChI, contain '/' or other special characters that conflict with URL syntax. In these cases, PUG REST can take the input field as a URL-encoded CGI argument value (after the '?' in the URL), using the same argument name that appears in the path. For example, to use the InChI string

InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)

as input, use just /inchi/ in the path part of the URL, and the argument inchi=(URL-encoded-string) as a CGI parameter:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/cids/JSON?inchi=InChI%3D1S%2FC9H8O4%2Fc1-6%2810%2913-8-5-3-2-4-7%288%299%2811%2912%2Fh2-5H%2C1H3%2C%28H%2C11%2C12%29

Access to PubChem Substances and Compounds
This section covers some of the basic methods of accessing PubChem chemical structure information, with many working samples. It is not intended to be a comprehensive document covering all PUG REST features, but rather enough of the common access methods to give a reasonable overview of how the service is designed and what it can do, so that one can quickly begin to use it for custom applications.

Input Methods
The first part of any PUG REST request is the input, which tells the service which records you’re interested in. There are many ways to approach this; the most common are presented here, with examples.

By Identifier
The most straightforward way to tell PUG REST what records you’re interested in is by specifying the SIDs or CIDs directly. This example says “give me the names of substance with SID 10000 in XML format”:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/10000/synonyms/XML

IDs may also be specified in a comma-separated list, here retrieving a CSV table of compound properties:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/1,2,3,4,5/property/MolecularFormula,MolecularWeight,SMILES/CSV

Large lists of IDs that are too long to put in the URL itself may be specified in the POST body, but be aware that if a PUG REST requests takes more than 30 seconds to complete, it will time out, so it’s better to deal with moderately sized lists of identifiers.

By Name
It is often convenient to refer to a chemical by name. Be aware though that matching chemical names to structure is an inexact science at best, and a name may often refer to more than one record. For example, “glucose” gives (at the time of writing) four CIDs, the same as if you were to search for that name by full synonym match in Entrez:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/glucose/cids/TXT

Some operations will use only the first identifier in the list, so if you want a picture of glucose, you can get what PubChem considers the “best” match to that name with the following URL:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/glucose/PNG

By default, the given name must be an exact to match the entire name of the record; optionally, you can specify that matches may be to individual words in the record name:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/myxalamid/cids/XML?name_type=word

By Structure Identity
There are numerous ways to specify a compound by its chemical structure, using SMILES, InChI, InChI key, or SDF. InChI and SDF require the use of POST because the format is incompatible with a simple URL string, so they won’t be discussed here. But specifying with most SMILES strings, or InChI key, is straightforward. For some operations, a SMILES can be used to get data even if the structure is not present in PubChem already, but may not work for others like retrieval of precomputed properties. The InChI key must always be present in the database, since unlike these other formats, it is not possible to determine structure from the key alone. This example will give the PubChem CID for the SMILES string “CCCC” (butane):

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/CCCC/cids/TXT

By Structure Search
The previous section describes how one can specify a structure, for which PUG REST will return only an exact match. There are however more sophisticated structure search techniques available, including substructure and superstructure, similarity (2D Tanimoto), and various partial identity matches (like same atom connectivity but unspecified stereochemistry). Molecular formula search also falls into this category in PUG REST. The complication with these searches is that it takes time to search the entire PubChem database of tens of millions of compounds, and so results may not be available within the previously mentioned 30 second time period of a PUG REST request. To work around this, PUG REST uses what is called an “asynchronous” operation, where you get a request identifier that is a sort of job ticket when you start the search. Then it is the caller’s responsibility to check periodically (say, every 5-10 seconds) whether the search has finished, and if so, retrieve the results. It is a two stage process, where the search is initiated by a request like this search for all records containing a seven-membered carbon ring:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/substructure/smiles/C1CCCCCC1/XML

The result of that request will include what PUG REST calls a “ListKey” – which is currently a unique, private, randomly-assigned 64 bit integer. This key is used in a subsequent request like:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/listkey/12345678910/cids/TXT

… where the listkey number in the above URL is the actual ListKey returned in the first call. This will either give a message to the effect of “your search is still running,” or if complete, will return the list of CIDs found - in this example at this time, around 230,000 records. (See below for more on how to deal with large lists of identifiers.)

By Fast (Synchronous) Structure Search
Some re-engineering of the PubChem search methods has enabled faster searching by identity, similarity (2D and 3D), substructure, and superstructure. These methods are synchronous inputs, meaning there is no waiting/polling necessary, as in the majority of cases they will return results in a single call. (Timeouts are possible if the search is too broad or complex.) These are normal input methods and can be used with any output. Some examples are below:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastidentity/cid/5793/cids/TXT?identity_type=same_connectivity

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsubstructure/cid/2244/cids/XML?StripHydrogen=true

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsimilarity_2d/cid/2244/property/MolecularWeight,MolecularFormula,RotatableBondCount/XML?Threshold=99

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsimilarity_3d/cid/2244/cids/JSON

By Cross-Reference (XRef)
PubChem substances and compounds often include a variety of cross-references to records in other databases. Sometimes it’s useful to do a reverse lookup by cross-reference value, such as this request that returns all SIDs that are linked to a patent identifier:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/xref/PatentID/US20050159403A1/sids/JSON

For a full list of cross-references available, see the specification document.

By Mass
Compounds (CIDs) can be selected by mass value or range. Mass types are "molecular_weight", "exact_mass", and "monoisotopic_mass". Lookup can be by equality to a single value, or within an inclusive range of values. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/molecular_weight/range/400.0/400.05/cids/JSON

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/exact_mass/equals/484.29372238/cids/JSON

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/monoisotopic_mass/range/455.14196/455.14198/cids/JSON

Available Data
Now that you’ve learned how to tell PUG REST what records you want to access, the next stage is to indicate what to do with these records – what information about them you want to retrieve. One of the major design goals of PUG REST is to provide convenient access to small “bits” of information about each record, like individual properties, cross-references, etc., which may not be possible with any other PubChem service without having to download a large quantity of data and sort through it for the one piece you need. That is, PubChem provides many ways to retrieve bulk data covering the entire database, but if all you want is, say, the molecular weight of one compound, PUG REST is the way to get this simply and quickly. (Whereas PUG REST is not the best way to get information for the whole database – so it’s probably not a good idea to write a “crawler” that calls PUG REST individually for every SID or CID in the system – there are better ways to get data for all records.)

Full Records
PUG REST can be used to retrieve entire records, in the usual formats that PubChem supports – ASN.1 (NCBI’s native format), XML, SDF. Now you can even get full records in JSON(P) as well. In fact, full record retrieval is the default action if you don’t specify some other operation. For example, both of these will return the record for aspirin (CID 2244) in various fully equivalent formats:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/SDF

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/record/XML

You can also request multiple records at once, though be aware that there is still the timeout limit on record retrieval so large lists of records may not be practical this way – but of course PubChem provides separate bulk download facilities.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/1,2,3,4,5/SDF

Images
As far as PUG REST is concerned, images are really a flavor of full-record output, as they depict the structure as a whole. So all you have to do to retrieve an image is to specify PNG format output instead of one of the other data formats described in the previous section. Note though that an image request will only show the first SID or CID in the input identifier list, there is currently no way to get multiple images in a single request. (However, PubChem’s download service can be used to get multiple images.) Image retrieval is fully compatible with all the various input methods, so for example you can use this to get an image for a chemical name, SMILES string, InChI key, etc.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/lipitor/PNG

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/CCCCC=O/PNG

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/RZJQGNCSTQAWON-UHFFFAOYSA-N/PNG

Compound Properties
All of the pre-computed properties for PubChem compounds are available through PUG REST, individually or in tables. See the specification document for a table of all the property names. For example, to get just a single molecular weight value:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/MolecularWeight/TXT

Or a CSV table of multiple compounds and properties:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/1,2,3,4,5/property/MolecularWeight,MolecularFormula,HBondDonorCount,HBondAcceptorCount,InChIKey,InChI/CSV

Synonyms
Chemical names can be both input and output in PUG REST. For example, to see all the synonyms of Vioxx that PubChem has, a rather long list:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/vioxx/synonyms/XML

Cross-References (XRefs)
PubChem has many cross-references between databases, all of which are available through PUG REST. See the specification document for a table of all the cross-reference types. For example, to get all the MMDB identifiers for protein structures that contain aspirin:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/xrefs/MMDBID/XML

Or the inverse of an example above, retrieving all the patent identifiers associated with a given SID:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/sid/137349406/xrefs/PatentID/TXT

And More…
This gives you some idea of the sorts of data one can access through PUG REST. It is not a comprehensive list, as we have not covered dates, classifications, BioAssay information and SID/CID/AID cross-links (detailed more below), etc.; more features may be added in the future. And we welcome feedback on new feature suggestions as well!

Access to PubChem BioAssays
In this section we describe the various types of BioAssay information available through PUG REST. A PubChem BioAssay is a fairly complex and sometimes very large entity with a great deal of data, so there are routes both to entire assay records and various component data readouts, etc., so that you can more easily get just the data that you’re interested in.

From AID
Assay Description
An assay is composed of two general parts: the description of the assay as a whole, including authorship, general description, protocol, and definitions of the data readout columns; and then the data section with all the actual test result values. To get just the description section via PUG REST, use a request like:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/504526/description/XML

There is also a simplified summary format that does not have the full complexity of the original description as above, and includes some information on targets, active and inactive SID and CID counts, etc. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/1000/summary/JSON

Assay Data
BioAssay data may be conceptualized as a large table where the columns are the readouts (enumerated in the description section), and the rows are the individual substances tested and their results for each column. So, retrieving an entire assay record involves the primary AID – the identifier for the assay itself – and a list of SIDs. If you want all the data rows of an assay, you can use a simple request like this one, which will return a CSV table of results. Note that full-data retrieval is the default operation for assays.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/504526/CSV

However, as some assays have many thousands of SID rows, there is a limit, currently 10,000, on the number of rows that can be retrieved in a single request. If you are interested in only a subset of the total data rows, you can use an optional argument to the PUG REST request to limit the output to just those SIDs (and note that with XML/ASN output you get the description as well when doing data retrieval). There are other ways to input the SID list, such as in the HTTP POST body or via a list key; see below for more detail on lists stored on the server.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/504526/XML?sid=104169547,109967232

If you are only interested in the concise data (i.e. active concentration readout), you can request it with additional information (i.e. AID, SID, CID, Activity Outcome, Target Accession, Target GeneID, Activity Value [uM], Activity Name, Assay Name, Assay Type, PubMed ID, RNAi):

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/504526/concise/JSON (XML and CSV are valid output formats)

Some assay data may be recast as dose-response curves, in which case you can request a simplified output:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/504526/doseresponse/CSV?sid=104169547,109967232

Targets
When the target of a BioAssay is known, it can be retrieved either as a sequence or gene, including identifiers in NCBI’s respective databases for these:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/490,1000/targets/ProteinGI,ProteinName,GeneID,GeneSymbol/XML

Note though that not all assays have protein or gene targets defined.

It is also possible to select assays via target identifier, specified by GI, Gene ID, or gene symbol, for example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/target/genesymbol/USP2/aids/TXT

Activity Name
BioAssays may be selected by the name of the primary activity column, for example to get all the AIDs that are measuring an EC50:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/activity/EC50/aids/JSON

Access to PubChem Genes
Gene Input Methods
By Gene ID
This is the recommended way to access gene data in PubChem by using the NCBI Gene identifiers. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/1956,13649/summary/JSON

For the sake of performance, some operations (e.g. retrieving bioactivity data) are limited to a single gene only, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/13649/concise/JSON

By Gene Symbol
One can use the official gene symbol to access gene data in PubChem. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/summary/JSON

Note that a gene symbol (case-insensitive) often maps to multiple genes of different organisms. For simplicity, it returns data by default for human genes. One can provide further taxonomy information to indicate the specific organism using NCBI Taxonomy ID, scientific taxonomy name, common taxonomy name, or taxonomy synonym. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/10090/summary/JSON (mouse Egfr gene by NCBI Taxonomy ID 10090)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/Mus%20musculus/summary/JSON (mouse Egfr gene by scientific taxonomy name)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/house%20mouse/summary/JSON (mouse Egfr gene by common taxonomy name)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/mouse/summary/JSON (mouse Egfr gene by taxonomy synonym)

By Gene Synonym
One can also use gene synonym such as alternative or old name to access gene data in PubChem. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/synonym/ERBB1/summary/JSON

Note that one synonym often maps to multiple genes of different organisms. For simplicity, only one gene synonym is allowed as input at a time.

Identifiers from external sources are treated as synonyms. So, the following link returns data for human EGFR in PubChem.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/synonym/HGNC:3236/summary/JSON

It is recommended to prepend IDs with ID source (e.g. Ensembl:ENSG00000146648) to eliminate ambiguity, though the two links below work the same:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/synonym/Ensemble:ENSG00000146648/summary/JSON (with ID source, recommended)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/synonym/ENSG00000146648/summary/JSON (without ID source)

Available Gene Data
Gene Summary
This operation returns a summary of gene: GeneID, Symbol, Name, TaxonomyID, Taxonomy, Description, and a list of Synonyms. Valid output formats are XML, JSON(P), and ASNT/B. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/1956,13649/summary/JSON (by Gene ID)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/summary/XML (by gene symbol, case insensitive and default to human)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/10090/summary/JSON (mouse with NCBI TaxonomyID 9606)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/Rattus%20norvegicus/summary/JSON (mouse with scientific taxonomy name)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/EGFR/Norway%20rat/summary/JSON (mouse with common taxonomy name)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/synonym/EGFR/summary/JSON (by synonym, note that one synonym may map to multiple GeneIDs)

Assays from Gene
This operation returns a list of AIDs tested against a given gene. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/13649/aids/TXT

For the sake of performance, only one gene is allowed as input.

Bioactivities from Gene
This operation returns the concise bioactivity data for a given gene. Valid output formats are XML, JSON(P), ASNT/B, and CSV.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/13649/concise/JSON (limited to one gene at a time)

For some genes with a large amount of data, the operation may be timed out. In such cases, one can first get the list of AIDs tested against the given gene, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/13649/aids/TXT

Then aggregate the concise bioactivity data from each AID, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/66438/concise/JSON

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/69721/concise/JSON

Pathways from Gene
This operation returns a list of pathways in which a given gene is involved. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/13649/pwaccs/TXT

Such pathway accessions can then be used to access PubChem Pathways data.

Access to PubChem Proteins
Protein Input Methods
By Protein Accession
This is the recommended way to access protein data in PubChem by using the NCBI Protein accessions. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P00533,P01422/summary/JSON (single accession or a list of comma-separated accessions)

By Protein Synonym
One can also use protein synonym to access protein data in PubChem. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/synonym/PR:P00533/summary/JSON

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/synonym/ChEMBL:CHEMBL203/summary/JSON

Identifiers from external sources are treated as synonyms. It is recommended to prepend IDs with ID source to eliminate ambiguity.

Available Protein Data
Protein Summary
This operation returns a summary of protein: ProteinAccession, Name, TaxonomyID, Taxonomy, and a list of Synonyms. Valid output formats are XML, JSON(P), and ASNT/B. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P00533,P01422/summary/JSON

Assays from Protein
This operation returns a list of AIDs tested against a given protein. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P00533/aids/TXT (limited to one protein only)

Bioactivities from Protein
This operation returns the concise bioactivity data for a given protein. Valid output formats are XML, JSON(P), ASNT/B, and CSV.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/Q01279/concise/JSON

For some proteins with a large amount of data, the operation may time out. In such cases, one can first get the list of AIDs tested against the given protein, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/Q01279/aids/TXT

Then aggregate the concise bioactivity data from each AID:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/66438/concise/JSON

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/69721/concise/JSON

Pathways from Protein
This operation returns a list of pathways in which a given protein is involved. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P00533/pwaccs/TXT

Such pathway accessions can then be used to access PubChem Pathways data.

Access to PubChem Pathways
Pathway Input Methods
By Pathway Accession
This is the only way to access pathway information in PubChem. The Pathway Accession is in the form of Source:ID (see more information here). For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/pathway/pwacc/Reactome:R-HSA-70171/summary/JSON (single accession)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/pathway/pwacc/Reactome:R-HSA-70171,BioCyc:HUMAN_PWY-4983/summary/JSON (a list of comma-separated accessions)

Available Pathway Data
Pathway Summary
This operation returns a summary of pathway: PathwayAccession, SourceName, SourceID, SourceURL, Name, Type, Category, Description, TaxonomyID, and Taxonomy. Valid output formats are XML, JSON(P), and ASNT/B. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/pathway/pwacc/Reactome:R-HSA-70171,BioCyc:HUMAN_PWY-4983/summary/JSON

Compounds from Pathway
This operation returns a list of compounds involved in a given pathway. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/pathway/pwacc/Reactome:R-HSA-70171/cids/TXT (limited to one pathway only)

Genes from Pathway
This operation returns a list of genes involved in a given pathway. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/pathway/pwacc/Reactome:R-HSA-70171/geneids/TXT (limited to one pathway only)

Proteins from Pathway
This operation returns a list of proteins involved in a given pathway. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/pathway/pwacc/Reactome:R-HSA-70171/accessions/TXT (limited to one pathway only)

Access to PubChem Taxonomies
Taxonomy Input Methods
By Taxonomy ID
This is the recommended way to access taxonomy information by using the NCBI Taxonomy identifiers. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/9606,2697049/summary/JSON (one ID or a list of comma-separated IDs)

By Taxonomy Synonym
One can also use taxonomy synonym such as scientific name and common name to access taxonomy information in PubChem. This is limited to one synonym at a time for simplicity. For example:
https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/synonym/Homo%20sapiens/summary/JSON
https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/synonym/human/summary/JSON

https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/synonym/SARS-COV-2/summary/JSON

Identifiers from external sources are treated as synonyms. It is recommended to prepend IDs with ID source (e.g. ITIS:180092) to eliminate ambiguity. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/synonym/ITIS:180092/summary/JSON

Available Taxonomy Data
Taxonomy Summary
This operation returns a summary of taxonomy: TaxonomyID, ScientificName, CommonName, Rank, RankedLineage, and a list of Synonyms. Valid output formats are XML, JSON(P), and ASNT/B. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/9606,10090,10116/summary/JSON

Assays and Bioactivities
The following operation returns a list of compounds involved in a given taxonomy. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/2697049/aids/TXT

There is no operation available to directly retrieve the bioactivity data associated with a given taxonomy, as often the data volume is huge. However, one can first get the list of AIDs using the above link, and then aggregate the concise bioactivity data from each AID, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/1409578/concise/JSON

Access to PubChem Cell Lines
Cell Line Input Methods
By Cell Line Accession
PubChem is using Cellosaurus and ChEMBL cell line accessions as its identifiers. This is the recommended way to access cell line data in PubChem. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/cellacc/CHEMBL3308376,CVCL_0045/summary/JSON

By Cell Line Synonym
One can also use cell line synonym such as name to access cell line information. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/synonym/HeLa/summary/JSON

Identifiers from external sources are treated as synonyms. It is recommended to prepend IDs with ID source (e.g. MeSH:D006367). For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/synonym/MeSH:D006367/summary/JSON

Available Cell Line Data
Cell Line Summary
This operation returns a summary of cell line: CellAccession, Name, Sex, Category, SourceTissue, SourceTaxonomyID, SourceOrganism, and a list of Synonyms. Valid output formats are XML, JSON(P), and ASNT/B. For example:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/cellacc/CVCL_0030,CVCL_0045/summary/JSON (by Cellosaurus cell line accession)

https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/synonym/HeLa/summary/JSON (by synonym)

Assays and Bioactivities from Cell Line
This operation returns a list of assays tested on a given cell line. Valid output formats are XML, JSON(P), ASNT/B, and TXT.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/synonym/HeLa/aids/TXT

There is no operation available to directly retrieve the bioactivity data associated with a given taxonomy, as often the data volume is huge. However, one can first get the list of AIDs using the above link, and then aggregate the concise bioactivity data from each AID, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/79900/concise/JSON

Dealing with Lists of Identifiers
Storing Lists on the Server
Some PUG REST requests may result in a very long list of identifiers, and it may not be practical to deal with all of them at once. Or you may have a set of identifiers you want to be able to use for several subsequent requests of different types. For this reason, we provide a way to store lists on the server side, and retrieve them in part or whole. The basic idea is that you request a “List Key” for your identifiers – in fact the same sort of key you get from a structure search as mentioned above. But any operation that results in a list of SIDs, CIDs, or AIDs can be stored in a ListKey this way, not just structure search.

Say for example you want to look at all the SIDs tested in a large assay. First make the request to get the SIDs and store them on the server:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/640/sids/XML?list_return=listkey

This will return a ListKey – along with the size of the list, and values needed to retrieve this same list from Entrez’s eUtils services. You can then use that listkey in subsequent request. For example, since assay data retrieval is limited in the number of rows, you could break it up into multiple requests of 1,000 SID rows at a time, like:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/640/CSV?sid=listkey&listkey=12345678910&listkey_start=0&listkey_count=1000

Here, substitute the “listkey” value with the key returned by the initial request above, then “listkey_start” is the zero-based index of the first element of the list to use, and “listkey_count” is how many. Simply repeat the request with increasing values of “listkey_start” in order to loop over the entire assay – either to get the contents of the whole assay, or (with a smaller count value perhaps) to show one page of results at a time in a custom assay data viewer, with pagination controls to move through the whole set of results.

A ListKey can be used in most places that could otherwise take an explicit list of identifiers. So, for example, the same list of SIDs can be used in the context of substance requests, such as this one to get the synonyms associated with the first 10 records on the same list:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/listkey/12345678910/synonyms/XML?&listkey_start=0&listkey_count=10

You can even create lists from identifiers specified in the URL (or in the HTTP POST body):

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/1,2,3,4,5/cids/XML?list_return=listkey

List Sharing between PUG-REST and E-Utilities
E-Utilities are a set of programs that provide programmatic access to data within the Entrez system, which integrates PubChem with other NCBI databases. While appropriate for searching or accessing text and numeric data, E-Utilities are not suitable for handling other types of data specific to PubChem (such as chemical structure queries, and bioactivity data tables). These data are readily accessible through PubChem-specific programmatic access routes such as PUG, PUG-SOAP, and PUG-REST. Therefore, E-Utilities and PubChem-specific programmatic access routes complement each other. As a result, to get desired data from PubChem programmatically, one may need to use the result from a PUG-REST request as an input to a subsequent E-Utilities request, or vice versa.

This can be done using the PubChem List Gateway, available at the URL:

https://pubchem.ncbi.nlm.nih.gov/list_gateway/list_gateway.cgi

It is a common gateway interface (CGI) that converts between the list key from a PUG-REST request and the Entrez history from an E-Utilities request.

An Entrez history is specified using three parameters: database (DB), Query Key, and WebEnv. The list gateway takes these three parameters for an Entrez history, and returns a list key, which can be used in a subsequent PUG-REST request. As an example, the following URL shows how to convert from a Entrez history to a PUG-REST list key:

https://pubchem.ncbi.nlm.nih.gov/list_gateway/list_gateway.cgi?action=entrez_to_pug&entrez_db=DB&entrez_query_key=QUERYKEY&entrez_webenv=WEBENV

where QUERYKEY and WEBENV are the Query Key and WebEnv values for an Entrez history, respectively, and DB is the name of the PubChem database in Entrez (“pccompound” for Compound, “pcsubstance” for Substance, and “pcassay” for BioAssay). The returned list key can be used in a PUG-REST request, as described in the Storing Lists on the Server section above.

Conversely, the list key from a PUG-REST request can be converted into the three parameters (DB, Query Key, and WebEnv) that specifies an Entrez history, via the following URL:

https://pubchem.ncbi.nlm.nih.gov/list_gateway/list_gateway.cgi?action=pug_to_entrez&pug_listkey=LISTKEY

where LISTKEY is a PUG-REST list key. The returned Entrez history (specified by DB, Query Key, WebEnv) can be used in an E-Utilities request (e.g., ESearch, ESummary, EFetch, or ELink).

Inter-conversion of Identifiers
PubChem has many (many) types of cross-links between databases, or between one records and other records in the same database. That is, you can move from “SID space” to “CID space” in a variety of ways, depending on just what relationship you’re interested in. The specification document has a complete table of these identifier inter-conversion options, depending on whether you’re starting from SIDs, CIDs, or AIDs. We’ll show a few examples here.

You’ve already seen one example just above of getting back SIDs associated with a given AID. That request returns all SIDs, but it’s also possible to get just the SIDs that are active in the assay, in this case a much smaller list than the full set of ~96,000 SIDs that were tested:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/640/sids/TXT?sids_type=active

Or to retrieve all the substances corresponding exactly to the structure of aspirin (CID 2244), which shows all the records of this chemical structure supplied to PubChem by multiple depositors – and there are many in this case. This sort of conversion operation can also be combined with ListKey storage in the same way discussed above, in case the results list is long.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/sids/XML?sids_type=standardized&list_return=listkey

There are operations to retrieve the various groups of related chemical structures that PubChem computes, such as this request to retrieve all compounds – salts, mixtures, etc. – whose parent compound is aspirin; that is, where aspirin is considered to be the “important” part of the structure:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/cids/TXT?cids_type=same_parent

Sometimes it’s possible to group lists of identifiers in the result according to identifiers in the input, and PUG REST includes options for that as well. Compare the output of the following two requests. The first simply returns one group of all standardized SIDs corresponding to any compound with the name ‘glucose’ (that is, deposited records that match one of the glucose CIDs exactly). The second groups them by CID, which is actually the default for this sort of request, unless you are storing the list on the server via ListKey, in which case it is necessarily flattened.

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/glucose/sids/XML?sids_type=standardized&list_return=flat

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/glucose/sids/XML?sids_type=standardized&list_return=grouped

How To Use HTTP POST
While being able to write most PUG REST requests as simple URLs is convenient, sometimes there are inputs that do not work well with this approach because of syntax conflicts or size restrictions. For example, a multi-line SDF file, any name or SMILES string or InChI that has ‘/’ (forward slash) or other special characters that are reserved in URL syntax, or long lists of identifiers that are too big to put directly in the URL of an HTTP GET request, can be put in the HTTP POST body instead. Many (though not necessarily all) of the PUG REST input types allow the argument to be specified by POST. While this isn’t something that one can type into a regular web client, most programmatic HTTP interface libraries will have the ability to use POST. Technically, there is no limit to the size of the POST body, but practically, a very large input may take a long time for PUG REST to process, leading to timeouts if it takes longer than 30 seconds.

There are existing standards for just how the information in the POST body is formatted, and you must include in the PUG REST call an HTTP header that indicates which content type you are supplying. The simpler format is “Content-Type: application/x-www-form-urlencoded” which is the same as the URL argument syntax after the ‘?’ separator, of the general form “arg1=value1&arg2=value2&…” (See here for more technical detail on these content types.) For example, use a URL like

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/cids/JSON

with “Content-Type: application/x-www-form-urlencoded” in the request header, and put the string

inchi=InChI=1S/C3H8/c1-3-2/h3H2,1-2H3

in the POST body. (With InChI this looks a little weird, because the first “inchi=” is the name of the PUG REST argument, and the second “InChI=” is part of the InChI string itself.) You should get back CID 6334 (propane). Note that some special characters may still need to be escaped, in particular the ‘+’ (plus sign) character which is a standard replacement for a space character in URL syntax. You must replace this with “%2B”, such as “smiles=CC(=O)OC(CC(=O)[O-])C[N%2B](C)(C)C” to use the SMILES string for CID 1 (acetylcarnitine). If PUG REST is giving you a “bad request” or “structure cannot be standardized” error message with your input, it’s possible there are other special characters that need to be escaped this way.

The first method just described above works well for single-line input strings, but is not applicable to inputs like SDF which are necessarily multi-lined. For this type, you’ll need to use the multipart/form-data type, and an appropriately formatted input. This method is a little more complex because of the existing protocol standard. To use the same example as above, first prepare a file (or string) that looks like this:

--AaB03x

Content-Disposition: form-data; name="inchi"

Content-Type: text/plain

InChI=1S/C3H8/c1-3-2/h3H2,1-2H3

--AaB03x--

Note that the POST body string/file in this case must have DOS-style “CR+LF” line endings, and there must be an empty line between the content headers and actual data line(s) (and no blank lines anywhere else). But in this format, no further escaping of special characters is needed. It looks a little strange, but your HTTP library may know how to construct this sort of thing automatically, check your documentation. This would be sent to the same URL as before, e.g.:

https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/cids/JSON

but this time with “Content-Type: multipart/form-data; boundary=AaB03x” in the request header. It is essential that the arbitrary boundary string given in the header match what’s used in the POST body (“AaB03x” in this example).

Conclusion
If you’ve read this far, hopefully by now you have a good understanding of the sorts of things PUG REST can do to facilitate access to PubChem data, and how to write your own PUG REST requests. Please feel free to contact us at pubchem-help@ncbi.nlm.nih.gov for assistance, if there’s something you’d like to be able to do with this service but can’t quite figure out how to formulate the requests, or if the features you need simply aren’t present and you would like us to consider adding them.

ON THIS PAGE
How PUG REST Works
Input: Design of the URL
Output: What You Get Back
Error Handling
Special Characters in the URL
Access to PubChem Substances and Compounds
Input Methods
By Identifier
By Name
By Structure Identity
By Structure Search
By Fast (Synchronous) Structure Search
By Cross-Reference (XRef)
By Mass
Available Data
Full Records
Images
Compound Properties
Synonyms
Cross-References (XRefs)
And More…
Access to PubChem BioAssays
From AID
Assay Description
Assay Data
Targets
Activity Name
Access to PubChem Genes
Gene Input Methods
By Gene ID
By Gene Symbol
By Gene Synonym
Available Gene Data
Gene Summary
Assays from Gene
Bioactivities from Gene
Pathways from Gene
Access to PubChem Proteins
Protein Input Methods
By Protein Accession
By Protein Synonym
Available Protein Data
Protein Summary
Assays from Protein
Bioactivities from Protein
Pathways from Protein
Access to PubChem Pathways
Pathway Input Methods
By Pathway Accession
Available Pathway Data
Pathway Summary
Compounds from Pathway
Genes from Pathway
Proteins from Pathway
Access to PubChem Taxonomies
Taxonomy Input Methods
By Taxonomy ID
By Taxonomy Synonym
Available Taxonomy Data
Taxonomy Summary
Assays and Bioactivities
Access to PubChem Cell Lines
Cell Line Input Methods
By Cell Line Accession
By Cell Line Synonym
Available Cell Line Data
Cell Line Summary
Assays and Bioactivities from Cell Line
Dealing with Lists of Identifiers
Storing Lists on the Server
List Sharing between PUG-REST and E-Utilities
Inter-conversion of Identifiers
How To Use HTTP POST
Conclusion
PubChem on X
PubChem on Facebook
PubChem Help
Connect with NLM
Twitter
Facebook
YouTube
National Library of Medicine
8600 Rockville Pike, Bethesda, MD 20894
Web Policies
FOIA
HHS Vulnerability Disclosure
Help
Accessibility
Careers
NLM
NIH
HHS
USA.gov
