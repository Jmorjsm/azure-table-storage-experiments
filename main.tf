terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "3.47.0"
    }
  }
}

provider "azurerm" {
  resource "azurerm_resource_group" "example" {
  name     = "table-storage-experiments"
  location = "West US 2"
}

resource "azurerm_storage_account" "example" {
  name                     = "table-storage-experiments-storageaccount"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  tags = {
    environment = "staging"
  }
}
}