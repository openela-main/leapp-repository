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


class CheckOLM(Actor):
    """
    Check if OLM client packages are installed and ensure upgrade repo is enabled.

    """

    name = 'check_olm'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        pkgs = self.get_oracle_olm_pkgs()
        if not pkgs:
            api.current_logger().info('No Oracle OLM client packages found')
            return

        oracle_olm = self.is_olm_repo_enabled()
        api.current_logger().info('Oracle OLM client repo result: {}'.format(oracle_olm))
        if oracle_olm is False:
            api.current_logger().warning('Oracle repo ol9_oraclelinuxmanager210_client is not enabled')
            self.produce_inhibitor(pkgs)

    def get_oracle_olm_pkgs(self):
        """
        Find Oracle OLM client packages
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        olm_packages = []

        for pkg in rpms:
            if pkg.repository == 'ol8_oraclelinuxmanager210_client':
                api.current_logger().info('Oracle OLM client package found {}'.format(pkg.name))
                olm_packages.append(pkg.name)

        if olm_packages:
            return olm_packages

    def is_olm_repo_enabled(self):
        leapp_enabled_repos = os.getenv('LEAPP_ENABLE_REPOS','')
        if (leapp_enabled_repos.find('ol9_oraclelinuxmanager210_client') != -1):
            api.current_logger().info('LEAPP_ENABLE_REPOS has ol9_oraclelinuxmanager210_client enabled')
            return True
        else:
            return False

    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the following Oracle OLM client packages have been detected, '
        summary += 'but Oracle OLM client upgrade repository ol9_oraclelinuxmanager210_client has not been enabled.\n{}'.format('\n'.join(pkgs))
        create_report([
            reporting.Title('Oracle OLM client packages detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

