from leapp import reporting
from leapp.actors import Actor
from leapp.libraries.common import rpms
from leapp.models import InstalledRPM
from leapp.tags import FactsPhaseTag, IPUWorkflowTag
from leapp.reporting import Report

class i686Inhibit(Actor):
    """
    Checks for problematic i686 rpms that will cause a dependency related failure on upgrade.
    """

    name = 'i686inhibit'
    consumes = ()
    produces = (Report,)
    tags = (IPUWorkflowTag, FactsPhaseTag)

    def process(self):
        output = rpms.get_installed_rpms()

        result = InstalledRPM()
        issuePackages = ["ibacm","usbguard","gobject-introspection-devel","fltk-devel","twolame-devel","opus-devel","mpdecimal-devel"]
        issueList = []
        for entry in output:
            entry = entry.strip()
            if not entry:
                continue
            name, version, release, epoch, packager, arch, pgpsig = entry.split('|')
            for item in issuePackages:
                if item in name:
                    if arch == "i686":
                       issueList.append(name + '.' + arch)
        if issueList:
            issueList = str(issueList).strip("[]")
            issueList = issueList.replace("'","")
            warnMsg = 'rpm(s) ' + issueList + ' for i686 architecture installed. This will cause dependency failure on upgrade.'
            self.log.warning(warnMsg)
            reporting.create_report(
                [
                    reporting.Title("Problematic i686 rpms installed"),
                    reporting.Summary(warnMsg),
                    reporting.Severity(reporting.Severity.HIGH),
                    reporting.Groups([reporting.Groups.REPOSITORY]),
                    reporting.Groups([reporting.Groups.INHIBITOR]),
                    reporting.Remediation(
                        hint=(
                            "Please run command #dnf remove for all conflicting packages before upgrade, e.g. #dnf remove " + issueList.replace(",","")
                        )
                    ),
                ]
            )

