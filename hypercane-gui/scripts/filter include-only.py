import os

import hypercane.actions.score
import hypercane.errors

from hypercane.args import universal_gui_required_args, universal_gui_optional_args
from hypercane.args.filter_includeonly import filter_includeonly_parser
from hypercane.version import __useragent__
from hypercane.actions import get_logger, calculate_loglevel
from hypercane.utils import get_hc_cache_storage

if __name__ == '__main__':

    for item in filter_includeonly_parser._subparsers._group_actions:
        for key in item.choices:

            subparser = item.choices[key]

            # Wooey's install script does not know how to handle functions, so we have to repeat this
            required = subparser.add_argument_group('required arguments')

            for entry in universal_gui_required_args:
                flags = entry['flags']
                argument_params = entry['argument_params']
                required.add_argument(*flags, **argument_params)

            optional = subparser.add_argument_group('optional arguments')
            for entry in universal_gui_optional_args:
                flags = entry['flags']
                argument_params = entry['argument_params']
                optional.add_argument(*flags, **argument_params)

    args = filter_includeonly_parser.parse_args()

    # setting expected arguments for GUI
    vars(args)['output_filename'] = "hypercane-filter-output.tsv"
    vars(args)['logfile'] = "hypercane-status.log"
    vars(args)['errorfilename'] = "hypercane-errors.dat"
    vars(args)['cache_storage'] = get_hc_cache_storage()
    vars(args)['input_arguments'] = args.input_file.name
    vars(args)['allow_noncompliant_archives'] = False

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    if args.errorfilename is not None:
        hypercane.errors.errorstore.type = hypercane.errors.FileErrorStore(args.errorfilename)

    print("starting to filter {} in input".format(args.which))
    args.exec(args)
    print("done filtering with {}".format(args.which))
