"""
This file is part of nucypher.

nucypher is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

nucypher is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with nucypher.  If not, see <https://www.gnu.org/licenses/>.
"""


import os
import pytest
from nucypher.blockchain.eth.deployers import UserEscrowDeployer, UserEscrowProxyDeployer


@pytest.fixture(scope='function')
def user_escrow_proxy(agency):
    token_agent, staking_agent, policy_agent = agency
    testerchain = policy_agent.blockchain
    deployer = testerchain.etherbase_account

    escrow_proxy_deployer = UserEscrowProxyDeployer(deployer_address=deployer)

    _escrow_proxy_deployments_txhashes = escrow_proxy_deployer.deploy(secret_hash=os.urandom(32))
    testerchain.time_travel(seconds=120)
    yield escrow_proxy_deployer.contract_address
    testerchain.registry.clear()
    testerchain.disconnect()


@pytest.mark.usefixtures('agency')
def test_user_escrow_deployer(agency, testerchain):
    deployer = testerchain.etherbase_account

    escrow_proxy_deployer = UserEscrowProxyDeployer(deployer_address=deployer, blockchain=testerchain)

    _escrow_proxy_deployments_txhashes = escrow_proxy_deployer.deploy(secret_hash=os.urandom(32))

    deployer = UserEscrowDeployer(deployer_address=deployer, blockchain=testerchain)

    deployment_txhashes = deployer.deploy()

    for title, txhash in deployment_txhashes.items():
        receipt = testerchain.wait_for_receipt(txhash=txhash)
        assert receipt['status'] == 1, "Transaction Rejected {}:{}".format(title, txhash)


@pytest.mark.slow()
@pytest.mark.usefixtures('user_escrow_proxy', 'three_agents')
@pytest.mark.skip(reason="Blocked by issue #1102")
def test_deploy_multiple(testerchain):
    deployer = testerchain.etherbase_account

    number_of_deployments = 100
    for index in range(number_of_deployments):
        deployer = UserEscrowDeployer(deployer_address=deployer, blockchain=testerchain)

        deployment_txhashes = deployer.deploy()

        for title, txhash in deployment_txhashes.items():
            receipt = testerchain.wait_for_receipt(txhash=txhash)
            assert receipt['status'] == 1, "Transaction Rejected {}:{}".format(title, txhash)

        # simulates passage of time / blocks
        if index % 15 == 0:
            testerchain.w3.eth.web3.testing.mine(1)
            testerchain.time_travel(seconds=5)
