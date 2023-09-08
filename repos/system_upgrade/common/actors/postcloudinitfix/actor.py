from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.tags import FinalizationPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
import os


class PostCloudInitFix(Actor):
    """
    Remove the object cache in cloud-init that causes issus with OL8 python36

    """

    name = 'post_cloudinit_fix'
    consumes = ()
    produces = (Report,)
    tags = (FinalizationPhaseTag.After, IPUWorkflowTag)

    def process(self):
        import os
        if os.path.exists("/var/lib/cloud/instance/obj.pkl"):
            os.remove("/var/lib/cloud/instance/obj.pkl")


