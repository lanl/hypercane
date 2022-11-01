import logging
import traceback
# from distance import hamming
from scipy.spatial.distance import hamming

from ..utils import get_raw_simhash
import hypercane.errors

module_logger = logging.getLogger('hypercane.cluster.dbscan')

def shdist(a, b, **oo):
    return hamming(a, b) / 64

def estimate_epsilon(X, transpose=True):

    # method from https://towardsdatascience.com/machine-learning-clustering-dbscan-determine-the-optimal-value-for-epsilon-eps-python-example-3100091cfbc

    from sklearn.neighbors import NearestNeighbors
    import numpy as np

    neigh = NearestNeighbors(n_neighbors=2)

    if transpose == True:
        nbrs = neigh.fit(X.T)
        distances, indices = nbrs.kneighbors(X.T)
    else:
        nbrs = neigh.fit(X)
        distances, indices = nbrs.kneighbors(X)

    distances = np.sort(distances, axis=0)
    distances = distances[:,1]

    xdata = np.arange(0, len(distances))
    ydata = distances

    slopes = []

    # the article says maximum curvature, which is where the slope is highest
    for i in range(0, len(ydata) - 1):
        slope = ( ydata[i + 1] - ydata[i] ) / (xdata[i + 1] - xdata[i])
        slopes.append(slope)

    return ydata[ slopes.index( max(slopes) ) ]

def cluster_by_simhash_distance(urimdata, cache_storage, simhash_function=get_raw_simhash, min_samples=2, eps=0.3):

    import concurrent.futures
    import numpy as np
    from datetime import datetime
    from sklearn.cluster import DBSCAN
    from ..utils import get_memento_http_metadata

    # learn existing cluster assignments
    urim_to_cluster = {}
    clusters_to_urims = {}
    for urim in urimdata:

        try:
            clusters_to_urims.setdefault( urimdata[urim]['Cluster'], [] ).append(urim)
            urim_to_cluster[urim] = urimdata[urim]['Cluster']
        except KeyError:
            clusters_to_urims.setdefault( None, [] ).append(urim)
            urim_to_cluster[urim] = None

    # compute simhashes
    urim_to_simhash = {}

    # module_logger.info("before clustering by Simhash, cluster assignments are: {}".format(clusters_to_urims))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # module_logger.info("executing threads to acquire simhashes for {} urims".format(len(urim_to_cluster.keys())))

        # TODO: allow user to choose tf-simhash rather than raw simhash
        future_to_urim = { executor.submit(get_raw_simhash, urim, cache_storage): urim for urim in urim_to_cluster.keys() }

        for future in concurrent.futures.as_completed(future_to_urim):
            urim = future_to_urim[future]

            try:
                simhash = future.result()
                module_logger.info("result is {}".format(simhash))
                # simhash is stored as a string in the database, convert to float for clustering
                urim_to_simhash[urim] = float(simhash)

            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}]'.format(urim, repr(exc)))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

    # module_logger.info("urim_to_simhash: {}".format(urim_to_simhash))

    for cluster in clusters_to_urims:

        simhash_list = []

        for urim in clusters_to_urims[cluster]:
            module_logger.info("examining URI-M {}".format(urim))

            try:
                simhash_list.append(urim_to_simhash[urim])
            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}]'.format(urim, repr(exc)))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

        X = np.matrix(simhash_list)

        db = DBSCAN(eps=eps, min_samples=min_samples, metric=shdist).fit(X.T)

        for index, label in enumerate(db.labels_):

            urim = clusters_to_urims[cluster][index]

            if cluster is None:
                urimdata[urim]['Cluster'] = "{}".format(label)
            else:
                 # preserve original cluster assignment
                urimdata[urim]['Cluster'] = "{}~~~{}".format(cluster, label)

    return urimdata

def cluster_by_memento_datetime(urimdata, cache_storage, min_samples=5, eps=0.5):

    import concurrent.futures
    import traceback
    import numpy as np
    from datetime import datetime
    from sklearn.cluster import DBSCAN
    from ..utils import get_memento_http_metadata
    from scipy.stats import zscore


    # Memento-Datetime values are not all Unique, but does it matter?
    # Two URI-Ms with the same Memento-Datetime will be in the same cluster.

    # learn existing cluster assignments
    urim_to_cluster = {}
    clusters_to_urims = {}
    for urim in urimdata:

        try:
            clusters_to_urims.setdefault( urimdata[urim]['Cluster'], [] ).append(urim)
            urim_to_cluster[urim] = urimdata[urim]['Cluster']
        except KeyError:
            clusters_to_urims.setdefault( None, [] ).append(urim)
            urim_to_cluster[urim] = None

    urim_to_mementodatetime = {}

    module_logger.info("preparing to extract memento-datetimes from {} mementos".format(len(urimdata.keys())))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        future_to_urim = { executor.submit(get_memento_http_metadata, urim, cache_storage, metadata_fields=["memento-datetime"]): urim for urim in urim_to_cluster.keys() }

        for future in concurrent.futures.as_completed(future_to_urim):

            urim = future_to_urim[future]

            module_logger.debug("examining result for {}".format(urim))

            try:
                mdt = future.result()[0]
                # mdt = datetime.strptime(mdt, "%a, %d %b %Y %H:%M:%S GMT")
                # urim_to_mementodatetime[urim] = datetime.timestamp(mdt)
                urim_to_mementodatetime[urim] = mdt.timestamp()
                module_logger.debug("assigned timestamp {} to {}".format(urim_to_mementodatetime[urim], urim))
            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}], skipping...'.format(urim, exc))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

    for cluster in clusters_to_urims:

        mdt_list = []

        for urim in clusters_to_urims[cluster]:

            mdt_list.append(urim_to_mementodatetime[urim])

        module_logger.info("mean of data: {}".format(np.mean(mdt_list)))
        module_logger.info("standard deviation of data: {}".format(np.std(mdt_list)))

        X = np.matrix(zscore(mdt_list))

        if eps is None:
            module_logger.info("no epsilon supplied, estimating epsilon")
            eps = estimate_epsilon(X)
            module_logger.info("estimated epsilon value of {}".format(eps))
        else:
            eps = float(eps)
            module_logger.info("using submitted epsilon value of {}".format(eps))

        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X.T)

        for index, label in enumerate(db.labels_):
            urim = clusters_to_urims[cluster][index]

            if cluster is None:
                urimdata[urim]['Cluster'] = "{}".format(label)
            else:
                # preserve original cluster assignment
                urimdata[urim]['Cluster'] = "{}~~~{}".format(cluster, label)

    return urimdata

def cluster_by_tfidf(urimdata, cache_storage, min_samples=2, eps=0.3):

    # thanks to: https://github.com/vishnuprathish/DocumentClustering/blob/master/dbscan.py

    import concurrent.futures
    import numpy as np
    from hypercane.utils import get_boilerplate_free_content
    from sklearn.feature_extraction.text import TfidfVectorizer
    from otmt.timemap_measures import full_tokenize
    from sklearn.cluster import DBSCAN
    from nltk.corpus import stopwords
    import string

    urim_to_cluster = {}
    clusters_to_urims = {}
    urim_to_content = {}

    for urim in urimdata:

        try:
            clusters_to_urims.setdefault( urimdata[urim]['Cluster'], [] ).append(urim)
            urim_to_cluster[urim] = urimdata[urim]['Cluster']
        except KeyError:
            clusters_to_urims.setdefault( None, [] ).append(urim)
            urim_to_cluster[urim] = None

    # corpus = []

    module_logger.info("acquiring boilerplate-free content")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        future_to_urim = { executor.submit(get_boilerplate_free_content, urim, cache_storage): urim for urim in urim_to_cluster.keys() }

        for future in concurrent.futures.as_completed(future_to_urim):

            urim = future_to_urim[future]

            try:
                content = future.result()
                # mdt = datetime.strptime(mdt, "%a, %d %b %Y %H:%M:%S GMT")
                # corpus.append( content )
                urim_to_content[urim] = content
            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}], skipping...'.format(urim, exc))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

    for cluster in clusters_to_urims:

        corpus = []

        for urim in clusters_to_urims[cluster]:
            module_logger.debug("examining URI-M {} from cluster {}".format(urim, cluster))

            try:
                corpus.append(urim_to_content[urim])
            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}]'.format(urim, repr(exc)))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

        stop_words = stopwords.words('english')
        stop_words.extend(string.punctuation)
        stop_words.extend([ "''", "``", "'s" ])

        module_logger.info("creating TF-IDF vectorizer from corpus")
        tfidf_vectorizer = TfidfVectorizer(
            tokenizer = ( lambda d: [w for w in full_tokenize(d) if w not in stop_words ] ),
            stop_words=None)
        tfidf = tfidf_vectorizer.fit_transform(corpus)

        # X = (tfidf * tfidf.T).toarray()
        X = tfidf.toarray()

        module_logger.info("mean of data: {}".format(np.mean(X)))
        module_logger.info("standard deviation of data: {}".format(np.std(X)))
        module_logger.info("max of data: {}".format(np.max(X)))
        module_logger.info("min of data: {}".format(np.min(X)))

        # with open("Xdata", 'w') as f:
        #     import json
        #     json.dump(X.tolist(), f, indent=4)

        if eps is None:
            module_logger.info("no epsilon supplied, estimating epsilon")
            # eps = estimate_epsilon(tfidf)
            eps = estimate_epsilon(X, transpose=False)
            module_logger.info("estimated epsilon value of {}".format(eps))
        else:
            eps = float(eps)
            module_logger.info("using submitted epsilon value of {}".format(eps))

        module_logger.info("setting up DBSCAN clustering on corpus TF-IDF with array of shape {}".format(tfidf.shape))
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)

        module_logger.info("saving cluster assignments for {} unique labels".format(len(np.unique(db.labels_))))

        for index, label in enumerate(db.labels_):

            urim = clusters_to_urims[cluster][index]

            if cluster is None:
                urimdata[urim]['Cluster'] = "{}".format(label)
            else:
                 # preserve original cluster assignment
                urimdata[urim]['Cluster'] = "{}~~~{}".format(cluster, label)

    return urimdata

def cluster_by_lda_vector(urimdata, cache_storage, min_samples=2, eps=0.3):

    # thanks to: https://github.com/vishnuprathish/DocumentClustering/blob/master/dbscan.py

    import concurrent.futures
    import numpy as np
    from hypercane.utils import get_boilerplate_free_content
    from sklearn.feature_extraction.text import TfidfVectorizer
    from otmt.timemap_measures import full_tokenize
    from sklearn.cluster import DBSCAN
    from gensim.models import LdaModel, LsiModel
    from gensim.corpora import Dictionary
    from nltk.tokenize import word_tokenize
    import string
    from nltk.corpus import stopwords

    urim_to_cluster = {}
    clusters_to_urims = {}
    urim_to_content = {}

    for urim in urimdata:

        try:
            clusters_to_urims.setdefault( urimdata[urim]['Cluster'], [] ).append(urim)
            urim_to_cluster[urim] = urimdata[urim]['Cluster']
        except KeyError:
            clusters_to_urims.setdefault( None, [] ).append(urim)
            urim_to_cluster[urim] = None

    # corpus = []

    module_logger.info("acquiring boilerplate-free content")

    stop_words = stopwords.words('english')
    stop_words.extend(string.punctuation)
    stop_words.extend([ "''", "``", "'s" ])

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:

        future_to_urim = { executor.submit(get_boilerplate_free_content, urim, cache_storage): urim for urim in urim_to_cluster.keys() }

        for future in concurrent.futures.as_completed(future_to_urim):

            urim = future_to_urim[future]

            try:
                content = future.result()
                # mdt = datetime.strptime(mdt, "%a, %d %b %Y %H:%M:%S GMT")
                # corpus.append( content )
                urim_to_content[urim] = content
            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}], skipping...'.format(urim, exc))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

    for cluster in clusters_to_urims:

        documents = []
        urimlist = []

        for urim in clusters_to_urims[cluster]:
            module_logger.debug("examining URI-M {} from cluster {}".format(urim, cluster))

            try:
                documents.append(
                    [word.lower() for word in word_tokenize(urim_to_content[urim].decode('utf8')) if word.lower() not in stop_words]
                )
                urimlist.append(urim)
            except Exception as exc:
                module_logger.exception('URI-M [{}] generated an exception: [{}]'.format(urim, repr(exc)))
                hypercane.errors.errorstore.add(urim, traceback.format_exc())

        module_logger.info("creating TF-IDF vectorizer from corpus")

        # from pprint import PrettyPrinter
        # pp = PrettyPrinter(indent=4)
        # pp.pprint(documents)      

        dictionary = Dictionary(documents) #
        corpus = [ dictionary.doc2bow(text) for text in documents]
        mod = LdaModel(corpus, id2word=dictionary, num_topics=10, chunksize=1, iterations=50, passes=10)

        X = []

        topicdata = {}
        topics = []

        for i in range(0, len(documents)):
            doc = documents[i]
            vec_bow = dictionary.doc2bow(doc)
            vec_lda = mod[vec_bow]

            # docscores = []

            for entry in vec_lda:
                topic = entry[0]
                score = entry[1]
                topicdata[ (i, topic) ] = score
                topics.append(topic)

        topics = list(set(topics))

        for i in range(0, len(documents)):

            row = []

            for topic in topics:

                if (i, topic) in topicdata:
                    row.append( topicdata[ (i, topic) ] )
                else:
                    row.append(0)
        
            X.append( row )

        # with open("Xdata", 'w') as f:
        #     import json
        #     json.dump(X.tolist(), f, indent=4)

        # from pprint import PrettyPrinter
        # pp = PrettyPrinter(indent=4)
        # pp.pprint(X)

        X = np.array(X)

        if eps is None:
            module_logger.info("no epsilon supplied, estimating epsilon")
            # eps = estimate_epsilon(tfidf)
            eps = estimate_epsilon(X, transpose=False)
            module_logger.info("estimated epsilon value of {}".format(eps))
        else:
            eps = float(eps)
            module_logger.info("using submitted epsilon value of {}".format(eps))

        module_logger.info("setting up DBSCAN clustering on corpus LDA vector with array of shape {}".format(X.shape))
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)

        module_logger.info("saving cluster assignments for {} unique labels".format(len(np.unique(db.labels_))))

        for index, label in enumerate(db.labels_):

            urim = clusters_to_urims[cluster][index]

            if cluster is None:
                urimdata[urim]['Cluster'] = "{}".format(label)
            else:
                 # preserve original cluster assignment
                urimdata[urim]['Cluster'] = "{}~~~{}".format(cluster, label)

    return urimdata
