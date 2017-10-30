#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import copy

from pycoshark.mongomodels import Issue, Event

from core import LabelSHARK, BaseLabelApproach


def remove_index(cls):
    tmp = copy.deepcopy(cls._meta)
    if 'indexes' in tmp.keys():
        del tmp['indexes']
    del tmp['index_specs']
    tmp['index_specs'] = None
    return tmp


Issue._meta = remove_index(Issue)
Event._meta = remove_index(Event)


@LabelSHARK.approach
class AdjustedSZZ(BaseLabelApproach):
    """This is basically SZZ [1] but not only for bugzilla and with regular expressions instead
    of flex.

    1: When Do Changes Induce Fixes? Jacek Śliwerski et al. 2005
    """

    def configure(self, config):
        self._config = config
        self._log = logging.getLogger(self.__class__.__name__)

        self._issue_links = []
        self._labels = []

        # precompile regex
        self._direct_link_jira = re.compile('(\s|^)(?P<ID>[A-Z][A-Z0-9_]+-[0-9]+)', re.M)
        self._direct_link_bz = re.compile('(bug|issue|bugzilla)[s]{0,1}[#\s]*(?P<ID>[0-9]+)', re.I | re.M)
        self._direct_link_gh = re.compile('(bug|issue)[s]{0,1}[#\s]*(?P<ID>[0-9]+)', re.I | re.M)
        self._keyword = re.compile('(\s|^)fix(e[ds])?|(\s|^)bugs?|defects?|patch', re.I | re.M)

    def set_commit(self, commit):
        self._issue_links = []
        self._labels = []

        gscore = 0
        direct_links = []
        issue_found = False

        for its in self._config['itss']:
            if 'jira' in its.url:
                score, issues, issue_found = self._jira_label(its, commit.message)
            elif 'bugzilla' in its.url:
                score, issues, issue_found = self._bz_label(its, commit.message)
            elif 'github' in its.url:
                score, issues, issue_found = self._gh_label(its, commit.message)

            direct_links.append((score, issues, issue_found))

            for r in issues:
                self._issue_links.append(r.id)

        # no direct link in any linked ITS, fall back to keyword (only if we really did not find any issue, if we found a link that is a feature we skip this otherwise we would have a lot of false positives)
        for score, links, issue_found in direct_links:
            if issue_found:
                gscore = score
                break
        else:
            gscore = self._keyword_label(commit.message)

        labelname = 'bugfix'
        if gscore > 0:
            self._labels.append((labelname, True))
        else:
            self._labels.append((labelname, False))

    def get_labels(self):
        return self._labels

    def get_issue_links(self):
        return self._issue_links

    def _keyword_label(self, message):
        score = 0
        for m in self._keyword.finditer(message):
            if m is not None:
                score += 1
        return score

    def _gh_label(self, issue_system, message):
        """We can only be sure about the status, which is either open or closed. Labels are custom per project. Type is not required."""
        score = 0
        ret = []
        issue_found = False
        for m in self._direct_link_gh.finditer(message):
            try:
                i = Issue.objects.get(issue_system_id=issue_system.id, external_id=m.group('ID').upper())
                issue_found = True
                if i.status in ['closed']:
                    score += 1
                    ret.append(i)

            except Issue.DoesNotExist:
                self._error('issue: {} does not exist'.format(m.group('ID')))
                pass
        return score, ret, issue_found

    def _bz_label(self, issue_system, message):
        score = 0
        ret = []
        issue_found = False
        for m in self._direct_link_bz.finditer(message):
            resolved = False
            fixed = False
            try:
                i = Issue.objects.get(issue_system_id=issue_system.id, external_id=m.group('ID').upper())
                issue_found = True

                if not i.issue_type:
                    # self._log.error("could not find issue type for issue: {}".format(m.group(1)))
                    self._error('could not find issue type for issue: {}'.format(m.group('ID')))
                if i.issue_type and i.issue_type.lower() == 'bug':
                    if i.status in ['resolved', 'closed']:
                        resolved |= i.status in ['resolved', 'closed']
                        fixed |= i.resolution == 'fixed'

                    for e in Event.objects.filter(issue_id=i.id):
                        resolved |= e.status is not None and e.status.lower() == 'status' and e.new_value is not None and e.new_value.lower() in ['resolved', 'closed']
                        fixed |= e.status is not None and e.status.lower() == 'resolution' and e.new_value is not None and e.new_value.lower() == 'fixed'

                if resolved and fixed:
                    score += 1
                    ret.append(i)

            except Issue.DoesNotExist:
                # self._log.error('issue: {} does not exist'.format(m.group(1)))
                self._error('issue: {} does not exist'.format(m.group('ID')))
                pass
        return score, ret, issue_found

    def _jira_label(self, issue_system, message):
        score = 0
        ret = []
        issue_found = False
        for m in self._direct_link_jira.finditer(message):
            resolved = False
            fixed = False
            try:
                i = Issue.objects.get(issue_system_id=issue_system.id, external_id=m.group('ID').upper())
                issue_found = True
                if not i.issue_type:
                    # self._log.error("could not find issue type for issue: {}".format(m.group(0)))
                    self._error('could not find issue type for issue: {}'.format(m.group('ID')))

                if i.issue_type and i.issue_type.lower() == 'bug':
                    if i.status in ['resolved', 'closed']:
                        resolved |= i.status in ['resolved', 'closed']
                        fixed |= i.resolution == 'fixed'

                    for e in Event.objects.filter(issue_id=i.id):
                        resolved |= e.status is not None and e.status.lower() == 'status' and e.new_value is not None and e.new_value.lower() in ['resolved', 'closed']
                        fixed |= e.status is not None and e.status.lower() == 'resolution' and e.new_value is not None and e.new_value.lower() == 'fixed'

                if resolved and fixed:
                    score += 1
                    ret.append(i)

            except Issue.DoesNotExist:
                # self._log.error('issue: {} does not exist'.format(m.group(0)))
                self._error('issue: {} does not exist'.format(m.group(1)))
                pass
        return score, ret, issue_found

    def _error(self, message):
        self._log.error(message)
