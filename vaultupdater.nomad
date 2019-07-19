job "vaultupdater" {
  datacenters = ["dc1","eu-west-2"]
  type = "batch"

  group "vaultEnityUpdater" {
    count = 1
    
  reschedule {
      attempts       = 1
      interval       = "1m"
      delay          = "30s"
      delay_function = "exponential"
      max_delay      = "120s"
      unlimited      = false
    }

     task "GroupEntityRenamer" {
      driver = "exec"
      vault {
  policies = ["superuser"]
}


      env {
        VAULT_ADDR = "https://active.vault.service.consul:8200"
      }

      artifact {
           source   = "git::https://github.com/GuyBarros/vault_groups_python.git"
           destination = "local/repo/1/"
           
         }

      config {
        command = "local/repo/1/run.sh"
      }

      resources {
        network {
          port "proxy" {}
        }
      }
    } 

  }

}