variable "cluster_name"       { type = string }
variable "cluster_endpoint"   { type = string }
variable "oidc_provider_arn"  { type = string }
variable "oidc_provider_url"  { type = string }
variable "node_role_arn"      { type = string }
variable "karpenter_version"  { type = string; default = "1.0.6" }

variable "max_cpu"    { type = string; default = "100" }
variable "max_memory" { type = string; default = "400Gi" }

variable "tags" { type = map(string); default = {} }
