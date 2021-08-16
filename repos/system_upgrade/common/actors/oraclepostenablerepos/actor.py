from leapp.actors import Actor
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.libraries.stdlib import run
from leapp.models import OracleEnabledRepos
from leapp.tags import FirstBootPhaseTag, IPUWorkflowTag


class OraclePostEnableRepos(Actor):
    """
    Enable repos that were enabled on leapp upgrade command
    """

    name = 'oracle_post_enable_repos'
    consumes = (OracleEnabledRepos,)
    produces = ()
    tags = (FirstBootPhaseTag, IPUWorkflowTag)

    def process(self):
        leapp_enabled_repos = next(api.consume(OracleEnabledRepos), None)
        repos_to_enable = leapp_enabled_repos.enabled_repos.split(',')
        for repo in repos_to_enable:
            try:
                api.current_logger().warning('Trying to enable repo {}'.format(repo))
                stdlib.run(['dnf', 'config-manager', '--enable', repo])
            except (OSError, stdlib.CalledProcessError):
                api.current_logger().warning('Failed to enable repo', exc_info=True)
                return

