from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.models import ActiveKernelModulesFacts
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
from leapp.libraries.common.config import architecture
from leapp.models import DistributionSignedRPM
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
import warnings
import subprocess
import os
import sys
import rpm

class CheckUEKR7(Actor):
    """
    Inhibit aarch64 upgrade if running UEKR6 or BTRFS filesystem in use.

    """

    name = 'check_uekr7'
    consumes = (ActiveKernelModulesFacts,DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)
    dialogs = (
        Dialog(
            scope='confirm_UEKR7_install_pagesize_4k',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Confirm upgrade to UEKR7 and pagesize change? '
                          'If no, the upgrade process will be interrupted.',
                    description='UEKR7 for aarch64 pagesize has changed from 64k to 4k.'
                                'Confirm install of UEK and pagesize change.',
                    reason='UEKR7 for aarch64 pagesize has changed from 64k to 4k.'
                ),
            )
        ),
    )

    def process(self):
        if not architecture.matches_architecture(architecture.ARCH_ARM64):
            return
        uekr7_current_kernel = self.check_uekr7_running()
        if uekr7_current_kernel is True:
            api.current_logger().info('Current running kernel version is UEKR7')
            return
        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == 'btrfs':
                    self.produce_inhibitor()
                    break
        result = self.confirm()
        if result is True:
            self.produce_report()
        else:
            self.produce_inhibitor_no_btrfs()

    def confirm(self):
        answer = self.get_answers(self.dialogs[0])
        return answer.get('confirm')

    def check_uekr7_running(self):
        running_kernel_version = api.current_actor().configuration.kernel.split('-')[0]
        api.current_logger().info('Current running kernel version is {}'.format(running_kernel_version))
        if running_kernel_version == "5.15.0":
            return True
        return False

    def produce_report(self):
        create_report([
            reporting.Title('Confirm upgrade to UEKR7 and pagesize change to 4k.'),
            reporting.Summary(
                'OL9 UEKR7 pagesize has changed from 64 to 4k. Require confirmation of upgrade.'
            ),
            reporting.ExternalLink(
                title='UEKR7 Pagesize change to 4k',
                url='https://docs.oracle.com/en/operating-systems/oracle-linux/9/install/'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([reporting.Groups.FILESYSTEM]),
            reporting.RelatedResource('kernel-driver', 'btrfs')
        ])

    def produce_inhibitor(self):
        create_report([
            reporting.Title('UEKR6 has been found and BTRFS filesystem in use.'),
            reporting.Summary(
                'Upgrade process was interrupted because btrfs is enabled '
                'and UEKR6 has been found.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.FILESYSTEM,
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(hint='Check the Oracle Linux documentation for OL9'),
            reporting.RelatedResource('kernel-driver', 'btrfs')
        ])

    def produce_inhibitor_no_btrfs(self):
        create_report([
            reporting.Title('Confirm upgrade to UEKR7 and pagesize change to 4k.'),
            reporting.Summary(
                'OL9 UEKR7 pagesize has changed from 64 to 4k. Require confirmation of upgrade.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.FILESYSTEM,
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(hint='Check the Oracle Linux documentation for OL9'),
            reporting.RelatedResource('kernel-driver', 'btrfs')
        ])

