terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.47.0"
    }
  }
   backend "azurerm" {
      resource_group_name  = "table-storage-experiments"
      storage_account_name = "jmorjsmtse"
      container_name       = "tfstate"
      key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

variable "GHCR_USERNAME" {
  type = string
}

variable "GHCR_PASSWORD" {
  type = string
}

resource "azurerm_resource_group" "table_storage_experiments" {
  name     = "table-storage-experiments"
  location = "West US 2"
}

resource "azurerm_storage_account" "table_storage_experiments" {
  name                     = "jmorjsmtse"
  resource_group_name      = azurerm_resource_group.table_storage_experiments.name
  location                 = azurerm_resource_group.table_storage_experiments.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  tags = {
    environment = "testing"
  }
}

resource "azurerm_container_group" "table_storage_experiments" {
  name                = "storage-experiment-continst"
  location            = azurerm_resource_group.table_storage_experiments.location
  resource_group_name = azurerm_resource_group.table_storage_experiments.name
  ip_address_type     = "Public"
  dns_name_label      = "tserunner"
  os_type             = "Linux"
  restart_policy      = "Never"

  container {
    name   = "storage-experiment"
    image  = "ghcr.io/jmorjsm/azure-table-storage-experiments:latest"
    cpu    = "0.5"
    memory = "1.5"
    ports {
      port     = 9998
      protocol = "UDP"
    }
    environment_variables = {
      "TABLE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.table_storage_experiments.primary_connection_string
    }
  }

  image_registry_credential {
    server   = "ghcr.io"
    username = var.GHCR_USERNAME
    password = var.GHCR_PASSWORD
  }

  tags = {
    environment = "testing"
  }
}
