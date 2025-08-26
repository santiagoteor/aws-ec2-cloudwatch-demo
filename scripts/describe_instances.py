import boto3

def get_instance_status(region, identifier):
    try:
        # Initialize the EC2 client for the specified region
        ec2_client = boto3.client('ec2', region_name=region)

        # Retrieve all instances
        response = ec2_client.describe_instances()

        # List to store matching instances
        matching_instances = []

        # Search for the target instance(s) by ID or Name tag
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_state = instance['State']['Name']

                # Check if identifier matches the Instance ID
                if instance_id == identifier:
                    matching_instances.append({
                        'InstanceId': instance_id,
                        'State': instance_state
                    })

                # Check if identifier matches the Name tag
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name' and tag['Value'] == identifier:
                            matching_instances.append({
                                'InstanceId': instance_id,
                                'State': instance_state,
                                'Name': tag['Value']
                            })

        # Print all matching instances
        if matching_instances:
            print(f"Found {len(matching_instances)} matching instance(s) for identifier '{identifier}':")
            for instance in matching_instances:
                print(f"Instance Name: {instance['Name']}, Instance ID: {instance['InstanceId']}, State: {instance['State']}")
        else:
            print(f"No instances found with ID or Name '{identifier}' in region {region}.")

    except Exception as e:
        print(f"Error retrieving instance status: {e}")

# Retrieve by Instance ID
get_instance_status(region='eu-north-1', identifier='i-047944d99cd7991bc')

# Retrieve by Instance Name
get_instance_status(region='eu-north-1', identifier='nicgar_santej_lab3')
