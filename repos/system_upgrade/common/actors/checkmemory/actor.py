from leapp.actors import Actor
from leapp.libraries.actor import checkmemory
from leapp.models import MemoryInfo, Report
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class CheckMemory(Actor):
    """
    The actor check the size of RAM against OL8 minimal hardware requirements

    Using the following resource: https://docs.oracle.com/en/operating-systems/oracle-linux/9/install/
    """

    name = 'checkmemory'
    consumes = (MemoryInfo,)
    produces = (Report,)
    tags = (ChecksPhaseTag, IPUWorkflowTag)

    def process(self):
        checkmemory.process()
