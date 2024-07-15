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
import subprocess


class CheckOSMS(Actor):
    """
    Check if OS Management Service (OSMS) is configured and active. If yes, inhibit the upgrade process.
    Do not inhibit, if leapp is executed with --osms flag
    """

    name = 'check_osms'
    consumes = (InstalledRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        if os.getenv('LEAPP_OSMS') == '1':
            return
        if has_package(InstalledRPM, 'osms-agent'):
            api.current_logger().warning('osms-agent package has been detected')
            self.produce_inhibitor()
            return

        result = self.osms_check()
        if result == 1:
            self.produce_inhibitor()

    def osms_check(self):
        try:
            ps = subprocess.Popen("ps -eaf | grep osms-agent | grep -v grep", shell=True, stdout=subprocess.PIPE)
            output = ps.stdout.read()
            ps.stdout.close()
            ps.wait()

            if (output.find('osms') != -1):
                api.current_logger().warning('Active osms-agent plugin has been detected')
                result = 1
            else:
                result = 0
        except:
            api.current_logger().warning('Unable to determine if osms plugin is active')
            result = 1

        return result

    def produce_inhibitor(self):
        remediation = ('The OSMS agent is included in OCI Oracle Linux platform images '
                       'and installed by default. If the instance is not actively managed '
                       'by OSMS, the OSMS agent can be disabled from the OCI console and the '
                       'upgrade can proceed. Please refer to '
                       'https://docs.oracle.com/en/operating-systems/oracle-linux/8/leapp/ '
                       'for information about disabling the OSMS agent.')
        create_report([
            reporting.Title('The OS Management Service (OSMS) agent is running on this instance.'),
            reporting.Summary(
                'The OSMS service is active on this instance.\n\n'
                'The OS Management Service does not currently support Oracle Linux 8 '
                'AppStreams, also known as modules or module streams.\n'
                'Upgrade cannot proceed with the OSMS agent active. '
                'Please refer to https://docs.oracle.com/en-us/iaas/os-management/osms/osms-getstarted.htm '
                'for more information about OSMS and Oracle Linux 8.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Tags([
                    reporting.Tags.SERVICES,
                    reporting.Tags.TOOLS
            ]),
            reporting.Flags([reporting.Flags.INHIBITOR]),
            reporting.Remediation(hint=remediation)
        ])

