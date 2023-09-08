from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.tags import FinalizationPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os


class PostLicenseFix(Actor):
    """
    Prevent license screen from constantly appearing on boot

    """

    name = 'post_license_fix'
    consumes = ()
    produces = (Report,)
    tags = (FinalizationPhaseTag.After, IPUWorkflowTag)

    def process(self):
        import os
        if os.path.exists("/etc/systemd/system/multi-user.target.wants/initial-setup-reconfiguration.service"):
            os.remove("/etc/systemd/system/multi-user.target.wants/initial-setup-reconfiguration.service")
        
        if os.path.exists("/etc/systemd/system/graphical.target.wants/initial-setup-reconfiguration.service"):
            os.remove("/etc/systemd/system/graphical.target.wants/initial-setup-reconfiguration.service")


