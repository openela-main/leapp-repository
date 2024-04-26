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

class RDMAUpgradeCheck(Actor):
    """
    Report if RDMA package is present, and if it is, add libfabric to to_remove
    """

    name = 'RDMA_upgrade_check'
    consumes = (InstalledRPM)
    produces = (RpmTransactionTasks)
    tags = (IPUWorkflowTag, FactsPhaseTag)

    def process(self):
        if not architecture.matches_architecture(architecture.ARCH_X86_64):
            return

        has_rdma_release = has_package(InstalledRPM, 'oracle-rdma-release')
        has_libibverbs = has_package(InstalledRPM, 'libibverbs')
        if not has_rdma_release or not has_libibverbs:    
	        return
        
        to_remove = ['libfabric']

        self.produce(RpmTransactionTasks(to_remove=to_remove))
