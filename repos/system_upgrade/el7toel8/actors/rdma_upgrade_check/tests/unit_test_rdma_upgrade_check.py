import os

from leapp.libraries.common.config import mock_configs
from leapp.models import (
    InstalledRPM,
    Module,
    RPM,
    RpmTransactionTasks,
    RDMAUpgradeCheck
)
from leapp.snactor.fixture import current_actor_context

RH_PACKAGER = 'Oracle America <https://github.com/oracle/oracle-linux>'


def fake_package(pkg_name):
    return RPM(name=pkg_name, version='0.1', release='1.sm01', epoch='1', packager=RH_PACKAGER, arch='noarch',
               pgpsig='RSA/SHA256, Mon 01 Jan 1970 00:00:00 AM -03, Key ID 199e2f91fd431d51')


RDMA_RPM = fake_package("oracle-rdma-release")
LIBIBVERBS_RPM = fake_package("libibverbs")

def test_no_rdma_package_present(current_actor_context):
    current_actor_context.feed(InstalledRPM(items=[]))
    current_actor_context.run(config_model=mock_configs.CONFIG)
    message = current_actor_context.consume(RDMAUpgradeCheck)
    assert not message


def test_rdma_package_present(current_actor_context):
    current_actor_context.feed(InstalledRPM(items=[RDMA_RPM]))
    current_actor_context.run(config_model=mock_configs.CONFIG)
    message = current_actor_context.consume(RDMAUpgradeCheck)[0]
    assert message.has_rdma-release


def test_libibverbs_package_present(current_actor_context):
    current_actor_context.feed(InstalledRPM(items=[LIBIBVERBS_RPM]))
    current_actor_context.run(config_model=mock_configs.CONFIG)
    message = current_actor_context.consume(RDMAUpgradeCheck)[0]
    assert message.has_libibverbs

def test_no_libibverbs_package_present(current_actor_context):
    current_actor_context.feed(InstalledRPM(items=[]))
    current_actor_context.run(config_model=mock_configs.CONFIG)
    message = current_actor_context.consume(RDMAUpgradeCheck)
    assert not message


def test_wrong_arch(current_actor_context):
    current_actor_context.feed(InstalledRPM(items=[RDMA_RPM]))
    current_actor_context.run(config_model=mock_configs.CONFIG_S390X)
    message = current_actor_context.consume(RDMAUpgradeCheck)
    assert not message
