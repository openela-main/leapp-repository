from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.libraries.common.rpms import has_package
from leapp.libraries.stdlib import api
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp.models import InstalledRPM
from leapp import reporting
from leapp.reporting import Report, create_report
import os
import os.path
import subprocess


class CheckALX(Actor):
    """
    Check if instance is Autonomous Linux Instance. If yes, inhibit the upgrade process.

    """

    name = 'check_alx'
    consumes = (InstalledRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        alx_bin = "/usr/sbin/alx"
        if os.path.isfile(alx_bin):
            api.current_logger().warning('/usr/sbin/alx binary is detected')
            self.produce_inhibitor()
            return

        result = self.osms_check()
        if result == 1:
            self.produce_inhibitor()

    def osms_check(self):
        try:
            ps = subprocess.Popen("ps -eaf | grep oci-alx | grep -v grep", shell=True, stdout=subprocess.PIPE)
            output = ps.stdout.read()
            ps.stdout.close()
            ps.wait()

            if (output.find('oci-alx') != -1):
                api.current_logger().warning('services, associated with Autonomous Linux Instance are running')
                result = 1
            else:
                result = 0
        except:
            api.current_logger().warning('Unable to identify if Autonomous Linux Instance services are running')
            result = 1

        return result

    def produce_inhibitor(self):
        remediation = ('Instance is identified to be an Autonomous Linux Instance. '
                       'Autonomous Linux Instances cannot be upgraded with Leapp. '
                       'Please refer to https://docs.oracle.com/en/operating-systems/oracle-linux/8/leapp/ '
                       'for information about leapp upgrade process.')
        create_report([
            reporting.Title('Autonomous Linux Instances cannot be upgraded with Leapp.'),
            reporting.Summary(
                'Instance is identified to be an Autonomous Linux Instance.\n\n'
                'leapp does not support Autonomous Linux Instance upgrade. '
                'Upgrade cannot proceed. '
                'Please refer to https://docs.oracle.com/en/operating-systems/oracle-linux/8/leapp/#olrm-oracle-linux-8 '
                'for more information about leapp upgrade process.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Tags([
                    reporting.Tags.SERVICES,
                    reporting.Tags.TOOLS
            ]),
            reporting.Flags([reporting.Flags.INHIBITOR]),
            reporting.Remediation(hint=remediation)
        ])

