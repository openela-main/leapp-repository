from leapp.actors import Actor
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.libraries.stdlib import run
from leapp.tags import FirstBootPhaseTag, IPUWorkflowTag


class PostUpdateEtcSysconfigKernel(Actor):
    """
    Update /etc/sysconfig/kernel file after upgrade.

    Ensure DEFAULTKERNEL is set to correct default boot kernel
    """

    name = 'post_update_etc_sysconfig_kernel'
    consumes = ()
    produces = ()
    tags = (FirstBootPhaseTag, IPUWorkflowTag)

    def process(self):
        try:
            current_default_kernel = stdlib.run(['grubby', '--default-kernel'])['stdout'].strip()
        except (OSError, stdlib.CalledProcessError):
            api.current_logger().warning('Failed to query grubby for default kernel', exc_info=True)
            return
        
        if (current_default_kernel.find('uek') != -1):
            ''' Update DEFAULTKERNEL entry at provided config file '''
            run(['/bin/sed',
                 '-i',
                 's/^DEFAULTKERNEL=kernel.*/DEFAULTKERNEL=kernel-uek/g',
                 '/etc/sysconfig/kernel'])
        else:
            ''' Update DEFAULTKERNEL entry at provided config file '''
            run(['/bin/sed',
                 '-i',
                 's/^DEFAULTKERNEL=kernel.*/DEFAULTKERNEL=kernel-core/g',
                 '/etc/sysconfig/kernel'])
            
