import argparse
import json

from aiu import ArchiveItCollection
from datetime import datetime

from . import get_logger, calculate_loglevel, process_input_args
from .identify import discover_original_resources_by_input_type
from ..utils import get_web_session

def generate_collection_metadata(collection_id, session):

    aic = ArchiveItCollection(collection_id, session=session)

    return aic.return_all_metadata_dict()

def generate_blank_metadata(urirs):

    blank_metadata = {'id': None,
        'exists': None,
        'metadata_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'name': None,
        'uri': None,
        'collected_by': None,
        'collected_by_uri': None,
        'description': None,
        'subject': [],
        'archived_since': None,
        'private': None,
        'optional': {},
        'seed_metadata': {
            'seeds': {}
        },
        'timestamps': {
            'seed_metadata_timestamp': '2020-01-25 16:45:59',
            'seed_report_timestamp': '2020-01-25 16:45:59'
        }
    }

    for urir in urirs:
        blank_metadata['seed_metadata']['seeds'][urir] = {
            'collection_web_pages': [{}],
            'seed_report': {}
        }

    return blank_metadata

def discover_collection_metadata(args):

    parser = argparse.ArgumentParser(
        description="Discover the collection metadata in a web archive collection. Only Archive-It is supported at this time.",
        prog="hc report metadata"
        )

    args = process_input_args(args, parser)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    session = get_web_session(cache_storage=args.cache_storage)

    logger.info("Starting collection metadata discovery run.")

    if args.input_type == 'archiveit':
        metadata = generate_collection_metadata(args.input_arguments, session)
    else:
        logger.warning("Metadata reports are only supported for Archive-It collections, proceeding to create JSON output for URI-Rs.")
        urirs = discover_original_resources_by_input_type(
            args.input_type, args.input_arguments, args.crawl_depth, session)
        metadata = generate_blank_metadata(urirs)

    with open(args.output_filename, 'w') as metadata_file:
        json.dump(metadata, metadata_file, indent=4)

    logger.info("Done with collection metadata discovery run.")

def print_usage():

    print("""'hc report' is used print reports about web archive collections

    Supported commands:
    * metadata - for discovering the metadata associated with seeds, only Archive-It is supported at this time

    Examples:
    
    hc report metadata -i archiveit -ia 8788 -o 8788-metadata.json
    
""")

supported_commands = {
    "metadata": discover_collection_metadata
}

