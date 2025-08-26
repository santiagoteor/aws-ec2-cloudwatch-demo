import boto3
from botocore.exceptions import ClientError

def list_regions():
    ec2 = boto3.client('ec2')
    try:
        regions = ec2.describe_regions()['Regions']
        return [{"RegionName": region['RegionName'], "Endpoint": region['Endpoint']} for region in regions]
    except ClientError as e:
        print(f"Error fetching regions: {e.response['Error']['Message']}")
        return []

def list_security_groups(region_name):
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.describe_security_groups()
        return [sg['GroupId'] for sg in response['SecurityGroups']]
    except ClientError as e:
        print(f"Error fetching security groups: {e.response['Error']['Message']}")
        return []

def list_key_pairs(region_name):
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.describe_key_pairs()
        return [key['KeyName'] for key in response['KeyPairs']]
    except ClientError as e:
        print(f"Error fetching key pairs: {e.response['Error']['Message']}")
        return []

def create_key_pair(region_name, key_name):
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.create_key_pair(KeyName=key_name)
        private_key = response['KeyMaterial']
        # Save the private key to a file
        with open(f"{key_name}.pem", "w") as file:
            file.write(private_key)
        print(f"Key pair '{key_name}' created and saved to '{key_name}.pem'.")
        return key_name
    except ClientError as e:
        print(f"Error creating key pair: {e.response['Error']['Message']}")
        return None

def start_instance(region_name, key_pair, security_group, instance_type, ami_id, instance_name, num_instances=1):
    try:
        ec2 = boto3.client('ec2', region_name=region_name)
        response = ec2.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=num_instances,
            InstanceType=instance_type,
            KeyName=key_pair,
            SecurityGroupIds=[security_group],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': instance_name}]
                }
            ]
        )

        instances = response['Instances']
        instance_ids = [instance['InstanceId'] for instance in instances]

        print(f"Successfully launched {len(instance_ids)} instance(s) in region {region_name}:")
        for instance_id in instance_ids:
            print(f" - Instance ID: {instance_id}")

        return instance_ids

    except ClientError as e:
        print(f"Error launching instance in region {region_name}: {e.response['Error']['Message']}")
        return None

if __name__ == "__main__":
    print("Showing available AWS regions...")
    regions = list_regions()

    if not regions:
        print("No regions available or unable to retrieve regions.")
    else:
        print("\nAvailable Regions:")
        for idx, region in enumerate(regions):
            print(f"{idx + 1}: {region['RegionName']} ({region['Endpoint']})")

        region_choice = int(input("\nSelect a region by number: ")) - 1
        if 0 <= region_choice < len(regions):
            selected_region = regions[region_choice]['RegionName']
            print(f"Selected Region: {selected_region}")

            print("\nFetching security groups...")
            security_groups = list_security_groups(selected_region)
            if security_groups:
                for idx, sg in enumerate(security_groups):
                    print(f"{idx + 1}: {sg}")
                sg_choice = int(input("Select a security group by number: ")) - 1
                selected_security_group = security_groups[sg_choice]
            else:
                print("No security groups found.")
                exit()

            print("\nShowing key pairs...")
            key_pairs = list_key_pairs(selected_region)
            if key_pairs:
                for idx, kp in enumerate(key_pairs):
                    print(f"{idx + 1}: {kp}")
                print(f"{len(key_pairs) + 1}: Create a new key pair")
                kp_choice = int(input("Select a key pair by number: ")) - 1
                if kp_choice == len(key_pairs):
                    new_key_name = input("Enter a name for the new key pair: ")
                    selected_key_pair = create_key_pair(selected_region, new_key_name)
                else:
                    selected_key_pair = key_pairs[kp_choice]
            else:
                print("No key pairs found.")
                new_key_name = input("Enter a name for the new key pair: ")
                selected_key_pair = create_key_pair(selected_region, new_key_name)

            instance_types = ["t3.nano", "t3.micro", "t3.small"]
            print("\nAvailable Instance Types:")
            for idx, it in enumerate(instance_types):
                print(f"{idx + 1}: {it}")
            it_choice = int(input("Select an instance type by number: ")) - 1
            selected_instance_type = instance_types[it_choice]

            instance_name = input("Enter a custom name for the EC2 instance: ")

            default_ami_id = "ami-08eb150f611ca277f"  # Ubuntu Server 24.04 LTS (x86_64)
            use_default_ami = input(f"Use default AMI ID ({default_ami_id})? (yes/no): ").strip().lower()
            if use_default_ami == "no":
                ami_id = input("Enter the AMI ID: ")
            else:
                ami_id = default_ami_id

            num_instances = int(input("Enter the number of instances to launch: "))

            print("Launching an EC2 instance...")
            start_instance(
                selected_region,
                selected_key_pair,
                selected_security_group,
                selected_instance_type,
                ami_id,
                instance_name,
                num_instances
            )
        else:
            print("Invalid selection. Exiting.")

