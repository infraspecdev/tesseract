variable "environment" {
  type    = string
  default = "dev"
}

variable "tags" {
  type    = map(string)
  default = {}
}
