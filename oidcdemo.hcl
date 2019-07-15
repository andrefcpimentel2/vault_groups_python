path "secrets/*" {
  capabilities = ["read", "list"] 
}
  # Group member can update the group information
  path "identity/*" {
    capabilities = ["list"]
}
