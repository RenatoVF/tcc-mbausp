variable "lightsail_in_use" {
  description = "lightsail is in use"
  type        = bool
  default     = false
}

variable "aws_region" {
  description = "AWS region for Lightsail availability zone"
  type        = string
  default     = "us-east-1"
}
