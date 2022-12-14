import logging

module_logger = logging.getLogger('hypercane.hfilter.highest_rank_per_cluster')

def return_highest_ranking_memento_per_cluster(urimdata, rankkey):

    cluster_assignments = {}
    highest_rank_per_cluster = []

    for urim in urimdata:
        cluster = urimdata[urim]['Cluster']
        cluster_assignments.setdefault(cluster, []).append(urim)

    module_logger.debug("cluster_assignments: {}".format(cluster_assignments))
    module_logger.debug("urimdata: {}".format(urimdata))
    module_logger.info("Applying score key {} to finding highest scoring memento per cluster for {} URI-Ms".format(
        rankkey, len(urimdata)
    ))

    for cluster in cluster_assignments:

        cluster_ranks = []

        for urim in cluster_assignments[cluster]:
            module_logger.info("examining URI-M {} with record {}".format(urim, urimdata[urim]))
            cluster_ranks.append( (urimdata[urim][rankkey], urim) )

        highest_rank_per_cluster.append( max(cluster_ranks)[1] )

    return highest_rank_per_cluster
