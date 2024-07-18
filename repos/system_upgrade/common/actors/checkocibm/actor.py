from leapp.actors import Actor
from leapp.libraries.stdlib import api
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os
import subprocess


class CheckOCIBM(Actor):
    """
    Check if the system is an OCI BM shape. If yes, inhibit the upgrade process.

    """

    name = 'check_ocibm'
    consumes = ()
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        result = self.ocibm_check()
        if result == 1:
            self.produce_inhibitor()

    def ocibm_check(self):
        try:
            cmd = "curl --connect-timeout 10 --max-time 30 -s -H \"Authorization: Bearer Oracle\" -L http://169.254.169.254/opc/v2/instance/shape"
            ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output = ps.stdout.read()
            ps.stdout.close()
            ps.wait()

            if (output.find(b'BM.') != -1):
                api.current_logger().warning('OCI BM shape has been detected')
                result = 1
            else:
                result = 0
        except:
            api.current_logger().warning('Unable to determine if system is an OCI BM shape')
            result = 1

        return result

    def produce_inhibitor(self):
        create_report([
            reporting.Title('OCI BM shape has been detected.'),
            reporting.Summary(
                'OCI BM shapes are unsupported and cannot be upgraded by leapp.\n'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SERVICES,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

