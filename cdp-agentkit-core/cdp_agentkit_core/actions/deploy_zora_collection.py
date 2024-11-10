from collections.abc import Callable

from cdp import Wallet
from pydantic import BaseModel, Field

from cdp_agentkit_core.actions import CdpAction

DEPLOY_ZORA_COLLECTION_PROMPT = """
This tool will deploy a Zora NFT collection contract onchain from the wallet. It takes the name of the NFT collection, the contract URI
for the contract-level metadata, the royalty mint schedule (every nth token will be minted to the creator), the royalty BPS, the royalty recipient,
and the collection admin as inputs.
"""


class DeployZoraCollectionInput(BaseModel):
    """Input argument schema for deploy Zora collection action."""

    name: str = Field(
        ...,
        description="The name of the Zora NFT collection",
    )
    contract_uri: str = Field(
        ...,
        description="The contract URI for the contract-level metadata",
    )
    royalty_mint_schedule: int = Field(
        ...,
        description="Every nth token which will go to the royalty recipient",
    )
    royalty_bps: int = Field(
        ...,
        description="The royalty BPS",
    )
    royalty_recipient: str = Field(
        ...,
        description="The address of the royalty recipient",
    )
    default_admin: str = Field(
        ...,
        description="The address of the default admin",
    )

def create_zora_collection(name, contract_uri, royalty_mint_schedule,
                           royalty_bps, royalty_recipient, default_admin):
    """
    Create a new Zora ERC-1155 collection.

    Args:
        name (str): The name of the collection
        contract_uri (str): The contractURI for the collection
        royalty_mint_schedule (int): Every nth token which will go to the royalty 
                                     recipient
        royalty_bps (int): The royalty BPS
        royalty_recipient (str): The address of the royalty recipient
        default_admin (str): The address of the default admin

    Returns:
        str: A message confirming the token creation with details
    """
    try:
        invocation = agent_wallet.invoke_contract(
            contract_address=ZORA_CREATOR_1155_FACTORY,
            abi=zora_factory_abi,
            method="createContract",
            args={
                "newContractURI":
                contract_uri,
                "name":
                name,
                "defaultRoyaltyConfiguration":
                [royalty_mint_schedule, royalty_bps, royalty_recipient],
                "defaultAdmin":
                default_admin,
                "setupActions": []
            })
        invocation.wait()
    except Exception as e:
        return f"Error deploying Zora collection: {str(e)}"

    return f"Collection {name} deployed successfully. Tx hash: \
    {invocation.transaction_link}"


class DeployZoraCollectionAction(CdpAction):
    """Deploy Zora collection action."""

    name: str = "deploy_zora_collection"
    description: str = DEPLOY_ZORA_COLLECTION_PROMPT
    args_schema: type[BaseModel] | None = DeployZoraCollectionInput
    func: Callable[..., str] = create_zora_collection