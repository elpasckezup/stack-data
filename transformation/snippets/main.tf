

/*
Transformation capability
*/
resource "aws_security_group" "transformation_sg" {
  
  name        = var.transformation_sg_name
  description = var.transformation_sg_description

  ingress {
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}