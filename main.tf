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
    environment = "staging"
  }
}
