from leapp.actors import Actor
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.models import OracleEnabledRepos, Report
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os


class CheckOracleEnabledRepos(Actor):
    """
    Check repos enabled on the leapp command line.

    """

    name = "check_oracle_enabled_repos"
    consumes = ()
    produces = (OracleEnabledRepos,)
    tags = (ChecksPhaseTag, IPUWorkflowTag,)

    def process(self):
        leapp_enabled_repos = os.getenv('LEAPP_ENABLE_REPOS')
        api.current_logger().info('Setting Oracle enabled repos to {}'.format(leapp_enabled_repos))

        self.produce(OracleEnabledRepos(enabled_repos=leapp_enabled_repos))

