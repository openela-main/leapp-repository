import os
import re

import leapp.libraries.common.config as ipu_config
from leapp.libraries.common.mounting import LoopMount, MountError
from leapp.libraries.stdlib import api, CalledProcessError, run
from leapp.models import CustomTargetRepository, TargetOSInstallationImage

def determine_ol_version_from_iso_mountpoint(iso_mountpoint):
    media_repo = os.path.join(iso_mountpoint, 'media.repo')
    determined_ol_ver = ''
    with open(media_repo) as f:
        for line in f:
            if 'name=Oracle Linux' in line:
                for each in line:
                    if determined_ol_ver != '':
                        break
                    try:
                        int(each)
                        determined_ol_ver = each
                        break
                    except:
                        pass
                return determined_ol_ver
        if not media_repo:
            return ''  # We did not determine anything
    return determined_ol_ver

def inform_ipu_about_request_to_use_target_iso():
    target_iso_path = ipu_config.get_env('LEAPP_TARGET_ISO')
    if not target_iso_path:
        return

    iso_mountpoint = '/iso'

    if not os.path.exists(target_iso_path):
        # If the path does not exists, do not attempt to mount it and let the upgrade be inhibited by the check actor
        api.produce(TargetOSInstallationImage(path=target_iso_path,
                                              repositories=[],
                                              mountpoint=iso_mountpoint,
                                              was_mounted_successfully=False))
        return

    # Mount the given ISO, extract the available repositories and determine provided RHEL version
    iso_scan_mountpoint = '/var/lib/leapp/iso_scan_mountpoint'
    try:
        with LoopMount(source=target_iso_path, target=iso_scan_mountpoint):
            required_repositories = ('BaseOS', 'AppStream')

            # Check what required repositories are present in the root of the ISO
            iso_contents = os.listdir(iso_scan_mountpoint)
            present_repositories = [req_repo for req_repo in required_repositories if req_repo in iso_contents]

            # Create custom repository information about the repositories found in the root of the ISO
            iso_repos = []
            for repo_dir in present_repositories:
                baseurl = 'file://' + os.path.join(iso_mountpoint, repo_dir)
                iso_repo = CustomTargetRepository(name=repo_dir, baseurl=baseurl, repoid=repo_dir)
                api.produce(iso_repo)
                iso_repos.append(iso_repo)

            ol_version = determine_ol_version_from_iso_mountpoint(iso_scan_mountpoint)

            api.produce(TargetOSInstallationImage(path=target_iso_path,
                                                  repositories=iso_repos,
                                                  mountpoint=iso_mountpoint,
                                                  ol_version=ol_version,
                                                  was_mounted_successfully=True))
    except MountError:
        # Do not analyze the situation any further as ISO checks will be done by another actor
        iso_mountpoint = '/iso'
        api.produce(TargetOSInstallationImage(path=target_iso_path,
                                              repositories=[],
                                              mountpoint=iso_mountpoint,
                                              was_mounted_successfully=False))
