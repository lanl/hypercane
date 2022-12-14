import logging
import pprint

from mementoembed.mementoresource import NotAMementoError

pp = pprint.PrettyPrinter(indent=4)

module_logger = logging.getLogger('hypercane.report.imagedata')

def get_managed_session(cache_storage):
    # TODO: replace calls from this with get_web_session after 
    # verifying that they both do the same thing now

    import os
    from urllib.parse import urlparse
    from pymongo import MongoClient
    from requests import Session
    from requests_cache import CachedSession
    from requests_cache.backends import MongoCache
    from mementoembed.sessions import ManagedSession
    from hypercane.version import __useragent__
    from urllib3.util.retry import Retry
    # from mementoembed.version import __useragent__
    from requests.adapters import HTTPAdapter

    proxies = None

    http_proxy = os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('HTTPS_PROXY')

    if http_proxy is not None and https_proxy is not None:
        proxies = {
            'http': http_proxy,
            'https': https_proxy
        }

    o = urlparse(cache_storage)
    if o.scheme == "mongodb":
        # these requests-cache internals gymnastics are necessary
        # because it will not create a database with the desired name otherwise
        dbname = o.path.replace('/', '')
        dbconn = MongoClient(cache_storage)
        session = ManagedSession(backend='mongodb')
        session.cache = MongoCache(connection=dbconn, db_name=dbname)
        session.proxies = proxies
        session.headers.update({'User-Agent': __useragent__})

        retry = Retry(
            total=10,
            read=10,
            connect=10,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        session.proxies = proxies
        session.headers.update({'User-Agent': __useragent__})

        return session
    else:
        raise RuntimeError("Caching is required for image analysis.")

def generate_image_data(urimdata, cache_storage):

    from mementoembed.imageselection import generate_images_and_scores, scores_for_image
    from mementoembed.mementoresource import memento_resource_factory

    managed_session = get_managed_session(cache_storage)

    imagedata = {}

    module_logger.info("generating image data with MementoEmbed libraries...")

    for urim in urimdata:

        try:
            try:
                # TODO: cache this information?
                mr = memento_resource_factory(urim, managed_session)
                imagedata[urim] = generate_images_and_scores(mr.im_urim, managed_session)
            except NotAMementoError:
                # TODO: this is dangerous, how do we protect the system from users who submit URI-Rs by accident?
                module_logger.warning("URI-M {} does not appear to come from a Memento-Compliant archive, resorting to heuristics which may be inaccurate...".format(urim))
                imagedata[urim] = generate_images_and_scores(urim, managed_session)

        except Exception:
            module_logger.exception("failed to produce an image report, skipping {} ...".format(urim))
            continue

    return imagedata

def output_image_data_as_jsonl(uridata, output_filename, cache_storage):

    from mementoembed.imageselection import generate_images_and_scores, scores_for_image
    from mementoembed.mementoresource import memento_resource_factory
    import jsonlines

    managed_session = get_managed_session(cache_storage)
    module_logger.info("generating image data with MementoEmbed libraries...")

    with jsonlines.open(output_filename, mode='w') as writer:

        for urim in uridata:
            # TODO: cache this information?

            try:
                try:
                    mr = memento_resource_factory(urim, managed_session)
                    imagedata = { "uri": urim, "imagedata": generate_images_and_scores(mr.im_urim, managed_session) }
                except NotAMementoError:
                    # TODO: this is dangerous, how do we protect the system from users who submit URI-Rs by accident?
                    module_logger.warning("URI-M {} does not appear to come from a Memento-Compliant archive, resorting to heuristics which may be inaccurate...".format(urim))
                    imagedata = { "uri": urim, "imagedata": generate_images_and_scores(urim, managed_session) }

            except Exception:
                module_logger.exception("failed to produce an image report for {}".format(urim))
                continue

            # pylint: disable=no-member
            writer.write(imagedata)

    return imagedata

def rank_images(imagedata):

    imageranking = []

    for urim in imagedata:
        module_logger.info("processing images for URI-M {}".format(urim))
        for image_urim in imagedata[urim]:

            module_logger.info("processing image at {}".format(image_urim))

            module_logger.debug("image data: {}".format(imagedata[urim][image_urim]))

            if imagedata[urim][image_urim] is None:
                module_logger.warning("no data found for image at {} -- skipping...".format(image_urim))
                continue

            if 'colorcount' in imagedata[urim][image_urim]:

                pixelsize = float(imagedata[urim][image_urim]['size in pixels'])
                colorcount = float(imagedata[urim][image_urim]['colorcount'])
                ratio = float(imagedata[urim][image_urim]['ratio width/height'])
                score = float(imagedata[urim][image_urim]['calculated score'])

                if 'metadata' in imagedata[urim][image_urim]['source']:
                    in_metadata = 1
                else:
                    in_metadata = 0

                N = imagedata[urim][image_urim]['N']
                n = imagedata[urim][image_urim]['n']

                if N == 0:
                    noverN = 0
                else:
                    noverN = n / N

                module_logger.debug("report for image {}:\n  colorcount: {}\n  ratio width/height: {}\n  n/N: {}\n".format(
                    image_urim, colorcount, ratio, noverN
                ))

                too_similar = False
                for entry in imageranking:
                    if entry[0] == colorcount:
                        if entry[1] == 1 / ratio:
                            if entry[2] == noverN:
                                too_similar = True

                if too_similar is False:

                    imageranking.append(
                        (
                            in_metadata,
                            score,
                            pixelsize,
                            colorcount,
                            1 / ratio,
                            noverN,
                            image_urim
                        )
                    )

    return sorted(imageranking, reverse=True)
