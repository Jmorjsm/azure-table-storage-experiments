terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.54.0"
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

variable "RESULTS_API_ZIP_DEPLOY_FILE" {
  type = string
}

resource "azurerm_resource_group" "table_storage_experiments" {
  name     = "table-storage-experiments-results"
  location = "West US"
}

resource "azurerm_storage_account" "table_storage_experiments_results" {
  name                     = "jmorjsmtseresults"
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
      "TABLE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.table_storage_experiments_results.primary_connection_string
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

resource "azurerm_service_plan" "results_service_plan" {
  name                = "results-service-plan"
  resource_group_name = azurerm_resource_group.table_storage_experiments.name
  location            = azurerm_resource_group.table_storage_experiments.location
  os_type             = "Linux"
  sku_name            = "B1"
}

# data "local_file" "results_api_function_app_zip" {
#   filename = var.RESULTS_API_ZIP_DEPLOY_FILE
# }

resource "azurerm_storage_container" "results_api_function_app_storage_container" {
  name                  = "results-api-function-app-storage-container"
  storage_account_name  = azurerm_storage_account.table_storage_experiments_results.name
  container_access_type = "private"
}

resource "azurerm_storage_blob" "storage_blob" {
  name = "${filesha256(var.RESULTS_API_ZIP_DEPLOY_FILE)}.zip"
  storage_account_name = azurerm_storage_account.table_storage_experiments_results.name
  storage_container_name = azurerm_storage_container.results_api_function_app_storage_container.name
  type = "Block"
  source = var.RESULTS_API_ZIP_DEPLOY_FILE
}

data "azurerm_storage_account_blob_container_sas" "storage_account_blob_container_sas" {
  connection_string = azurerm_storage_account.table_storage_experiments_results.primary_connection_string
  container_name    = azurerm_storage_container.results_api_function_app_storage_container.name

  start = "${formatdate("YYYY-MM-DD", timestamp()))}T00:00:00Z"
  expiry = "${formatdate("YYYY-MM-DD", timeadd(timestamp(), "24h"))}T00:00:00Z"

  permissions {
    read   = true
    add    = false
    create = false
    write  = false
    delete = false
    list   = false
  }
}

resource "azurerm_linux_function_app" "results_api_function_app" {
  name                = "results-api-function-app"
  resource_group_name = azurerm_resource_group.table_storage_experiments.name
  location            = azurerm_service_plan.results_service_plan.location

  storage_account_name       = azurerm_storage_account.table_storage_experiments_results.name
  storage_account_access_key = azurerm_storage_account.table_storage_experiments_results.primary_access_key
  service_plan_id            = azurerm_service_plan.results_service_plan.id

  

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE" =  "https://${azurerm_storage_account.table_storage_experiments_results.name}.blob.core.windows.net/${azurerm_storage_container.results_api_function_app_storage_container.name}/${azurerm_storage_blob.storage_blob.name}${data.azurerm_storage_account_blob_container_sas.storage_account_blob_container_sas.sas}",
    "STORAGE_CONNECTION" = "${azurerm_storage_account.table_storage_experiments_results.primary_connection_string}"
  }

  site_config {
    always_on         = false
    use_32_bit_worker = true
  
    application_stack {
      python_version = "3.10"
    }
  }
}
