import os
import sys
import argparse

from hypercane.utils import get_hc_cache_storage

universal_cli_required_args = [
    {   'flags': ['-i' ],
        'argument_params': {
            'required': True,
            'dest': 'input_type',
            'help': "The input type, one of mementos, timemaps, original-resources, archiveit, trove, or pandora-collection.",
            'choices': ['mementos', 'timemaps', 'original-resources', 'archiveit', 'pandora-subject', 'pandora-collection', 'trove']
        }
    },
    {   'flags': [ '-a', '-ia', '--input-arguments'],
        'argument_params': {
            'required': True,
            'dest': 'input_arguments',
            'help': "Either a file containing a list of URIs, or a collection identifier from Archive-It, Pandora, or Trove.",
        }
    },
    {   'flags': [ '-o', '--output-filename'],
        'argument_params': {
            'required': True,
            'dest': 'output_filename',
            'help': "The file to which we write output."
        }
    },
    {
        'flags': [ '--allow-noncompliant-archives' ],
        'argument_params': {
            'required': False,
            'action': 'store_true',
            'help': argparse.SUPPRESS,
            'dest': 'allow_noncompliant_archives'
        }
    }
]

universal_cli_optional_args = [
    {   'flags': ['-l', '--logfile'],
        'argument_params': {
            'required': False,
            'dest': 'logfile',
            'help': "The path to a logging file. The log is printed to screen by default.",
            'default': sys.stdout
        }
    },
    {   'flags': [ '-v', '--verbose' ],
        'argument_params': {
            'required': False,
            'dest': 'verbose',
            'action': 'store_true',
            'help': "This will raise the logging level to debug for more verbose output"
        }
    },
    {   'flags': [ '-q', '--quiet' ],
        'argument_params': {
            'required': False,
            'dest': 'quiet',
            'action': 'store_true',
            'help': "This will lower the logging level to only show warnings or errors"
        }
    },
    {
        'flags': [ '--crawl-depth'],
        'argument_params': {
            'required': False,
            'dest': 'crawl_depth',
            'help': "EXPERIMENTAL -- crawl the web archive to this depth",
            'default': 1,
            'type': int
        }
    },
    {
        'flags': [ '-cs', '--cache-storage' ],
        'argument_params': {
            'required': False,
            'dest': 'cache_storage',
            'help': "The path to the MongoDB database to use as a cache",
            'default': get_hc_cache_storage()
        }
    },
    {
        'flags': [ '-e', '--errorfilename' ],
        'argument_params': {
            'required': False,
            'dest': 'errorfilename',
            'help': "The path to filename that records URL processing failures",
            'default': 'hypercane-errors.dat'
        }
    },
]

universal_gui_required_args = [
    {   'flags': [ '-i', '--input-type' ],
        'argument_params' : {
            'required': True,
            'dest': 'input_type',
            'help': 'The input type, one of mementos, timemaps, or original-resources.',
            'choices': ['mementos', 'timemaps', 'original-resources']
        }    
    },
    {   'flags': [ '-a', '--input-arguments' ],
        'argument_params' : {
            'required': True,
            'dest': 'input_file',
            'help': "A file containing a list of newline separated URIs.",
            'type': argparse.FileType('r')
        }
    }
]

universal_by_cid_gui_required_args = [
    {   'flags': [ '-i', '--input-type' ],
        'argument_params' : {
            'required': True,
            'dest': 'input_type',
            'help': 'The collection type, one of archiveit, pandora-subject, pandora-collection, or trove.',
            'choices': ['archiveit', 'pandora-subject', 'pandora-collection', 'trove']
        }    
    },
    {   'flags': [ '-a', '--input-arguments' ],
        'argument_params' : {
            'required': True,
            'dest': 'collection_id',
            'help': "A collection identifier.",
        }
    }
]

universal_gui_optional_args = [
    {   'flags': [ '-v', '--verbose' ],
        'argument_params': {
            'required': False,
            'dest': 'verbose',
            'action': 'store_true',
            'help': "This will raise the logging level to debug for more verbose output"
        }
    },
    {   'flags': [ '-q', '--quiet' ],
        'argument_params': {
            'required': False,
            'dest': 'quiet',
            'action': 'store_true',
            'help': "This will lower the logging level to only show warnings or errors"
        }
    },
    {
        'flags': [ '--crawl-depth'],
        'argument_params': {
            'required': False,
            'dest': 'crawl_depth',
            'help': "EXPERIMENTAL -- crawl the web archive to this depth",
            'default': 1,
            'type': int
        }
    }
]
