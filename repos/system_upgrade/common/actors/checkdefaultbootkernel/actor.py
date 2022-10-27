from leapp.actors import Actor
from leapp.libraries import stdlib
from leapp.libraries.stdlib import api
from leapp.models import DefaultBootKernelInfo, Report, ActiveKernelModulesFacts
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report


class CheckDefaultBootKernel(Actor):
    """
    Check the default boot kernel, set to UEK if BTRFS is detected.

    BRTFS is supported only in the UEK kernel in OL9. BTRFS is no
    longer available or supported in the RHCK kernel.
    """

    name = "CheckDefaultBootKernel"
    consumes = (ActiveKernelModulesFacts,)
    produces = (Report, DefaultBootKernelInfo)
    tags = (ChecksPhaseTag, IPUWorkflowTag,)

    def process(self):
        try:
            current_default_kernel = stdlib.run(['grubby', '--default-kernel'])['stdout'].strip()
        except (OSError, stdlib.CalledProcessError):
            api.current_logger().warning('Failed to query grubby for default kernel', exc_info=True)
            self.produce_inhibitor()
            return

        btrfs_used = 'False'
        for fact in self.consume(ActiveKernelModulesFacts):
            for active_module in fact.kernel_modules:
                if active_module.filename == 'btrfs':
                    btrfs_used = 'True'
                    break

        if (current_default_kernel.find('uek') != -1):
            api.current_logger().info('Kernel UEK detected as default boot kernel')
            api.produce(DefaultBootKernelInfo(kernel_type='kernel-uek'))
            self.produce_report('UEK')
        else:
            if btrfs_used == 'False':
                api.current_logger().info('Kernel RHCK detected as default boot kernel')
                api.produce(DefaultBootKernelInfo(kernel_type='kernel'))
                self.produce_report('RHCK')
            else:
                api.current_logger().info('BTRFS detected, setting UEK as OL9 default boot kernel')
                api.produce(DefaultBootKernelInfo(kernel_type='kernel-uek'))
                self.produce_report('UEK')

    def produce_report(self, kernel_type):
        create_report([
            reporting.Title('Default Boot Kernel'),
            reporting.Summary(
                'Setting default boot kernel in OL9 to {}'.format(kernel_type)
            ),
            reporting.Severity(reporting.Severity.MEDIUM),
            reporting.Groups([reporting.Groups.KERNEL])
        ])

    def produce_inhibitor(self):
        create_report([
            reporting.Title('Default Boot Kernel'),
            reporting.Summary(
                'Unable to detect default boot kernel, is grubby installed.'
            ),
            reporting.Severity(reporting.Severity.HIGH),
            reporting.Groups([reporting.Groups.KERNEL]),
            reporting.Groups([reporting.Groups.INHIBITOR]),
            reporting.Remediation(hint='Check if grubby is installed.')
        ])



