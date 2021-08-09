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


class CheckOFED(Actor):
    """
    Check if any OFED packages are installed and inhibit the upgrade

    """

    name = 'check_ofed'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        pkgs = self.get_ofed_pkgs()
        if not pkgs:
            api.current_logger().info('No OFED packages found')
        else:
            self.produce_inhibitor(pkgs)

    def get_ofed_pkgs(self):
        """
        Find OFED packages
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        ofed_packages = []

        for pkg in rpms:
            if pkg.repository == 'ol7_UEKR3_OFED20' or pkg.repository == 'ol7_UEKR4_OFED':
                api.current_logger().warning('OFED package found {}'.format(pkg.name))
                ofed_packages.append(pkg.name)

        if ofed_packages:
            return ofed_packages

        for pkg in rpms:
            release = pkg.release
            pkg_name = pkg.name
            if (release.find('OFED.IOV') != -1):
                api.current_logger().info('OFED package found {}'.format(pkg_name))
                ofed_packages.append(pkg_name)
            if pkg_name == 'libibverbs' and (release.find('el7uek4') != -1):
                api.current_logger().info('OFED package found {}'.format(pkg_name))
                ofed_packages.append(pkg_name)
        return ofed_packages


    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the following OFED packages have been detected. '
        summary += 'Leapp upgrades are unsupported when OFED packages are installed.\n{}'.format('\n'.join(pkgs))
        create_report([
            reporting.Title('OFED packages detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Tags([
                    reporting.Tags.SECURITY,
                    reporting.Tags.TOOLS
            ]),
            reporting.Flags([reporting.Flags.INHIBITOR])
        ])

