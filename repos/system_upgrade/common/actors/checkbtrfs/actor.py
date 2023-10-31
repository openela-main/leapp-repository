from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.models import ActiveKernelModulesFacts
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report


class CheckBtrfs(Actor):
    """
    Check if Btrfs filesystem is in use. If yes, inhibit the upgrade process.

    """

    name = 'check_btrfs'
    consumes = (ActiveKernelModulesFacts,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)
    dialogs = (
        Dialog(
            scope='confirm_UEK_install_and_default_boot_kernel',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Use UEK as default boot in OL8? '
                          'If no, the upgrade process will be interrupted.',
                    description='BTRFS module is no longer available in RHCK. '
                                'Confirm install of UEK as default boot kernel.',
                    reason='BTRFS module is no longer available in RHCK. '
                           'BTRFS filesystems will be inaccesible when booting '
                           'into RHCK in OL8'
                ),
            )
        ),
    )

    def process(self):

        hint = 'In order to unload the module from the running system, check the accompanied command.'
        command = ['modprobe', '-r', 'btrfs']

        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == 'btrfs':
                    result = self.confirm()
                    if result is True:
                        self.produce_report()
                    else:
                        self.produce_inhibitor()
                    break

    def confirm(self):
        answer = self.get_answers(self.dialogs[0])
        return answer.get('confirm')

    def produce_report(self):
        create_report([
            reporting.Title('Btrfs supported in UEK only'),
            reporting.Summary(
                'The Btrfs file system has been removed in RHCK8, only supported using UEK in OL8'
            ),
            reporting.ExternalLink(
                title='Managing the Btrfs File System',
                url='https://docs.oracle.com/en/operating-systems/oracle-linux/8/fsadmin/fsadmin-ManagingtheBtrfsFileSystem.html#btrfs-main'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Tags([reporting.Tags.FILESYSTEM]),
            reporting.RelatedResource('kernel-driver', 'btrfs')
        ])

    def produce_inhibitor(self):
        create_report([
            reporting.Title('BTRFS used, confirm UEK as default boot kernel in OL8 '),
            reporting.Summary(
                'Upgrade process was interrupted because btrfs is enabled '
                'and need to confirm UEK as default boot kernel in OL8 '
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Tags([
                    reporting.Tags.FILESYSTEM,
                    reporting.Tags.SECURITY,
                    reporting.Tags.TOOLS
            ]),
            reporting.Flags([reporting.Flags.INHIBITOR]),
            reporting.Remediation(hint='Confirm UEK kernel install and default boot'),
            reporting.RelatedResource('kernel-driver', 'btrfs')
        ])

