import subprocess
import sys
from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.models import ActiveKernelModulesFacts
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
from leapp.libraries.stdlib import api


class CheckBtrfsRAID(Actor):
    """
    Check if Btrfs RAID is in use. If yes, inhibit the upgrade process.

    """

    name = 'check_btrfs_raid'
    consumes = (ActiveKernelModulesFacts,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == 'btrfs':
                    result = self.check_raid_in_use()
                    if result is True:
                        self.produce_inhibitor()
                    break

    def check_raid_in_use(self):
        mounts = []
        raid_found = False
        try:
            for line in subprocess.check_output(['df', '-t', 'btrfs']).decode(sys.stdout.encoding).strip().split('\n'):
                if len(line.split()) > 2:
                    api.current_logger().info('Found BTRFS mount {}'.format(line.split()[5]))
                    mounts.append(line.split()[5])
        except:
            api.current_logger().error('BTRFS kernel module is loaded, but no btrfs filesystems detected.')
            return True

        mounts.remove('Mounted')

        for mount in mounts:
            for line in subprocess.check_output(['btrfs', 'fi', 'df', mount]).decode(sys.stdout.encoding).strip().split('\n'):
                if (line.find('RAID') != -1):
                    raid_found = True

        if raid_found:
            return True

    def produce_inhibitor(self):
        create_report([
            reporting.Title('BTRFS RAID detected, upgrade cannot proceed.'),
            reporting.Summary(
                'Upgrade process was interrupted because BTRFS RAID has been '
                'detected, upgrade is unavailable if BTRFS RAID is in use. '
            ),
            reporting.Remediation(hint='If you are sure btrfs is not being used, '
                'you can unload the btrfs kernel module by running `modprobe -r btrfs` '
                'and run the leapp upgrade again'),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.FILESYSTEM,
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.RelatedResource('kernel-driver', 'btrfs')
        ])



