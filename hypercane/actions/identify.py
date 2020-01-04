import sys
import os
import argparse
import json

from urllib.parse import urlparse
from scrapy.crawler import CrawlerProcess

from ..identify import list_seed_uris, generate_archiveit_urits, download_urits_and_extract_urims, list_seed_mementos, generate_collection_metadata
from ..identify.archivecrawl import crawl_mementos, StorageObject
from ..version import __useragent__
from . import get_logger, calculate_loglevel, get_web_session, add_default_args, process_collection_input_types

def process_input_args(args, parser):

    parser.add_argument('-i', help="the input type and identifier, only archiveit and a collection ID is supported at this time, example: -i archiveit=8788", dest='input_type', required=True, type=process_collection_input_types)

    parser.add_argument('-o', required=True, help="the file to which we write output", dest='output_filename')

    parser.add_argument('--crawl-depth', '--depth', required=False, help="the number of levels to use in the crawl", dest='crawl_depth', default=1, type=int)

    parser = add_default_args(parser)

    args = parser.parse_args(args)

    return args

def extract_uris_from_input(input_string):

    uri_list = input_string.split(',')
    uri_output_list = []
    
    for uri in uri_list:
        o = urlparse(uri)
        if o.scheme == 'http' or o.scheme == 'https':
            uri_output_list.append(uri)
        elif o.scheme == 'file':
            with open(o.path) as f:
                for line in f.read():
                    line = line.strip()
                    uri_output_list.append(line)
        else:
            # assume it is a filename
            with open(uri) as f:
                for line in f.read():
                    line = line.strip()
                    uri_output_list.append(line)

    return uri_output_list

def discover_timemaps(args):

    parser = argparse.ArgumentParser(
        description="Discover the timemaps in a web archive collection.",
        prog="hc identify timemaps"
        )
    
    args = process_input_args(args, parser)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    session = get_web_session(cachefile=args.cachefile)

    logger.info("Starting timemap discovery run.")

    collection_type = args.input_type[0]
    logger.info("Collection type: {}".format(collection_type))
    urits = []

    if collection_type == "archiveit":
        collection_id = args.input_type[1]
        logger.info("Collection identifier: {}".format(collection_id))
        seeds = list_seed_uris(collection_id, session)
        urits = generate_archiveit_urits(collection_id, seeds)

        if args.crawl_depth > 1:
            urims = download_urits_and_extract_urims(urits, session)
            link_storage = StorageObject()
            crawl_mementos(link_storage, urims, args.crawl_depth)

            for item in link_storage.storage:
                urits.append(item[0])

    elif collection_type == "timemaps":
        urits = extract_uris_from_input(args.input_type[1])
    elif collection_type == "mementos":
        urims = extract_uris_from_input(args.input_type[1])
        link_storage = StorageObject()
        crawl_mementos(link_storage, urims, args.crawl_depth)

        for item in link_storage.storage:
            urits.append(item[0])
        
    elif collection_type == "original-resources":
        # TODO: implement this with a user-specified aggregator so they can create their own collections
        raise NotImplementedError("Extracting TimeMaps from Original Resources is not implemented at this time")
    elif collection_type == "warcs":
        raise NotImplementedError("Extracting TimeMaps from WARCs is not implemented at this time")

    with open(args.output_filename, 'w') as output:
        for urit in urits:
            output.write("{}\n".format(urit))

    logger.info("Done with timemap discovery run.")

def discover_original_resources(args):

    parser = argparse.ArgumentParser(
        description="Discover the original resources in a web archive collection.",
        prog="hc identify original-resources"
        )
    
    args = process_input_args(args, parser)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    session = get_web_session(cachefile=args.cachefile)

    logger.info("Starting original resource discovery run.")

    collection_type = args.input_type[0]
    urirs = []

    if collection_type == "archiveit":
        collection_id = args.input_type[1]
        logger.info("Collection type: {}".format(collection_type))
        logger.info("Collection identifier: {}".format(collection_id))
        seeds = list_seed_uris(collection_id, session)
        urits = generate_archiveit_urits(collection_id, seeds)
        urims = download_urits_and_extract_urims(urits, session)
        link_storage = StorageObject()
        crawl_mementos(link_storage, urims, args.crawl_depth)

        for item in link_storage.storage:
            urirs.append(item[1])

    elif collection_type == "timemaps":
        urits = extract_uris_from_input(args.input_type[1])
        urims = download_urits_and_extract_urims(urits, session)
        link_storage = StorageObject()
        crawl_mementos(link_storage, urims, args.crawl_depth)

        for item in link_storage.storage:
            urirs.append(item[1])

    elif collection_type == "mementos":
        urims = extract_uris_from_input(args.input_type[1])
        link_storage = StorageObject()
        crawl_mementos(link_storage, urims, args.crawl_depth)

        for item in link_storage.storage:
            urirs.append(item[1])
        
    elif collection_type == "original-resources":
        # identity
        urirs = extract_uris_from_input(args.input_type[1])

    elif collection_type == "warcs":
        # TODO: extract from WARC-Target-URI
        raise NotImplementedError("Extracting Original Resources from WARCs is not implemented at this time")

    with open(args.output_filename, 'w') as output:
        for urir in urirs:
            output.write("{}\n".format(urir))

    logger.info("Done with original resource discovery run.")

def discover_mementos(args):

    parser = argparse.ArgumentParser(
        description="Discover the mementos in a web archive collection.",
        prog="hc identify mementos"
        )
    
    args = process_input_args(args, parser)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    session = get_web_session(cachefile=args.cachefile)

    logger.info("Starting memento discovery run.")

    collection_type = args.input_type[0]
    output_urims = []

    if collection_type == "archiveit":
        collection_id = args.input_type[1]
        seeds = list_seed_uris(collection_id, session)
        urits = generate_archiveit_urits(collection_id, seeds)

        if args.crawl_depth > 1:
            urims = download_urits_and_extract_urims(urits, session)
            link_storage = StorageObject()
            crawl_mementos(link_storage, urims, args.crawl_depth)

            for item in link_storage.storage:
                urits.append(item[0])

            urits = list(set(urits)) # in case of overlap
        
        output_urims = download_urits_and_extract_urims(urits, session)

    elif collection_type == "timemaps":
        urits = extract_uris_from_input(args.input_type[1])
        
        if args.crawl_depth > 1:
            urims = download_urits_and_extract_urims(urits, session)
            link_storage = StorageObject()
            crawl_mementos(link_storage, urims, args.crawl_depth)

            for item in link_storage.storage:
                urits.append(item[0])

            urits = list(set(urits)) # in case of overlap

        output_urims = download_urits_and_extract_urims(urits, session)

    elif collection_type == "mementos":
        # identity
        output_urims = extract_uris_from_input(args.input_type[1])

    elif collection_type == "original-resources":
        # TODO: implement this with a user-specified aggregator so they can create their own collections
        raise NotImplementedError("Extracting Mementos from Original Resources is not implemented at this time")

    elif collection_type == "warcs":
        # TODO: implement this with an option to provide a URI prefix with which to construct URI-Ms
        raise NotImplementedError("Extracting Mementos from WARCs is not implemented at this time")

    with open(args.output_filename, 'w') as output:
        for urim in output_urims:
            output.write("{}\n".format(urim))

    logger.info("Done with memento discovery run.")

# def process_discover_collection_metadata_args(args):

#     parser = argparse.ArgumentParser(
#         description="Discover the collection metadata in a web archive collection. Only Archive-It is supported at this time.",
#         prog="hc identify timemaps"
#         )

#     parser.add_argument('-i', help="the input type and identifier, only archiveit and a collection ID is supported at this time, example: -i archiveit=8788", dest='input_type', required=True, type=process_collection_input_types)

#     parser.add_argument('-o', required=True, help="the file to which we write output", dest='output_filename')

#     parser = add_default_args(parser)

#     args = parser.parse_args(args)

#     return args  

# def discover_collection_metadata(args):
    
#     args = process_discover_collection_metadata_args(args)

#     logger = get_logger(
#         __name__,
#         calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
#         args.logfile
#     )

#     session = get_web_session(cachefile=args.cachefile)

#     logger.info("Starting collection metadata discovery run.")

#     collection_type = args.input_type[0]
#     collection_id = args.input_type[1]

#     logger.info("Collection type: {}".format(collection_type))
#     logger.info("Collection identifier: {}".format(collection_id))

#     metadata = generate_collection_metadata(collection_id, session)

#     with open(args.output_filename, 'w') as metadata_file:
#         json.dump(metadata, metadata_file, indent=4)

#     logger.info("Done with collection metadata discovery run.")

def print_usage():

    print("""'hc identify' is used discover resource identifiers in a web archive collection, document collection, a list of TimeMaps, or a directory containing WARCs

    Supported commands:
    * timemaps - for discovering the TimeMap URI-Ts from a web archive collection
    * mementos - for discovering the memento URI-Ms in a web archive collection
    * original-resources - for discovering the original resource URI-Rs in a web archive collection, list of TimeMap URI-Ts, or a directory containing WARCs

    Examples:
    
    hc identify original-resources -i archiveit=8788 -o seed-output-file.txt

    hc identify timemaps -i archiveit=8788 -o timemap-output-file.txt

    hc identify mementos -i timemaps=http://archive.example.net/timemap/link/http://example.com,http://archive2.example.net/timemap/json/http://example3.com -o timemap-output-file.txt
    
""")

supported_commands = {
    "timemaps": discover_timemaps,
    "mementos": discover_mementos,
    "original-resources": discover_original_resources
}

