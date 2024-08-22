from leapp.libraries.common.config import get_env
from leapp import reporting
from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.reporting import create_report, Report
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class OSMSCheck(Actor):
    """
    Check with user that they understand limitations of manage instance upgrade.

    If admin does not confirm that they understand pre-requisites and actions needed
    to perform post-upgrade upgrade will be stalled.
    """
    name = 'osms_check'
    consumes = ()
    produces = (Report,)
    tags = (IPUWorkflowTag, ChecksPhaseTag)
    dialogs = (
        Dialog(
            scope='oracle_cloud_agent_check',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Can you confirm that no package updates will be installed '
                          'during system upgrade using OS Management Service ? '
                          'If no, the upgrade process will be interrupted.',
                    description='oracle-cloud-agent is running and system upgrade '
                                'is started as upgrade of managed instance. '
                                'Stop oracle-cloud-agent or confirm that no updates will be installed.',
                    reason='Installing any package during the managed instance upgrade '
                           'may leave the system in non-upgradeable state or '
                           'break the upgrade itself.'
                ),
            )
        ),
        Dialog(
            scope='osms_post_check',
            reason='Confirmation',
            components=(
                BooleanComponent(
                    key='confirm',
                    label='Do you confirm that you will need to remove all existing software sources '
                          'after the upgrade using OCI compute console. '
                          'Also after completed upgrade you will need to add OL9 BaseOS Latest software source '
                          'and your own software sources if needed',
                    description='Replacement of software sources on manage instance '
                                'does not happen automatically.'
                                ' User needs to confirm they understand'
                                ' that some actions will be needed post-upgrade',
                    reason='Upgrading managed instance if additional steps are not performed '
                           'may end up in upgraded instance not being functional.'
                ),
            )
        ),
    )

    def process(self):
        osms_enabled = get_env('LEAPP_OSMS')
        if osms_enabled:
            confirmations = ["oracle_cloud_agent_check", "osms_post_check"]
            for confirmation in confirmations:
                result = self.confirm(confirmation)
                if result and confirmation == "oracle_cloud_agent_check":
                    self.produce_report_cloud_agent()
                elif result and confirmation == "osms_post_check":
                    self.produce_report_osms()
                elif result is False:
                    # user specifically chose to disagree with auto disablement
                    self.produce_inhibitor(confirmation)
        else:
            return

    def confirm(self, confirmations):
        questions = {
            'oracle_cloud_agent_check': self.dialogs[0],
            'osms_post_check': self.dialogs[1]
        }

        return self.get_answers(questions[confirmations]).get('confirm')

    def produce_report_osms(self):
        create_report([
            reporting.Title('Managed instance upgrade requires user to accept certain requirements for used Software Source.'),
            reporting.Summary(
                'User needs to confirm that they will remove old Software Sources after the upgrade '
                'and will enable OL9 BaseOS Latest software source and their own software sources'

            ),
            reporting.Severity(reporting.Severity.MEDIUM),
            reporting.Groups([
                    reporting.Groups.AUTHENTICATION,
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Remediation(hint='Do not forget to ensure accepted requirements are met'),
            reporting.RelatedResource('package', 'oracle-cloud-agent')
        ])

    def produce_report_cloud_agent(self):
        create_report([
            reporting.Title('Managed instance upgrade requires user to accept certain requirements for OS Management Service'),
            reporting.Summary(
                'When managed instance is being upgraded, user needs to ensure that'
                ' no packages will be installed/removed/updated via OS Management Service during the upgrade'
                ' itself. '

            ),
            reporting.Severity(reporting.Severity.MEDIUM),
            reporting.Groups([
                    reporting.Groups.AUTHENTICATION,
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Remediation(hint='Do not forget to ensure accepted requirements are met'),
            reporting.RelatedResource('package', 'oracle-cloud-agent')
        ])

    def produce_inhibitor(self, reason):
        if reason == "oracle_cloud_agent_check":
            reported = "Not installing packages using OS Management Service during the upgrade process"
        elif reason == "osms_post_check":
            reported = "User will need to manually replace Software sources after upgrade"
        create_report([
            reporting.Title(
                'Upgrade process was interrupted because user did not confirm  '
                'he complies with necessary pre or post steps, specifically - '
                '{0}.'.format(reported)),
            reporting.Summary(
                ' Upgrading managed instance requires user to ensure'
                'that packages are not installed using OS Management Service during the upgrade process.'
                'Also user needs to confirm that they understand that Software sources replacement needs to be performed manually '
                'after upgrade is finished. '
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([
                    reporting.Groups.AUTHENTICATION,
                    reporting.Groups.SECURITY,
                    reporting.Groups.TOOLS
            ]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(
                hint='Confirm that you understand requirements to perform manage instance upgrade.'.format(module)),
            reporting.RelatedResource('package', 'oracle-cloud-agent')
        ])
