terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.47.0"
    }
  }
}

provider "azurerm" {
  features {}
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
    image  = "jmorjsm/azure-table-storage-experiments"
    cpu    = "0.5"
    memory = "1.5"
    ports {
      port     = 443
      protocol = "TCP"
    }
  }

  tags = {
    environment = "testing"
  }
}