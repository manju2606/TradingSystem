variable "cluster_id" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "cache_subnet_group_name" {
  type = string
}

variable "allowed_security_group_ids" {
  type = list(string)
}

variable "auth_token" {
  type      = string
  sensitive = true
}

variable "node_type" {
  type    = string
  default = "cache.t3.micro"
}

variable "num_cache_nodes" {
  type    = number
  default = 1
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "snapshot_retention_days" {
  type    = number
  default = 1
}

variable "tags" {
  type    = map(string)
  default = {}
}
