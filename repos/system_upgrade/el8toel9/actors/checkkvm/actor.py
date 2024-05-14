from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.models import DistributionSignedRPM, InstalledRPM, RpmTransactionTasks
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.libraries.common.config import architecture
from leapp.dialogs.components import BooleanComponent
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os
import sys


class CheckKVM(Actor):
    """
    Check if Oracle KVM is installed and ensure ol9_kvm_utils is enabled

    """

    name = 'check_kvm'
    consumes = (DistributionSignedRPM,)
    produces = (Report,RpmTransactionTasks,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        pkgs = self.get_oracle_kvm_pkgs()
        if not pkgs:
            api.current_logger().info('No Oracle KVM packages found')
            return

        oracle_kvm = self.is_kvm_utils_enabled()
        api.current_logger().info('Oracle KVM repo result: {}'.format(oracle_kvm))
        if oracle_kvm is False:
            api.current_logger().warning('Oracle ol9_kvm_utils is not enabled')
            self.produce_inhibitor(pkgs)

    def get_oracle_kvm_pkgs(self):
        """
        Find Oracle KVM packages
        """
        rpms_to_exclude = []
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        kvm_packages = []

        for pkg in rpms:
            if pkg.repository == 'ol8_kvm_appstream':
                if pkg.name == 'libvirt-bash-completion' and pkg.stream == 'kvm_utils':
                    rpms_to_exclude.append('libvirt-daemon-common')
                    api.produce(RpmTransactionTasks(to_exclude=rpms_to_exclude))
                api.current_logger().info('Oracle KVM package found {}'.format(pkg.name))
                kvm_packages.append(pkg.name)
        
        if kvm_packages:
            api.current_logger().info('Excluding OL9 package from transaction: {}'.format('libvirt-daemon-common'))
            return kvm_packages

    def is_kvm_utils_enabled(self):
        leapp_enabled_repos = os.getenv('LEAPP_ENABLE_REPOS','')
        if (leapp_enabled_repos.find('ol9_kvm_utils') != -1):
            api.current_logger().info('LEAPP_ENABLE_REPOS has ol9_kvm_utils is enabled')
            return True
        else:
            return False

    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the following Oracle KVM packages have been detected, '
        summary += 'but Oracle KVM upgrade repository ol9_kvm_utils has not been enabled.\n{}'.format('\n'.join(pkgs))
        create_report([
            reporting.Title('Oracle KVM packages detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

