from leapp.models import Model, fields
from leapp.topics import SystemFactsTopic


class DefaultBootKernelInfo(Model):
    """
    The model represents information about the default boot kernel.

    """

    topic = SystemFactsTopic

    """
    This field is either kernel-uek for UEK or kernel for RHCK

    """

    kernel_type = fields.String()
