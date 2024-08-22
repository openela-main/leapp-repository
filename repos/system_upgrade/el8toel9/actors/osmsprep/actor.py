from leapp.libraries.common.config import get_env
from leapp.actors import Actor
from leapp.libraries.stdlib import run, api
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os.path, shutil

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
        leapp_repo_name = 'leapp-upgrade-repos-ol9.repo\n'
        leapp_repo_file = '/etc/yum.repos.d/leapp-upgrade-repos-ol9.repo'
        leapp_repo_file_osms_backup = '/etc/yum.repos.d/leapp-upgrade-repos-ol9.repo.osms-backup'
        api.current_logger().warning("Upgrade of OCI managed instance is requested. Adding leapp-upgrade-repos-ol9.repo to /etc/oracle-cloud-agent/plugins/osms/ignored_repos.conf and restarting oracle-cloud-agent")
        fconfig = open(configfile, "a")
        if leapp_repo_name not in open(configfile).read():
            fconfig.write(leapp_repo_name)
        run(['systemctl', 'restart', 'oracle-cloud-agent'])
        if not os.path.isfile(leapp_repo_file) and os.path.isfile(leapp_repo_file_osms_backup):
            api.current_logger().warning("leapp repository file %s not found, but it's backup %s found, restoring leapp repository file to proceed with upgrade", leapp_repo_file, leapp_repo_file_osms_backup)
            shutil.copyfile(leapp_repo_file_osms_backup, leapp_repo_file)
        return
