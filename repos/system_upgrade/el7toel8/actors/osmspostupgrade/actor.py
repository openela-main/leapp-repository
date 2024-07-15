import os
import errno
from leapp.libraries.common.config import get_env

from leapp.actors import Actor
from leapp.libraries.stdlib import run
from leapp.reporting import Report, create_report
from leapp import reporting
from leapp.tags import FinalizationPhaseTag, IPUWorkflowTag


class OSMSPostUpgrade(Actor):
    """
    Perform additional steps for OSMS upgrade. At this moment performed actions are:
    * Python3 alternatives set: alternatives --set python /usr/bin/python3

    """

    name = 'osmspostupgrade'
    consumes = ()
    produces = (Report,)
    tags = (FinalizationPhaseTag, IPUWorkflowTag)

    def process(self):
        actions = "Python3 alternatives set \n"
        if get_env('LEAPP_OSMS') == 1:
            run(['alternatives', '--set', 'python', '/usr/bin/python3'])
            create_report([
                reporting.Title('OSMS post-upgrade actions performed'),
                reporting.Summary(
                    'At this moment performed actions are: "{}"'.format(actions)),
                reporting.Groups([reporting.Groups.UPGRADE_PROCESS]),
            ])
        else:
            return

