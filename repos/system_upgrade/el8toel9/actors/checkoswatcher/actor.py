from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.models import DistributionSignedRPM, InstalledRPM
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.libraries.common.config import architecture
from leapp.dialogs.components import BooleanComponent
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os
import sys


class CheckOSWatcher(Actor):
    """
    Check if oswatcher package is installed and notify of upgrade to pcp in OL9

    """

    name = 'check_oswatcher'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)
    dialogs = (
        Dialog(
            scope='update_oswatcher_to_pcp',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Confirm upgrade of oswatcher package to pcp? '
                          'If no, the upgrade process will be interrupted.',
                    description='oswatcher package has been replaced by pcp in OL9'
                                'Confirm upgrade of oswatcher package to pcp?',
                    reason='oswatcher package has been replaced by pcp in OL9'
                ),
            )
        ),
    )

    def process(self):
        pkgs = self.get_oswatcher_packages()
        if not pkgs:
            return

        confirm_upgrade = self.confirm()
        if confirm_upgrade is True:
            self.produce_report()
        else:
            self.produce_inhibitor()

    def confirm(self):
        answer = self.get_answers(self.dialogs[0])
        return answer.get('confirm')

    def get_oswatcher_packages(self):
        """
        Find oswatcher package
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        oswatcher_packages = []

        for pkg in rpms:
            if pkg.name == 'oswatcher':
                api.current_logger().info('Oracle oswatcher package found {}'.format(pkg.name))
                oswatcher_packages.append(pkg.name)

        if oswatcher_packages:
            return oswatcher_packages

    def produce_report(self):
        summary = 'OSWatcher package has been removed in OL9 and will be replaced by pcp.'
        create_report([
            reporting.Title('OSWatcher is removed from OL9.'),
            reporting.Summary(summary),
            reporting.ExternalLink(
                title='Working With Performance Co-Pilot',
                url='https://docs.oracle.com/en/operating-systems/oracle-linux/9/monitoring/monitoring-WorkingWithPerformanceCoPilot.html#pcp%22'
            ),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Severity(reporting.Severity.HIGH)
        ])

    def produce_inhibitor(self):
        summary = 'Upgrade process was inhibited as OSWatcher is no longer available in OL9. '
        summary += 'Please confirm the update of the oswatcher package to pcp.'
        create_report([
            reporting.Title('OSWatcher is removed from OL9.'),
            reporting.Summary(summary),
            reporting.ExternalLink(
                title='Working With Performance Co-Pilot',
                url='https://docs.oracle.com/en/operating-systems/oracle-linux/9/monitoring/monitoring-WorkingWithPerformanceCoPilot.html#pcp%22'
            ),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

