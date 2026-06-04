variable "name" {
  description = "rds instance name"
  type        = string
  default     = "sadcloudrds"
}
############## Network ##############

variable "main_subnet_id" {
  description = "ID of main subnet"
  default = "default_main_subnet_id"
}

variable "secondary_subnet_id" {
  description = "ID of secondary subnet"
  default = "default_secondary_subnet_id"
}

############## Findings ##############

variable "no_minor_upgrade" {
  description = "do not automatically apply minor DB engine updates"
  type        = bool
  default     = false
}

variable "backup_disabled" {
  description = "disable rds instance backups"
  type        = bool
  default     = false
}


variable "storage_not_encrypted" {
  description = "do not encrypt rds instances"
  type        = bool
  default     = false
}

variable "single_az" {
  description = "only use a single availability zone with the rds instance"
  type        = bool
  default     = false
}

variable "rds_publicly_accessible" {
  description = "RDS instance is publicly accessible"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Deployment environment (PRD or HML)"
  type        = string
  default     = "PRD"
}

variable "required_tags" {
  description = "Map of required tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "enable_rds" {
  description = "Enable creating RDS instances"
  type        = bool
  default     = false
}

variable "rds_count" {
  description = "Number of RDS instances to create when enabled"
  type        = number
  default     = 1
}

variable "rds_instance_class" {
  description = "Preferred RDS instance class"
  type        = string
  default     = "db.t2.micro"
}