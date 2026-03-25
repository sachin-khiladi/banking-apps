variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "app_name" {
  description = "Short application name used in resource names"
  type        = string
}

variable "env" {
  description = "Deployment environment (dev | prod)"
  type        = string
}

variable "unique_suffix" {
  description = "Short suffix to guarantee globally unique Cosmos account names (e.g. last 6 chars of subscription ID)"
  type        = string
}

variable "enable_serverless" {
  description = "Enable Cosmos DB serverless capacity mode (true = dev cost savings; false = provisioned autoscale for prod)"
  type        = bool
  default     = true
}

variable "consistency_level" {
  description = "Default consistency level for the Cosmos DB account"
  type        = string
  default     = "Session"

  validation {
    condition     = contains(["BoundedStaleness", "Eventual", "Session", "Strong", "ConsistentPrefix"], var.consistency_level)
    error_message = "consistency_level must be one of: BoundedStaleness, Eventual, Session, Strong, ConsistentPrefix."
  }
}

variable "db_name" {
  description = "SQL (NoSQL) database name inside the Cosmos account"
  type        = string
  default     = "banking"
}

variable "container_name" {
  description = "SQL container name — must match the app constant _CONTAINER_NAME = \"accounts\""
  type        = string
  default     = "accounts"
}

variable "partition_key_path" {
  description = "Partition key path — must match the app constant _PARTITION_KEY = \"accountNumber\""
  type        = string
  default     = "/accountNumber"
}

variable "max_throughput" {
  description = "Autoscale max throughput (RU/s) — only used when enable_serverless = false"
  type        = number
  default     = 1000
}

variable "deployer_object_id" {
  description = "Object ID of the principal running Terraform; granted Cosmos DB Built-in Data Contributor for local dev access"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
