# vault_groups_python


## Create OIDC method

```
export VAULT_ADDR='<vault_address>'

vault login <root token>

vault auth enable oidc

vault write auth/oidc/config oidc_discovery_url="https://login.microsoftonline.com/<tenant id>/v2.0" oidc_client_id="<client id>" oidc_client_secret="<client secret>" default_role="oidcdemo"

echo 'path "secrets/*" {
  capabilities = ["read", "list"] 
}
  # Group member can list the identity information
  path "identity/*" {
    capabilities = ["list"]
}' > oidcdemo.hcl

vault policy write oidcdemo oidcdemo.hcl

vault write auth/oidc/role/oidcdemo bound_audiences="<client_id>" allowed_redirect_uris="<vault_address:default port>/ui/vault/auth/oidc/oidc/callback" allowed_redirect_uris="<vault_address:8250>/oidc/callback" user_claim="sub" policies="oidcdemo" claim_mappings={dysplayname=dysplayname,surname=surname,givenname=givenname,preferred_username=preferred_username,unique_name=unique_name,email=email,name=name}

```
