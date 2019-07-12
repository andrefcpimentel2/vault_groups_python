#!/usr/bin/env python

import hvac
import json
import requests

VAULT_ADDRESS = ""
VAULT_TOKEN = ""


client = hvac.Client(
    url=VAULT_ADDRESS,
    token=VAULT_TOKEN,
    )

def listEntities():
    list_response = client.secrets.identity.list_entities()
    # list_response = client.secrets.identity.list_entities_by_name() ## list by name
    entity_keys = list_response['data']['keys']
    print('The following entity IDs are currently configured: {keys}'.format(keys=entity_keys))

    for entity in entity_keys:
        read_response = client.secrets.identity.read_entity(
        entity_id=entity,
        )
        print (json.dumps(str(read_response), indent=4, sort_keys=True))
    return entity_keys


def createGroupByEntityID(entityID):
    ##fetches the name from the auth method
    entity_alias = getEntityAlias(entityID)

    ##Updates the entity with the alias name to better identification
    updateEntityName(entityID,entity_alias)

    #create group policy first
    createGroupPolicyByIdentity(entity_alias)

    group_name=entity_alias+'-group'
    group_policy=entity_alias+'-policy'

    client.secrets.identity.create_or_update_group_by_name(
        name=group_name,
        member_entity_ids=entityID,
        policies=group_policy,
    )

    #finally create the shared kv for the group
    try:
        createGroupSharedkv(entity_alias)
    except:
        print("path already in use -- skipping")



def createGroupSharedkv(entityID):

    mount_point=entityID+'-kv'

    client.sys.enable_secrets_engine(
    backend_type='kv',
    path=mount_point,
    )

def createGroupPolicyByIdentity(entity_alias):

    policy_name=entity_alias+"-policy"

    policy_template = """
    # Grant permissions on the group specific path
    # The region is specified in the group metadata
    path "%s-kv/*" {
        capabilities = [ "create", "update", "read", "delete", "list" ]
    }

    # Group member can update the group information
    path "identity/group/id/{{identity.groups.names.%s-group.id}}" {
    capabilities = [ "create", "update", "read", "delete", "list" ]
    }

    path "identity/*" {
    capabilities = [ "list" ]
    }

   

    """ % (entity_alias,entity_alias)

    client.sys.create_or_update_policy(
        name=policy_name,
        policy=policy_template,
    )

def getEntityAlias(entityID):

    read_response = client.secrets.identity.read_entity(
            entity_id=entityID,
    )
    print(read_response)
    if read_response['data']['aliases'][0]['mount_type'] == "oidc":
        name = read_response['data']['aliases'][0]['metadata']['email']
    else:
        name = read_response['data']['aliases'][0]['name']
    
    print('Name for entity ID {id} is: {name}'.format(id=entityID, name=name))
    return name

def updateEntityName(entityID,entity_alias):
    ##updates entity name using aliases
    client.secrets.identity.update_entity(
        entity_id=entityID,
        name=entity_alias,
    )

def main():
    entity_keys = listEntities()

    for entity in entity_keys:
        listEntities()
        createGroupByEntityID(entity)



if __name__ == '__main__':
    main()