output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Map of public subnet IDs by availability zone"
  value       = { for k, v in aws_subnet.public : k => v.id }
}

output "private_subnet_ids" {
  description = "Map of private subnet IDs by availability zone"
  value       = { for k, v in aws_subnet.private : k => v.id }
}

output "nat_gateway_ids" {
  description = "Map of NAT gateway IDs by availability zone"
  value       = { for k, v in aws_nat_gateway.main : k => v.id }
}
