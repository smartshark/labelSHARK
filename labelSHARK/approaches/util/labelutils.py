import logging

from pycoshark.mongomodels import Event, IssueSystem
from pycoshark.utils import jira_is_resolved_and_fixed

log = logging.getLogger('labelSHARK')


def isbugfix(issue):
    its = IssueSystem.objects(id=issue.issue_system_id).get()
    if 'jira' in its.url:
        return _jira_isbugfix(issue)
    elif 'bugzilla' in its.url:
        return _bz_isbugfix(issue)
    elif 'github' in its.url:
        return _gh_isbugfix(issue)
    else:
        log.error('unknown ITS type for ITS url %s for bugfix labels' % its.url)
        return False


def isfeatureadd(issue):
    its = IssueSystem.objects(id=issue.issue_system_id).get()
    if 'jira' in its.url:
        return _is_jira_featureadd(issue)
    else:
        log.error('unknown ITS type for ITS url %s for feature add labels' % its.url)
        return False

def _is_jira_featureadd(issue):
    is_added_feature = False
    featureadd_types = set(['new feature','proposal','improvement','wish','planned work','request'])
    if not issue.issue_type:
        log.warning('could not find issue type for issue %s' % issue.id)
    else:
        if issue.issue_type and issue.issue_type.lower() in featureadd_types:
            is_added_feature = jira_is_resolved_and_fixed(issue)
    return is_added_feature

def _jira_isbugfix(issue):
    is_fixed_bug = False
    if not issue.issue_type:
        log.warning('could not find issue type for issue %s' % issue.id)
    else:
        if issue.issue_type and issue.issue_type.lower() == 'bug':
            is_fixed_bug = jira_is_resolved_and_fixed(issue)
    return is_fixed_bug

def _bz_isbugfix(issue):
    resolved = False
    fixed = False
    if not issue.issue_type:
        log.error('could not find issue type for issue %s' % issue.id)
    else:
        if issue.issue_type and issue.issue_type.lower() == 'bug':
            if issue.status in ['resolved', 'closed']:
                resolved = True
                fixed |= issue.resolution == 'fixed'

            for e in Event.objects.filter(issue_id=issue.id):
                resolved |= e.status is not None and e.status.lower() == 'status' and e.new_value is not None and e.new_value.lower() in [
                    'resolved', 'closed']
                fixed |= e.status is not None and e.status.lower() == 'resolution' and e.new_value is not None and e.new_value.lower() == 'fixed'
    return resolved and fixed


def _gh_isbugfix(issue):
    """We can only be sure about the status, which is either open or closed. Labels are custom per project. Type is not required."""
    if issue.status in ['closed']:
        return True
    else:
        return False
