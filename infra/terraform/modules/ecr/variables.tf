variable "repository_names" {
  type    = list(string)
  default = ["trading-api", "trading-streamlit"]
}

variable "images_to_keep" { type = number; default = 10 }
variable "force_delete"   { type = bool;   default = false }
variable "tags"           { type = map(string); default = {} }
