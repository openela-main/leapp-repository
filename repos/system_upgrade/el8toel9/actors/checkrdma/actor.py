from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.models import DistributionSignedRPM, InstalledRPM, RepositoriesFacts
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.libraries.common.config import architecture
from leapp.dialogs.components import BooleanComponent
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os
import sys


class CheckRDMA(Actor):
    """
    Check if RDMA UEKR6 is installed and confirm upgrade to RDMA UEKR7

    """

    name = 'check_rdma'
    consumes = (DistributionSignedRPM,RepositoriesFacts,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)
    dialogs = (
        Dialog(
            scope='confirm_RDMA_upgrade_to_UEKR7',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Confirm upgrade to RDMA UEKR7? '
                          'If no, the upgrade process will be interrupted.',
                    description='OL9 only supports RDMA UEKR7.'
                                'Confirm install of UEKR7 kernel and RDMA',
                    reason='OL9 only supports RDMA UEKR7.'
                ),
            )
        ),
    )

    def process(self):
        pkgs = self.get_oracle_rdma_pkgs()
        if not pkgs and not self.check_ol8_rdma_uekr6_enabled():
            api.current_logger().info('No Oracle RDMA configuration found')
            return

        if self.check_uekr7_running():
            if self.is_ol9_rdma_enabled():
                api.current_logger().info('RDMA detected, running kernel is UEKR7 and ol9_RDMA is enabled.')
                self.produce_report()
                return
            else:
                api.current_logger().warning('RDMA detected, running kernel is UEKR7 and ol9_RDMA is not enabled.')
                self.produce_inhibitor_enable_repo()
                return

        if self.confirm():
            if self.is_ol9_rdma_enabled():
                api.current_logger().info('RDMA detected and confirmation of upgrade to UEKR7 confirmed.')
                self.produce_report()
                return
            else:
                api.current_logger().warning('RDMA detected, upgrade to UEKR7 confirmed, ol9_RDMA is not enabled.')
                self.produce_inhibitor_enable_repo()
                return
        else:
            api.current_logger().warning('RDMA detected and confirmation of upgrade to UEKR7 not confirmed.')
            self.produce_inhibitor_confirmation()
            return

    def confirm(self):
        answer = self.get_answers(self.dialogs[0])
        return answer.get('confirm')

    def check_ol8_rdma_uekr6_enabled(self):
        for repos in self.consume(RepositoriesFacts):
            for repo_file in repos.repositories:
                for repo in repo_file.data:
                    api.current_logger().warning('REPO {}'.format(repo.repoid))
                    if repo.repoid == 'ol8_UEKR6_RDMA' and repo.enabled:
                        api.current_logger().warning('ol8_UEKR6_RDMA repository is enabled.')
                        return True
        return False

    def get_oracle_rdma_pkgs(self):
        """
        Find Oracle RDMA packages
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        rdma_packages = []

        for pkg in rpms:
            if pkg.name == 'libibverbs' and (pkg.release.find('el8ora') != -1):
                api.current_logger().info('Oracle RDMA package found {}'.format(pkg.name))
                rdma_packages.append(pkg.name)

        if rdma_packages:
            return rdma_packages

    def check_uekr6_running(self):
        running_kernel_version = api.current_actor().configuration.kernel.split('-')[0]
        api.current_logger().info('Current running kernel version is {}'.format(running_kernel_version))
        if running_kernel_version == "5.4.17":
            return True
        return False

    def check_uekr7_running(self):
        running_kernel_version = api.current_actor().configuration.kernel.split('-')[0]
        api.current_logger().info('Current running kernel version is {}'.format(running_kernel_version))
        if running_kernel_version == "5.15.0":
            return True
        return False

    def is_ol9_rdma_enabled(self):
        leapp_enabled_repos = os.getenv('LEAPP_ENABLE_REPOS','')
        if (leapp_enabled_repos.find('ol9_RDMA') != -1):
            api.current_logger().info('LEAPP_ENABLE_REPOS ol9_RDMA is enabled')
            return True
        else:
            api.current_logger().info('LEAPP_ENABLE_REPOS ol9_RDMA is not enabled')
            return False

    def produce_inhibitor_confirmation(self):
        summary = 'Upgrade process was inhibited as RDMA UEKR6 has been detected, '
        summary += 'please confirm upgrade to RDMA UEKR7.'
        create_report([
            reporting.Title('Oracle RDMA UEKR6 has been detected.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.KERNEL,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])

    def produce_inhibitor_enable_repo(self):
        summary = 'Upgrade process was inhibited as RDMA has been detected, '
        summary += 'but OL9 RDMA repo has not been enabled.'
        create_report([
            reporting.Title('Oracle RDMA detected, but OL9 RDMA repository has not been enabled.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.KERNEL,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(hint='Enable the ol9_RDMA repository on the leapp command line.')
        ])

    def produce_report(self):
        create_report([
            reporting.Title('RDMA will be upgraded to UEKR7'),
            reporting.Summary(
                'OL9 only supports UEKR7 kernel and RDMA, UEK and RDMA will be upgraded to UEKR7.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.KERNEL,
                    reporting.Groups.TOOLS
            ])
        ])

