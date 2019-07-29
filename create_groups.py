#!/usr/bin/env python

import hvac
import json
import requests
import os

VAULT_ADDRESS =  os.environ.get('VAULT_ADDR', None)
VAULT_TOKEN =  os.environ.get('VAULT_TOKEN', None)


client = hvac.Client(
    url=VAULT_ADDRESS,
    token=VAULT_TOKEN,
    verify=False,
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

    ##fetches the mount point for the Entity alias
    mount_accessor = getEntityAliasMountAccessor(entityID)
    ##Updates the entity alias with the alias name to better identification
    try:
        updateEntityAliasName(entityID,entity_alias,mount_accessor)
    except Exception as e: print("Skipping: {e} ".format(e=e))
  
    group_name=entity_alias+'-group'
    group_policy=entity_alias+'-policy'

    #finally create the shared kv for the group
    try:
        createGroupSharedkv(entity_alias)
    except Exception as e: print("Skipping: {e} ".format(e=e))

    #create group policy first

    if checkGroupExists(group_name):
        print ("Group Exists -- Skipping")
    else:    
        createGroupPolicyByIdentity(entity_alias, group_policy)
        #Finally, creates the group
        print('creating group {group_name} for entity {entityID} and policies {group_policy}'.format(group_name=group_name,entityID=entityID,group_policy=group_policy))
        try:
            client.secrets.identity.create_or_update_group_by_name(
                name=group_name,
                member_entity_ids=entityID,
                policies=group_policy,
            )
        except Exception as e: print("Skipping: {e} ".format(e=e))

def checkGroupExists(group_name):
    try:
        list_response = client.secrets.identity.list_groups_by_name()
        group_keys = list_response['data']['keys']
    
        if group_name in group_keys:
            return True
    except Exception as e: print("Skipping: {e} ".format(e=e))
    return False
    
#Creates a KV for the user group
def createGroupSharedkv(entityID):

    mount_point=entityID+'-kv'

    client.sys.enable_secrets_engine(
    backend_type='kv',
    path=mount_point,
    )
    print('mounted kv at mountpath {name}'.format(name=mount_point))

#Creates group policy - only user has access to kv and group info
def createGroupPolicyByIdentity(entity_alias, group_policy):

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
        name=group_policy,
        policy=policy_template,
    )
    print('Created group policy for entity {name}'.format(name=entity_alias))

#Gets Entity alias as set on OIDC metadata or on Github name
def getEntityAlias(entityID):

    read_response = client.secrets.identity.read_entity(
            entity_id=entityID,
    )

    if read_response['data']['aliases'][0]['mount_type'] == "oidc":
        name = read_response['data']['aliases'][0]['metadata']['name']
    elif read_response['data']['aliases'][0]['mount_type'] == "github":
        name = read_response['data']['aliases'][0]['name']
    
    print('Name for entity ID {id} is: {name}'.format(id=entityID, name=name))
    return name

#Gets mount accessor for managing the Entity Alias (mandatory)
def getEntityAliasMountAccessor(entityID):

    read_response = client.secrets.identity.read_entity(
            entity_id=entityID,
    )
 
    mount_accessor = read_response['data']['aliases'][0]['mount_accessor']
    
    print('Mount accessor for entity ID {id} is: {mount_accessor}'.format(id=entityID, mount_accessor=mount_accessor))
    return mount_accessor

#updates entity name using aliases
def updateEntityName(entityID,entity_alias):
    
    client.secrets.identity.update_entity(
        entity_id=entityID,
        name=entity_alias,
    )
    print('Updated entity {id} with {name}'.format(id=entityID, name=entity_alias) )

##updates entity alias name using metadaa/alias name
def updateEntityAliasName(entityID,entity_alias,mount_accessor):
    
    entity_alias_name = entity_alias+'-alias'
    client.secrets.identity.create_or_update_entity_alias(
        canonical_id=entityID,
        name=entity_alias_name,
        mount_accessor=mount_accessor
    )
    print('Updated alias {id} with {name}'.format(id=entityID, name=entity_alias_name) )

#Main gets list of entities and creates groups/policies/kv for each entity
def main():
    entity_keys = listEntities()

    for entity in entity_keys:
        createGroupByEntityID(entity)

if __name__ == '__main__':
    main()
