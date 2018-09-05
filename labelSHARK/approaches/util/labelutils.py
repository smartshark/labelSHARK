import logging

from pycoshark.mongomodels import Event, IssueSystem

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
        log.error('unknown ITS type for ITS url %s' % its.url)
        return False


def _jira_isbugfix(issue):
    resolved = False
    fixed = False
    if not issue.issue_type:
        log.error('could not find issue type for issue %s' % issue.id)
    else:
        if issue.issue_type and issue.issue_type.lower() == 'bug':
            if issue.status in ['resolved', 'closed']:
                resolved = True
                fixed |= issue.resolution.lower() != 'duplicated'

            for e in Event.objects.filter(issue_id=issue.id):
                resolved |= e.status is not None and e.status.lower() == 'status' and e.new_value is not None and e.new_value.lower() in \
                            ['resolved', 'closed']
                fixed |= e.status is not None and e.status.lower() == 'resolution' and e.new_value is not None and e.new_value.lower() == 'fixed'
    return resolved and fixed


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
