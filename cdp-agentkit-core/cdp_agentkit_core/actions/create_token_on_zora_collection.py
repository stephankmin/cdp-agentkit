from collections.abc import Callable

from cdp import Wallet
from pydantic import BaseModel, Field

from cdp_agentkit_core.actions import CdpAction
from cdp_agentkit_core.actions.utils import make_image_token_metadata

CREATE_TOKEN_ON_ZORA_COLLECTION_PROMPT = """
This tool will create a new token on a Zora NFT collection. It takes the collection address, the token name,
the token description, the file path of the token image, and the max supply.
"""

class CreateTokenOnZoraCollectionInput(BaseModel):
    """Input argument schema for create token on Zora collection action."""

    collection_address: str = Field(
        ...,
        description="The address of the Zora NFT collection",
    )
    name: str = Field(
        ...,
        description="The name of the token",
    )
    description: str = Field(
        ...,
        description="The description of the token",
    )
    image_path: str = Field(
        ...,
        description="The file path of the token image",
    )
    max_supply: int = Field(
        ...,
        description="The max supply of the token",
    )


def create_token_on_zora_collection(wallet: Wallet, collection_address: str, name: str, description: str, image_path: str, max_supply: int) -> str:
    """
    Create a new token on a Zora ERC-1155 collection.

    Args:
        collection_address (str): The address of the Zora NFT collection
        name (str): The name of the token
        description (str): The description of the token
        image_path (str): The file path of the token image
        max_supply (int): The max supply of the token

    Returns:
        str: A message confirming the token creation with details
    """
    print("Pinning image to IPFS...")
    token_uri = make_image_token_metadata(name, description, image_path)
                    
    try:
        print("Creating new token on Zora collection...")
        invocation = agent_wallet.invoke_contract(
            contract_address=collection_address,
            abi=zora_creator_1155_impl_abi,
            method="setupNewToken",
            args={
                "newURI": token_uri,
                "maxSupply": max_supply
            })
        invocation.wait()
    except Exception as e:
        return f"Error setting up new token on Zora collection: {str(e)}"

    return f"New token setup on Zora collection successfully. Tx hash: \
    {invocation.transaction_link}"