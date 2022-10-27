import os
import errno

from leapp.actors import Actor
from leapp.libraries.stdlib import run
from leapp.reporting import Report, create_report
from leapp import reporting
from leapp.tags import FinalizationPhaseTag, IPUWorkflowTag


class OraclePostUpgrade(Actor):
    """
    Rename the leapp upgrade repo file /etc/yum.repos.d/leapp-upgrade-repos-ol9.repo

    Required as it may interfere with installed files from oraclelinux-release-el9.
    """

    name = 'oraclepostupgrade'
    consumes = ()
    produces = (Report,)
    tags = (FinalizationPhaseTag, IPUWorkflowTag)

    def process(self):
        leapp_upgrade_repo_file = '/etc/yum.repos.d/leapp-upgrade-repos-ol9.repo'
        leapp_save_file = '/etc/yum.repos.d/leapp-upgrade-repos-ol9.repo.save'
        if os.path.isfile(leapp_upgrade_repo_file):
            try:
                os.rename(leapp_upgrade_repo_file,leapp_save_file)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

        create_report([
            reporting.Title('Leapp upgrade file {} renamed'.format(leapp_upgrade_repo_file)),
            reporting.Summary(
                'The upgrade repo file has been renamed "{}"'.format(leapp_save_file)),
            reporting.Groups([reporting.Groups.UPGRADE_PROCESS]),
        ])

