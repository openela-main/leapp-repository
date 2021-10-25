from leapp.actors import Actor
from leapp.dialogs import Dialog
from leapp.dialogs.components import BooleanComponent
from leapp.tags import ApplicationsPhaseTag, IPUWorkflowTag
from leapp import reporting
from leapp.reporting import Report, create_report
from leapp.libraries.stdlib import api
from leapp.libraries.common.config import architecture
import os
import re


class PostOracleKVMEmulatorFix(Actor):
    """
    Fix Oracle KVM emulator in VM xml files

    """

    name = 'post_oracle_kvm_emulator_fix'
    consumes = ()
    produces = (Report,)
    tags = (ApplicationsPhaseTag, IPUWorkflowTag)

    def process(self):
        VIRT_MODULE_FILE="/etc/dnf/modules.d/virt.module"

        if os.path.exists(VIRT_MODULE_FILE):
            for line in open(VIRT_MODULE_FILE, 'r'):
                if re.search("stream = kvm_utils2", line):
                    self.check_kvm_emulator()

    def check_kvm_emulator(self):
        """
        Check emulator in VM xml files
        """
        KVM_VMCONFIG_XML_DIR="/etc/libvirt/qemu"
        if not os.path.exists(KVM_VMCONFIG_XML_DIR):
            return

        if architecture.matches_architecture(architecture.ARCH_ARM64):
            KVM_EMULATOR="<emulator>/usr/bin/qemu-system-aarch64</emulator>"
        else:
            KVM_EMULATOR="<emulator>/usr/bin/qemu-system-x86_64</emulator>"

        found=0
        for file in os.listdir(KVM_VMCONFIG_XML_DIR):
            if file.endswith(".xml"):
                for line in open(os.path.join(KVM_VMCONFIG_XML_DIR,file), 'r'):
                    if re.search(KVM_EMULATOR, line):
                        api.current_logger().info('Found Oracle KVM OL7 emulator in {}'.format(file))
                        self.create_softlink()
                        return

    def create_softlink(self):
        """
        Create workaround softlink for old emulator path
        """
        OL8_KVM_EMULATOR="/usr/libexec/qemu-kvm"
        if architecture.matches_architecture(architecture.ARCH_ARM64):
            OL7_KVM_EMULATOR="/usr/bin/qemu-system-aarch64"
        else:
            OL7_KVM_EMULATOR="/usr/bin/qemu-system-x86_64"
        if os.path.exists(OL7_KVM_EMULATOR):
            api.current_logger().error('Unable to create softlink, file exists {}'.format(OL7_KVM_EMULATOR))
            return
        if os.path.exists(OL8_KVM_EMULATOR):
            os.symlink(OL8_KVM_EMULATOR,OL7_KVM_EMULATOR)
            api.current_logger().info('Created symlink {}'.format(OL7_KVM_EMULATOR))
        else:
            api.current_logger().error('Unable to create softlink, file does not exist {}'.format(OL8_KVM_EMULATOR))
