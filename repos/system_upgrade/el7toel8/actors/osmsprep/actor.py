from leapp.libraries.common.config import get_env
from leapp.actors import Actor
from leapp.libraries.stdlib import run, api
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report

class OSMSprepRepos(Actor):
    """
    Perform preparational work for managed instance upgrade
    """

    name = 'osmspreprepos'
    consumes = ()
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        if not get_env("LEAPP_OSMS"):
            return
        elif get_env("LEAPP_OSMS") == '1':
            self.add_leapp_repo()


    def add_leapp_repo(self):
        configfile = '/etc/oracle-cloud-agent/plugins/osms/ignored_repos.conf'
        leapp_repo_name = 'leapp-upgrade-repos-ol8.repo\n'
        api.current_logger().warning("Upgrade of OCI manage instance is requested.\nAdding leapp-upgrade-repos-ol8.repo to\n/etc/oracle-cloud-agent/plugins/osms/ignored_repos.conf\nand restarting oracle-cloud-agent")
        fconfig = open(configfile, "a")
        if leapp_repo_name not in open(configfile).read():
            fconfig.write(leapp_repo_name)
        run(['systemctl', 'restart', 'oracle-cloud-agent'])
        return
