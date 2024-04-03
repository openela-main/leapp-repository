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
import warnings


class CheckOCIRubySDK(Actor):
    """
    Check if oci-ruby-sdk package is installed and suggest proper steps to perform upgrade

    """

    name = 'check_oci-ruby-sdk'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        pkgs = self.get_oracle_ocirubysdk_pkg()
        if not pkgs:
            api.current_logger().info('No oci-ruby-sdk package found')
            return
        self.produce_inhibitor(pkgs)

    def get_oracle_ocirubysdk_pkg(self):
        """
        Find oci-ruby-sdk package
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        ocirubysdk_packages = []

        for pkg in rpms:
            if pkg.name == 'oci-ruby-sdk':
                api.current_logger().info('Oracle oci-ruby-sdk package found {}'.format(pkg.name))
                ocirubysdk_packages.append(pkg.name)

        if ocirubysdk_packages:
            return ocirubysdk_packages

    def produce_inhibitor(self,pkgs):
        create_report([
            reporting.Title('Oracle oci-ruby-sdk package detected, please remove to perform upgrade.'),
            reporting.Summary(
                'oci-ruby-sdk package is detected as installed.\n\n'
                'Upgrade cannot proceed with the package installed, '
                'since Oracle Linux 8 version of oci-ruby-sdk is compatible only with non-default ruby Application Streams. '
                'It is encourage to migrate to other OCI SDKs, or make a choice of what ruby Application Stream to use '
                'after upgrade to Oracle Linux 8. '
                'Please refer to https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/rubysdk.htm '
                'for information about current status of oci-ruby-sdk on Oracle Linux 8. '
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

