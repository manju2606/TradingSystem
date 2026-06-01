variable "cluster_name"        { type = string }
variable "kubernetes_version"  { type = string; default = "1.30" }
variable "vpc_id"              { type = string }
variable "private_subnet_ids"  { type = list(string) }
variable "public_subnet_ids"   { type = list(string) }
variable "cluster_role_arn"    { type = string }
variable "node_role_arn"       { type = string }
variable "ebs_csi_role_arn"    { type = string }

variable "system_node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}
variable "system_node_desired" { type = number; default = 2 }
variable "system_node_min"     { type = number; default = 2 }
variable "system_node_max"     { type = number; default = 4 }

variable "tags" {
  type    = map(string)
  default = {}
}
