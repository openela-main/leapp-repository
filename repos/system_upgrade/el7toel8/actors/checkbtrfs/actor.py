from leapp import reporting
from leapp.actors import Actor
from leapp.models import ActiveKernelModulesFacts
from leapp.reporting import create_report, Report
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class CheckBtrfs(Actor):
    """
    Check if Btrfs filesystem is in use. If yes, inhibit the upgrade process.

    """

    name = 'check_btrfs'
    consumes = (ActiveKernelModulesFacts,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):

        hint = 'In order to unload the module from the running system, check the accompanied command.'
        command = ['modprobe', '-r', 'btrfs']

        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == 'btrfs':
                    create_report([
                        reporting.Title('Btrfs supported in UEK only'),
                        reporting.Summary(
                            'The Btrfs file system has been removed in RHCK8, only supported using UEK in OL8'
                        ),
                        reporting.ExternalLink(
                            title='Managing the Btrfs File System',
                            url='https://docs.oracle.com/en/operating-systems/oracle-linux/8/fsadmin/fsadmin-ManagingtheBtrfsFileSystem.html#btrfs-main'  # noqa: E501; pylint: disable=line-too-long
                        ),
                        reporting.Severity(reporting.Severity.HIGH),
                        reporting.Groups([reporting.Groups.FILESYSTEM]),
                        reporting.Remediation(hint=hint, commands=[command]),
                        reporting.RelatedResource('kernel-driver', 'btrfs')
                    ])
                    break
