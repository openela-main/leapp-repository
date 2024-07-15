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


class CheckGLUSTERFS8(Actor):
    """
    Check if GlusterFS 8 is installed and ensure ol8_gluster_appstream repository is enabled

    """

    name = 'check_glusterfs8'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        GLUSTERFS_MODULE_FILE="/etc/dnf/modules.d/glusterfs.module"
        if os.path.exists(GLUSTERFS_MODULE_FILE):
            os.remove(GLUSTERFS_MODULE_FILE)
        pkgs = self.get_oracle_glusterfs8_pkgs()
        if not pkgs:
            api.current_logger().info('No Oracle GlusterFS 8 packages found')
            return

        oracle_gluster8 = self.is_gluster_appstream_enabled()
        api.current_logger().info('Oracle GlusterFS 8 repo result: {}'.format(oracle_gluster8))
        if oracle_gluster8 is False:
            api.current_logger().warning('Oracle ol8_kvm_appstream is not enabled')
            self.produce_inhibitor(pkgs)
            return

        config = ConfigParser.RawConfigParser()
        config.add_section('glusterfs')
        config.set('glusterfs','name','glusterfs')
        config.set('glusterfs','stream','8')
        config.set('glusterfs','profiles','')
        config.set('glusterfs','state','enabled')

        with open(GLUSTERFS_MODULE_FILE, 'w') as configfile:
            config.write(configfile)

        self.produce_report()

    def get_oracle_glusterfs8_pkgs(self):
        """
        Find Oracle GlusterFS packages
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        glusterfs8_packages = []

        for pkg in rpms:
            if pkg.repository == 'ol7_gluster8':
                api.current_logger().info('Oracle GlusterFS 8 packages found {}'.format(pkg.name))
                glusterfs8_packages.append(pkg.name)

        if glusterfs8_packages:
            return glusterfs8_packages

    def is_gluster_appstream_enabled(self):
        leapp_enabled_repos = os.getenv('LEAPP_ENABLE_REPOS','')
        if (leapp_enabled_repos.find('ol8_gluster_appstream') != -1):
            api.current_logger().info('LEAPP_ENABLE_REPOS has ol8_gluster_appstream is enabled')
            return True
        else:
            return False

    def produce_report(self):
        summary = 'The GlusterFS 8 packages are installed. '
        create_report([
            reporting.Title('GlusterFS 8 is installed'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.LOW),
            reporting.Groups([reporting.Groups.FILESYSTEM])
        ])

    def produce_inhibitor(self,pkgs):
        summary = 'Upgrade process was inhibited as the following Oracle GlusterFS 8 packages have been detected, '
        summary += 'but Oracle GlusterFS 8 upgrade repository ol8_gluster_appstream has not been enabled.\n{}'.format('\n'.join(pkgs))
        create_report([
            reporting.Title('Oracle GlusterFS 8 packages detected, upgrade inhibited.'),
            reporting.Summary(summary),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])


