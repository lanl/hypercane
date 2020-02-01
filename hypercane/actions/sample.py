import sys

def run_sample_with_dsa1(parser, args):

    from sys import platform
    import errno

    if platform == "win32":
        print("Error: AlNoamany's Algorithm can only be executed via `hc sample` on Linux or macOS. Please see documentation for how to execute it on Windows and submit an issue to our Issue Tracker if you need Windows support.")
        sys.exit(errno.ENOTSUP)

    import argparse
    import subprocess
    import os
    import shlex
    from datetime import datetime
    from hypercane.actions import add_input_args, add_default_args
    from hypercane.actions import get_logger, calculate_loglevel
    from hypercane.utils import get_web_session, save_resource_data
    from hypercane.identify import discover_resource_data_by_input_type, \
        discover_timemaps_by_input_type

    parser = add_input_args(parser)

    parser = add_default_args(parser)

    runtime_string = "{}".format(datetime.now()).replace(' ', 'T')

    parser.add_argument('--working-directory', required=False, 
        help="the directory to which this application should write output",
        default="/tmp/hypercane/working/{}".format(runtime_string),
        dest='sample_count')

    args = parser.parse_args(args)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    logger.info("Executing DSA1 (AlNoamany's) algorithm")

    scriptdir = os.path.dirname(os.path.realpath(__file__))

    subprocess.run(
        [
            "{}/../packaged_algorithms/dsa1.sh".format(scriptdir),
            args.input_type,
            args.input_arguments,
            args.cache_storage,
            args.logfile,
            args.working_directory,
            args.output_filename
        ]
    )

    logger.info("Done executing DSA1 (AlNoamany's) algorithm")

    return args

def sample_with_dsa1(args):

    import argparse

    parser = argparse.ArgumentParser(
        description="Sample URI-Ms from a web archive collection with DSA1 (AlNoamany's) algorithm.",
        prog="hc sample dsa1"
        )

    run_sample_with_dsa1(parser, args)

def sample_with_alnoamany(args):

    import argparse

    parser = argparse.ArgumentParser(
        description="Sample URI-Ms from a web archive collection with DSA1 (AlNoamany's) algorithm.",
        prog="hc sample alnoamany"
        )
    
    run_sample_with_dsa1(parser, args)

def sample_with_true_random_args(args):

    import argparse

    from hypercane.actions import add_input_args, add_default_args

    parser = argparse.ArgumentParser(
        description="Sample random URLs from a web archive collection.",
        prog="hc sample true-random"
        )

    parser = add_input_args(parser)

    parser.add_argument('-k', required=False, help="the number of items to sample", default=28, dest='sample_count')

    parser = add_default_args(parser)

    args = parser.parse_args(args)

    return args

def sample_with_true_random(args):
    
    from hypercane.sample.true_random import select_true_random
    from hypercane.actions import get_logger, calculate_loglevel
    from hypercane.utils import get_web_session, save_resource_data
    from hypercane.identify import discover_resource_data_by_input_type, \
        discover_mementos_by_input_type

    args = sample_with_true_random_args(args)

    logger = get_logger(
        __name__,
        calculate_loglevel(verbose=args.verbose, quiet=args.quiet),
        args.logfile
    )

    session = get_web_session(cache_storage=args.cache_storage)
    output_type = 'mementos'

    logger.info("Starting random sampling of URI-Ms.")

    urimdata = discover_resource_data_by_input_type(
        args.input_type, output_type, args.input_arguments, args.crawl_depth,
        session, discover_mementos_by_input_type
    )

    logger.info("Executing select true random algorithm")
    sampled_urims = select_true_random(list(urimdata.keys()), int(args.sample_count))

    logger.info("Writing sampled URI-Ms out to {}".format(args.output_filename))
    save_resource_data(args.output_filename, urimdata, 'original-resources', sampled_urims)

    logger.info("Done sampling.")

def print_usage():

    print("""hc sample is used execute different algorithms for selecting mementos from a web archive collection, document collection, a list of TimeMaps, or a directory containing WARCs

    Supported commands:
    * true-random - randomly chooses n URI-Ms from the input
    * dsa1 - select URI-Ms using the DSA1 (AlNoamany's) Algorithm
    * alnoamany - alias for dsa1

    Examples:
    
    hc sample true-random -i archiveit=8788 -o seed-output-file.txt -n 10
    
""")

supported_commands = {
    "true-random": sample_with_true_random,
    "dsa1": sample_with_dsa1,
    "alnoamany": sample_with_dsa1
}

