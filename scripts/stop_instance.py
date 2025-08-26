import boto3

def stop_instance(region, identifier):
    try:
        # Initialize the EC2 client for the specified region
        ec2_client = boto3.client('ec2', region_name=region)

        # Retrieve all instances
        response = ec2_client.describe_instances()

        # List to store i nstances to stop
        instances_to_stop = []

        # Search for matching instances by ID or Name tag
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_state = instance['State']['Name']
                instance_name = None

                # Retrieve Name tag if available
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            instance_name = tag['Value']

                # Check for match by Instance ID or Name tag
                if instance_id == identifier or instance_name == identifier:
                    if instance_state == 'running':
                        instances_to_stop.append(instance_id)
                    else:
                        print(f"Instance {instance_id} (Name: {instance_name}) is in state '{instance_state}' and cannot be stopped.")

        # Stop matching instances
        if instances_to_stop:
            print(f"Stopping instances: {instances_to_stop}")
            ec2_client.stop_instances(InstanceIds=instances_to_stop)
            print(f"Successfully initiated stop for instances: {instances_to_stop}")
        else:
            print(f"No running instances found with ID or Name '{identifier}'.")

    except Exception as e:
        print(f"Error stopping instance(s): {e}")

stop_instance(region='eu-north-1', identifier='i-047944d99cd7991bc')
stop_instance(region='eu-north-1', identifier='nicgar_santej_lab3')

