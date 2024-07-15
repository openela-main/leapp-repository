from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.models import DistributionSignedRPM, InstalledRPM
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.dialogs.components import BooleanComponent
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os
import sys
import warnings
try:
    import ConfigParser
except ImportError:
    warnings.warn('ConfigParser is unavailable', ImportWarning)


class CheckGLUSTERFS6(Actor):
    """
    Check if GlusterFS 6 rpm packages are installed in this server

    """

    name = 'check_glusterfs6'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        pkgs = self.get_oracle_glusterfs6_pkgs()
        if not pkgs:
            api.current_logger().info('No Oracle GlusterFS 6 packages found')
            return

        if pkgs:
            self.produce_inhibitor(pkgs)
            return

        self.produce_report()

    def get_oracle_glusterfs6_pkgs(self):
        """
        Find Oracle GlusterFS 6 packages
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        glusterfs6_packages = []

        for pkg in rpms:
            if pkg.repository == 'ol7_gluster6':
                api.current_logger().info('Oracle GlusterFS 6 packages found {}'.format(pkg.name))
                glusterfs6_packages.append(pkg.name)

        if glusterfs6_packages:
            return glusterfs6_packages

    def produce_report(self):
        summary = 'No GlusterFS 6 packages are installed on this server. '
        create_report([
            reporting.Title('GlusterFS 6 is not installed'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.LOW),
            reporting.Groups([reporting.Groups.FILESYSTEM])
        ])

    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the following Oracle GlusterFS 6 packages have been detected, '
        summary += 'start by upgrading GlusterFS 6 to GlusterFS 8 following the documentation, '
        summary += 'also Oracle GlusterFS8 upgrade repository ol8_gluster_appstream has not been enabled.\n{}'.format('\n'.join(pkgs))
        create_report([
            reporting.Title('Oracle GlusterFS 6 packages detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])


