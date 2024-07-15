import os

from leapp.actors import Actor
from leapp.libraries.common.config import architecture
from leapp.libraries.common.rpms import has_package
from leapp.libraries.stdlib import run
from leapp.models import (
    InstalledRPM,
    Module,
    RpmTransactionTasks,
)
from leapp.tags import FactsPhaseTag, IPUWorkflowTag

class OLCNEUpgradeCheck(Actor):
    """
    Report if oracle-olcne-release-el7 package is present, and if it is, add oracle-olcne-release-el8 to to_install
    """

    name = 'OLCNE_upgrade_check'
    consumes = (InstalledRPM)
    produces = (RpmTransactionTasks)
    tags = (IPUWorkflowTag, FactsPhaseTag)

    def process(self):
        if not architecture.matches_architecture(architecture.ARCH_X86_64):
            return

        has_olcne_release = has_package(InstalledRPM, 'oracle-olcne-release-el7')
        if not has_olcne_release:
	        return
        
        to_install = ['oracle-olcne-release-el8']

        self.produce(RpmTransactionTasks(to_install=to_install))
