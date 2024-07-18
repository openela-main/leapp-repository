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
    Do not inhibit, if it is auto-detected that instance is the OCI Managed Instance.
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
                       'by OSMS, you should disable OSMS agent '
                       'from the OCI console and the upgrade can proceed. Please refer to '
                       'https://docs.oracle.com/en/operating-systems/oracle-linux/8/leapp/ '
                       'for information about upgrading instances managed by OSMS.')
        create_report([
            reporting.Title('The OS Management Service (OSMS) agent is running on this instance and instance is not identified as managed'),
            reporting.Summary(
                'The OSMS service is active on this instance.\n\n'
                'Upgrade cannot proceed with the OSMS agent active, unless you ensure '
                'yum reports system as receiving updates from OSMS. '
                'Please refer to https://docs.oracle.com/en/operating-systems/oracle-linux/8/leapp/ '
                'for information about upgrading instances managed by OSMS. '
                'Please refer to https://docs.oracle.com/en-us/iaas/os-management/osms/osms-getstarted.htm '
                'for more information about OSMS and Oracle Linux 8.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SERVICES,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(hint=remediation)
        ])

