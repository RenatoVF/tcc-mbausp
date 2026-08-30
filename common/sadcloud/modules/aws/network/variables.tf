
variable "name" {
  description = "Name for instances and group"
  type        = string
  default     = "sadcloud"
}

variable "needs_network" {
  description = "Do we need to create a network or not"
  type = bool
  default = false
}

variable "required_tags" {
  description = "Tags to apply to network resources"
  type        = map(string)
  default     = {}
}
