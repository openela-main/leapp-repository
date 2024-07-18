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


class CheckLVM2Cluster(Actor):
    """
    Check if Oracle lvm2-cluster package is installed and inhibit upgrade

    """

    name = 'check_lvm2_cluster'
    consumes = (InstalledRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        pkgs = self.get_lvm2_cluster_pkgs()
        if not pkgs:
            api.current_logger().info('lvm2-cluster package is not installed')
            return

        self.produce_inhibitor(pkgs)

    def get_lvm2_cluster_pkgs(self):
        """
        Find Oracle lvm2-cluster packages
        """
        rpms = next(api.consume(InstalledRPM), InstalledRPM()).items
        lvm2_cluster_packages = []

        for pkg in rpms:
            if pkg.name == 'lvm2-cluster':
                api.current_logger().info('lvm2-cluster package found {}'.format(pkg.name))
                lvm2_cluster_packages.append(pkg.name)

        if lvm2_cluster_packages:
            return lvm2_cluster_packages

    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the lvm2-cluster package has been detected.'
        create_report([
            reporting.Title('Unsupported package upgrade lvm2-cluster detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

