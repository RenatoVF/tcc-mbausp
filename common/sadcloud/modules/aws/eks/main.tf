resource "aws_eks_cluster" "example" {
  name     = "example"
  role_arn = aws_iam_role.main[0].arn
  version =  var.out_of_date ? "1.14" : null

  vpc_config {
    subnet_ids =  ["${var.main_subnet_id}","${var.secondary_subnet_id}"]
    endpoint_public_access = var.publicly_accessible
    # public_access_cidrs = "${var.globally_accessible ? ["0.0.0.0/0"] : ["127.0.0.0/8"]}"
  }

  enabled_cluster_log_types = var.no_logs ? [] : ["api","audit","authenticator","controllerManager","scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.example-AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.example-AmazonEKSServicePolicy,
  ]

  count = var.enable_eks ? 1 : 0

  tags = merge({
    Name = var.name
  }, var.required_tags)
}

resource "aws_iam_role" "main" {
  count = var.enable_eks ? 1 : 0
  name = "eks-cluster-sadcloud-example"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY

  tags = merge({
    Name = var.name
  }, var.required_tags)
}

resource "aws_iam_role_policy_attachment" "example-AmazonEKSClusterPolicy" {
  count = var.enable_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.main[0].name
}

resource "aws_iam_role_policy_attachment" "example-AmazonEKSServicePolicy" {
  count = var.enable_eks ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.main[0].name
}
