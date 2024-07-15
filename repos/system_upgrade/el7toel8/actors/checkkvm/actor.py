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
try:
    import ConfigParser
except ImportError:
    warnings.warn('ConfigParser is unavailable', ImportWarning)


class CheckKVM(Actor):
    """
    Check if Oracle KVM is installed and ensure ol8_kvm_appstream is enabled

    """

    name = 'check_kvm'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        VIRT_MODULE_FILE="/etc/dnf/modules.d/virt.module"
        if os.path.exists(VIRT_MODULE_FILE):
            os.remove(VIRT_MODULE_FILE)
        pkgs = self.get_oracle_kvm_pkgs()
        if not pkgs:
            api.current_logger().info('No Oracle KVM packages found')
            return

        oracle_kvm = self.is_kvm_appstream_enabled()
        api.current_logger().info('Oracle KVM repo result: {}'.format(oracle_kvm))
        if oracle_kvm is False:
            api.current_logger().warning('Oracle ol8_kvm_appstream is not enabled')
            self.produce_inhibitor(pkgs)
            return

        config = ConfigParser.RawConfigParser()
        config.add_section('virt')
        config.set('virt','name','virt')
        config.set('virt','stream','kvm_utils2')
        config.set('virt','profiles','common')
        config.set('virt','state','enabled')

        with open(VIRT_MODULE_FILE, 'w') as configfile:
            config.write(configfile)

        self.produce_report()

    def get_oracle_kvm_pkgs(self):
        """
        Find Oracle KVM packages
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        kvm_packages = []

        for pkg in rpms:
            if pkg.repository == 'ol7_kvm_utils':
                api.current_logger().info('Oracle KVM package found {}'.format(pkg.name))
                kvm_packages.append(pkg.name)
            if pkg.name == 'qemu-kvm' and architecture.matches_architecture(architecture.ARCH_ARM64):
                api.current_logger().info('Oracle KVM package found {}'.format(pkg.name))
                kvm_packages.append(pkg.name)

        if kvm_packages:
            return kvm_packages

    def is_kvm_appstream_enabled(self):
        leapp_enabled_repos = os.getenv('LEAPP_ENABLE_REPOS','')
        if (leapp_enabled_repos.find('ol8_kvm_appstream') != -1):
            api.current_logger().info('LEAPP_ENABLE_REPOS has ol8_kvm_appstream is enabled')
            return True
        else:
            return False

    def produce_report(self):
        if architecture.matches_architecture(architecture.ARCH_ARM64):
            arch = "aarch64"
        else:
            arch = "x86_64"
        summary = 'The QEMU emulator executable in Oracle Linux 8 is /usr/libexec/qemu-kvm. '
        summary += 'In Oracle Linux 7, architecture-specific QEMU emulators were used. As part '
        summary += 'of the upgrade, Leapp will create a symlink from /usr/bin/qemu-system-{} '.format(arch)
        summary += 'to /usr/libexec/qemu-kvm to accommodate existing KVM guests.'
        create_report([
            reporting.Title('Difference in QEMU emulator in OL8'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.LOW),
            reporting.Groups([reporting.Groups.FILESYSTEM])
        ])

    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the following Oracle KVM packages have been detected, '
        summary += 'but Oracle KVM upgrade repository ol8_kvm_appstream has not been enabled.\n{}'.format('\n'.join(pkgs))
        create_report([
            reporting.Title('Oracle KVM packages detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Tags([
                    reporting.Tags.SECURITY,
                    reporting.Tags.TOOLS
            ]),
            reporting.Flags([reporting.Flags.INHIBITOR])
        ])

