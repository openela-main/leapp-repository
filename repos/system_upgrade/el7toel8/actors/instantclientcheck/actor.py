import sys
from leapp.libraries.common import rpms
from leapp.models import InstalledRPM
from leapp import reporting
from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.reporting import create_report, Report
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag

issueList = []

class InstantClientCheck(Actor):
    """
    Checks with user that they understand Instantclient packages pre-version 21 will not be upgraded and must be manually installed following upgrade, as they are not supported.
    """

    name = 'instantclient_check'
    consumes = ()
    produces = (Report,)
    tags = (IPUWorkflowTag, ChecksPhaseTag)
    dialogs = (
        Dialog(
            scope='instant_client_install',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Please confirm that you understand that '
                          'instantclient packages from currently installed versions '
                          'are not supported by leapp and will not be '
                          'upgraded.',
                    description='instantclient is installed from '
                                'unsupported version. Please uninstall '
                                'instantclient and manually reinstall following upgrade. Please confirm that you acknowledge installed instantclient '
                                'packages are not supported by leapp.',
                    reason='currently installed instantclient packages are not '
                           'supported by leapp and will not be automatically upgraded '
                           'or removed.'
                ),
            )
        ),
    )


    def process(self):
        global issuelist
        output = rpms.get_installed_rpms()
        result = InstalledRPM()
        with open('instantclient.config','r') as file:
            issuePackages = file.read().splitlines()
        for entry in output:            
            if not entry:
                continue
            name, version, release, epoch, packager, arch, pgpsig = entry.split('|')
            for item in issuePackages:
                if item in name:
                   issueList.append(name)
        arglist = sys.argv
        for arg in arglist:
            if 'ol8_oracle_instantclient' == arg:
                self.produce_arg_inhibitor()
        if issueList:
            confirmations =["instant_client_install"]
            for confirmation in confirmations:
                result = self.confirm(confirmation)
                if result:
                    self.produce_report()
                elif result is False:
                    # user specifically chose to disagree with instantclient warning
                    self.produce_inhibitor(confirmation)
        else:
            return

    def confirm(self, confirmations):
        questions = {
            'instant_client_install': self.dialogs[0]
        }

        return self.get_answers(questions[confirmations]).get('confirm')

    def produce_report(self):
        issueString = []
        for issue in issueList:
            issueString.append(issue.encode('ascii','ignore'))
        create_report([
            reporting.Title('installed instantclient packages not supported by Leapp.'),
            reporting.Summary(
                'User must confirm that they acknowledge installed instantclient packages '
                'are not supported by Leapp and will not be upgraded or removed. User is recommended to manually reinstall instantclient post-upgrade. '
                'Packages installed are as follows: ' + ", ".join(issueString)),
            reporting.Severity(reporting.Severity.MEDIUM),
            reporting.Groups([
                    reporting.Groups.REPOSITORY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Remediation(hint='Please acknowledge that installed Instantclient packages are not supported and will not be upgraded.')
        ])

    def produce_arg_inhibitor(self):
        create_report([
            reporting.Title(
                'Upgrade process was interrupted because user has attempted to enable unsupported instantclient repository.'),
            reporting.Summary(
                'Instantclient upgrade is not supported by Leapp. The ol8_oracle_instantclient repository should not be enabled '
                'when attempting to upgrade the system.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.REPOSITORY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(
                hint='Please rerun upgrade process without providing --enablerepo ol8_oracle_instantclient argument.')
        ])

    def produce_inhibitor(self, reason):
        if reason == "instant_client_install":
            reported = "User not acknowledged instantclient upgrade unsupported"
        create_report([
            reporting.Title(
                'Upgrade process was interrupted because user did not confirm  '
                'they acknowledge instantclient incompatibility, specifically - '
                '{0}.'.format(reported)),
            reporting.Summary(
                ' Upgrading instance requires user to acknowledge '
                'that instantclient packages are unsupported during the upgrade process and will not be removed or upgraded.'
                'Also user needs to confirm that they understand that instantclient package replacement needs to be performed manually '
                'after upgrade is finished. '
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.REPOSITORY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(
                hint='Confirm that you understand that instantclient packages are not supported by Leapp and will not be upgraded or removed.'.format(module))])
