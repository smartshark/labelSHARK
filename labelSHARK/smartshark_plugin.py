#!/usr/bin/env python

"""Plugin for execution with serverSHARK."""

import argparse
import os
import sys
import logging
import timeit
import copy

from core import LabelSHARK

from mongoengine import *
from pycoshark.mongomodels import VCSSystem, Commit, IssueSystem
from pycoshark.utils import get_code_entity_state_identifier, create_mongodb_uri_string
from pycoshark.utils import get_base_argparser


def remove_index(cls):
    tmp = copy.deepcopy(cls._meta)
    if 'indexes' in tmp.keys():
        del tmp['indexes']
    del tmp['index_specs']
    tmp['index_specs'] = None
    return tmp


VCSSystem._meta = remove_index(VCSSystem)
Commit._meta = remove_index(Commit)
IssueSystem._meta = remove_index(IssueSystem)


# set up logging, we log everything to stdout except for errors which go to stderr
# this is then picked up by serverSHARK
log = logging.getLogger('labelSHARK')
log.setLevel(logging.INFO)
i = logging.StreamHandler(sys.stdout)
e = logging.StreamHandler(sys.stderr)

i.setLevel(logging.INFO)
e.setLevel(logging.ERROR)

log.addHandler(i)
log.addHandler(e)


def main(args):
    # timing
    start = timeit.default_timer()

    uri = create_mongodb_uri_string(args.db_user, args.db_password, args.db_hostname, args.db_port, args.db_authentication, args.ssl)
    connect(args.db_database, host=uri)

    vcs = VCSSystem.objects.get(url=args.url)

    itss = []
    if args.issue_systems == 'all':
        for its in IssueSystem.objects.filter(project_id=vcs.project_id):
            itss.append(its)
    else:
        for url in args.issue_systems.split(','):
            its = IssueSystem.objects.get(url=url)
            itss.append(its)

    log.info("Starting commit labeling")

    # import every approach defined or all
    if args.approaches == 'all':
        # just list every module in the package and import it
        basepath = os.path.dirname(os.path.abspath(__file__))
        for app in os.listdir(os.path.join(basepath, '/approaches/')):
            if app.endswith('.py') and app != '__init__.py':
                __import__('approaches.{}'.format(app[:-3]))
    else:
        # if we have a list of approaches import only those
        for app in args.approaches.split(','):
            __import__('approaches.{}'.format(app))

    # add specific configs
    config = {'itss': itss,
              'args': args}
    a = LabelSHARK()
    a.configure(config)
    for commit in Commit.objects.filter(vcs_system_id=vcs.id):
        labels = a.get_labels(commit)
        log.info('commit: {}, labels: {}'.format(commit.revision_hash, labels))
        # save the labels:
        # commit.labels.upsert(labels)

    end = timeit.default_timer() - start
    log.info("Finished commit labeling in {:.5f}s".format(end))

if __name__ == '__main__':
    # we basically re-use the vcsSHARK argparse config here
    parser = get_base_argparser('Analyze the given URI. An URI should be a checked out GIT Repository.', '1.0.0')
    parser.add_argument('-u', '--url', help='URL of the project (e.g., GIT Url).', required=True)
    parser.add_argument('-is', '--issue_systems', help='Comma separated list of issue_system URLs or all for every ITS for this project.', required=True)
    parser.add_argument('-ap', '--approaches', help='Comma separated list of python module names that implement approaches or all for every approach.', required=True)
    main(parser.parse_args())
