from leapp.actors import Actor
from leapp.models import DistributionSignedRPM
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
from leapp.exceptions import StopActorExecution, StopActorExecutionError
import warnings
import subprocess
import os
import sys
import rpm
try:
    import xmlrpclib
except ImportError:
    warnings.warn("No xmlrpclib available", ImportWarning)
import ssl


olm_client_packages = ['rhn-check','rhn-client-tools','rhn-setup']
olm_min_supported_version = "2.10"
olm_config_file='/etc/sysconfig/rhn/up2date'

class CheckOLM(Actor):
    """
    Check if connected to OLM and both client and server
    are version 2.10 or higher. If not inhibit the upgrade.

    """

    name = 'check_olm'
    consumes = (DistributionSignedRPM,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        olm_configured = self.is_olm_registered()
        if olm_configured is True:
            olm_clients_supported = self.check_olm_client_versions()
            if olm_clients_supported is False:
                self.produce_inhibitor()
            olm_server_supported = self.check_olm_server_version()
            if olm_server_supported is False:
                self.produce_inhibitor()
            else:
                self.produce_report()

    def is_olm_registered(self):
        """
        Is the client connected to an OLM server
        """
        try:
            ps = subprocess.Popen("yum repolist", shell=True, stdout=subprocess.PIPE)
            output = ps.stdout.read()
            ps.stdout.close()
            ps.wait()

            if (output.find('This system is receiving updates from Spacewalk server') != -1):
                api.current_logger().info('Detected system is connected to an OLM server.')
                return True
        except:
            api.current_logger().error('Unable to determine if system is receiving updates from OLM')
            raise StopActorExecutionError('Unable to determine if system is receiving updates from OLM')

    def check_olm_client_versions(self):
        for olm_pkg in olm_client_packages:
            pkgs = self.get_pkgs(olm_pkg)
            if not pkgs:
                api.current_logger().error('OLM configured, but client package {} not found'.format(olm_pkg))
                return False
            for pkg in pkgs:
                if rpm.labelCompare((None, pkg.version, None), (None, olm_min_supported_version, None)) < 0:
                    api.current_logger().error('OLM package {} version {} less than 2.10'.format(pkg.name,pkg.version))
                    return False
        return True

    def get_pkgs(self,pkg_name):
        """
        Get all installed packages of the given name signed by Oracle.
        """
        rpms = next(api.consume(DistributionSignedRPM), DistributionSignedRPM()).items
        return [pkg for pkg in rpms if pkg.name == pkg_name]

    def check_olm_server_version(self):
        f = open(olm_config_file,'r')

        lines = f.readlines()
        for line in lines:
            if line.startswith('serverURL='):
                api.current_logger().info('OLM Server URL {}'.format(line.split('=')[1]))
                SATELLITE_URL = line.split('=')[1].replace('XMLRPC','').strip() + 'rpc/api'
        f.close()

        if not SATELLITE_URL:
            api.current_logger().error('Unable to determine OLM serverURL in {}'.format(olm_config_file))
            raise StopActorExecutionError('Unable to determine OLM serverURL')

        try:
            client = xmlrpclib.Server(SATELLITE_URL, verbose=0, use_datetime=0, context=ssl._create_unverified_context())
            olm_server_version = client.api.systemVersion()
            if rpm.labelCompare((None, olm_server_version, None), (None, olm_min_supported_version, None)) < 0:
                api.current_logger().error('OLM package server version {} less than supported version 2.10'.format(olm_server_version))
                return False
        except:
            api.current_logger().error('Unable to determine OLM server version from {}'.format(SATELLITE_URL))
            raise StopActorExecutionError('Unable to determine OLM server version')
        return True

    def produce_report(self):
        create_report([
            reporting.Title('OLM version supported'),
            reporting.Summary(
                'OLM has been detected and runnnig supported version 2.10 or higher.'
            ),
            reporting.ExternalLink(
                title='Oracle Linux Manager 2.10',
                url='https://docs.oracle.com/en/operating-systems/oracle-linux-manager/2.10/admin/'
            ),
            reporting.Severity(reporting.Severity.HIGH)
        ])

    def produce_inhibitor(self):
        create_report([
            reporting.Title('OLM version unsupported.'),
            reporting.Summary(
                'Upgrade process was interrupted because OLM has been detected '
                'and running an unsupported version. Leapp upgrades for systems '
                'connected to OLM are supported for version 2.10 and higher only.'
            ),
            reporting.ExternalLink(
                title='Oracle Linux Manager 2.10',
                url='https://docs.oracle.com/en/operating-systems/oracle-linux-manager/2.10/admin/'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR])
        ])


