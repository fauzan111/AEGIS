# Single-AZ VPC, matches the tutor's HLD: one public subnet (entry point
# for the NAT gateway and anything internet-facing), one private subnet
# (everything else — EKS nodes, the internal ALB/NLB, all NF pods).
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.7"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = [var.az]
  public_subnets  = ["10.0.0.0/24"]
  private_subnets = ["10.0.1.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true # exactly 1 NAT GW, not one-per-AZ — cost-conscious, matches single-AZ design
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Tags the EKS module and the AWS Load Balancer Controller both expect
  # to auto-discover which subnets to use for internal vs. internet-facing
  # load balancers.
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}
