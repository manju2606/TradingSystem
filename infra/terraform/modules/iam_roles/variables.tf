variable "prefix"               { type = string }
variable "ebs_csi_assume_policy" {
  type        = string
  description = "JSON assume-role policy for EBS CSI — provide the IRSA trust policy from the eks module output"
  default     = <<-EOT
    {"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Principal":"*","Resource":"*"}]}
  EOT
}
variable "tags" { type = map(string); default = {} }
