import time
import streamlit as st
import boto3
from botocore.exceptions import ClientError
from streamlit_option_menu import option_menu
import base64
import logging
from datetime import datetime, timedelta
import plotly.graph_objs as go
import tempfile


# Load the logo
logo_path = "logo.png"  # Replace with your logo file path
with open(logo_path, "rb") as image_file:
    encoded_logo = base64.b64encode(image_file.read()).decode("utf-8")


def list_security_groups(region_name):
    try:
        ec2 = boto3.client("ec2", region_name=region_name)
        response = ec2.describe_security_groups()
        return [sg["GroupId"] for sg in response["SecurityGroups"]]
    except ClientError as e:
        st.error(f"Error retrieving security groups: {e.response['Error']['Message']}")
        return []


def list_key_pairs(region_name):
    try:
        ec2 = boto3.client("ec2", region_name=region_name)
        response = ec2.describe_key_pairs()
        return [key["KeyName"] for key in response["KeyPairs"]]
    except ClientError as e:
        st.error(f"Error retrieving key pairs: {e.response['Error']['Message']}")
        return []


def create_key_pair(region_name, key_name):
    try:
        ec2 = boto3.client("ec2", region_name=region_name)
        response = ec2.create_key_pair(KeyName=key_name)
        private_key = response["KeyMaterial"]
        with open(f"{key_name}.pem", "w") as file:
            file.write(private_key)
        st.success(f"Key pair '{key_name}' created and saved to '{key_name}.pem'.")
        return key_name
    except ClientError as e:
        st.error(f"Error creating key pair: {e.response['Error']['Message']}")
        return None


def start_instance(region_name, key_pair, security_group, instance_type, ami_id, instance_name, num_instances=1):
    try:
        ec2 = boto3.client("ec2", region_name=region_name)
        response = ec2.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=num_instances,
            InstanceType=instance_type,
            KeyName=key_pair,
            SecurityGroupIds=[security_group],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": instance_name}],
                }
            ],
        )
        instances = response["Instances"]
        instance_ids = [instance["InstanceId"] for instance in instances]
        st.success(f"Successfully launched {len(instance_ids)} instance(s) in region {region_name}:")
        for instance_id in instance_ids:
            st.write(f"- Instance ID: {instance_id}")
        return instance_ids
    except ClientError as e:
        st.error(f"Error launching instance: {e.response['Error']['Message']}")
        return None
def list_instances(region):
    """
    Retrieves the list of EC2 instances in the given region, including their state and tags.
    """
    try:
        ec2_client = boto3.client("ec2", region_name=region)
        response = ec2_client.describe_instances()
        instances = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                state = instance["State"]["Name"]
                name = None
                if "Tags" in instance:
                    for tag in instance["Tags"]:
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                instances.append({"InstanceId": instance_id, "Name": name, "State": state})
        return instances
    except ClientError as e:
        st.error(f"Error retrieving instances: {e.response['Error']['Message']}")
        return []


def start_instance_by_id(region, instance_id):
    """
    Starts an EC2 instance by Instance ID.
    """
    try:
        ec2_client = boto3.client("ec2", region_name=region)
        ec2_client.start_instances(InstanceIds=[instance_id])
        st.success(f"Successfully started instance: {instance_id}")
    except ClientError as e:
        st.error(f"Error starting instance {instance_id}: {e.response['Error']['Message']}")


def stop_instance_by_id(region, instance_id):
    """
    Stops an EC2 instance by Instance ID.
    """
    try:
        ec2_client = boto3.client("ec2", region_name=region)
        ec2_client.stop_instances(InstanceIds=[instance_id])
        st.success(f"Successfully stopped instance: {instance_id}")
    except ClientError as e:
        st.error(f"Error stopping instance {instance_id}: {e.response['Error']['Message']}")



def create_bucket(bucket_name, region=None):
    try:
        if region is None:
            s3_client = boto3.client("s3")
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client("s3", region_name=region)
            location = {"LocationConstraint": region}
            s3_client.create_bucket(
                Bucket=bucket_name, CreateBucketConfiguration=location
            )
        return f"Bucket '{bucket_name}' created successfully in region '{region}'."
    except ClientError as e:
        logging.error(e)
        return f"Failed to create bucket '{bucket_name}' in region '{region}': {e.response['Error']['Message']}"


def upload_file_to_s3_with_file(bucket_name, file, file_name):
    s3_client = boto3.client("s3")
    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file.read())  # Write the file's content to the temporary file
            temp_file_path = temp_file.name

        # Upload the temporary file to S3
        s3_client.upload_file(temp_file_path, bucket_name, file_name)
        return f"File '{file_name}' uploaded successfully to bucket '{bucket_name}'."
    except ClientError as e:
        logging.error(e)
        return f"Failed to upload file: {e.response['Error']['Message']}"
    finally:
        # Clean up the temporary file
        try:
            import os
            os.remove(temp_file_path)
        except Exception as cleanup_error:
            logging.error(f"Failed to delete temporary file: {cleanup_error}")


# Function to delete an object from a bucket
def delete_object(bucket_name, object_key):
    try:
        s3_client = boto3.client("s3")
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return f"Object '{object_key}' deleted successfully from bucket '{bucket_name}'."
    except ClientError as e:
        logging.error(e)
        return f"Failed to delete object '{object_key}' from bucket '{bucket_name}': {e.response['Error']['Message']}"

def fetch_instance_metrics(region, instance_id, metrics_to_monitor):
    cloudwatch_client = boto3.client('cloudwatch', region_name=region)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)

    metric_data = []
    for metric in metrics_to_monitor:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace=metric['Namespace'],
                MetricName=metric['MetricName'],
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average'],
                Unit=metric['Unit']
            )
            datapoints = response.get('Datapoints', [])
            if datapoints:
                latest_point = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
                metric_data.append({
                    'MetricName': metric['MetricName'],
                    'Timestamp': latest_point['Timestamp'],
                    'Average': latest_point['Average'],
                    'Unit': metric['Unit']
                })
        except Exception as e:
            st.error(f"Error retrieving metric {metric['MetricName']}: {e}")
    return metric_data

# Define groups of metrics
metric_groups = {
    "CPU Metrics": [
        {'MetricName': 'CPUUtilization', 'Namespace': 'AWS/EC2', 'Unit': 'Percent'}
    ],
    "Disk Operations": [
        {'MetricName': 'DiskReadOps', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
        {'MetricName': 'DiskWriteOps', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
        {'MetricName': 'DiskReadBytes', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'},
        {'MetricName': 'DiskWriteBytes', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'}
    ],
    "Network Metrics": [
        {'MetricName': 'NetworkIn', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'},
        {'MetricName': 'NetworkOut', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'}
    ]
}
# Sidebar with logo and custom navigation menu
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{encoded_logo}" alt="Logo" width="120" height="80" style="margin-bottom: 10px;">
            <h2 style="color:#7AD180; font-size: 20px; margin: 0;">M7024E Console</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )


s3_regions = boto3.session.Session().get_available_regions("s3")
default_region = "eu-north-1"
default_index = s3_regions.index(default_region) if default_region in s3_regions else 0

with st.sidebar:
    selected_region = st.selectbox("Select AWS Region", s3_regions, index=default_index)

    selected_tab = option_menu(
        menu_title=None,
        options=["EC2", "S3", "CloudWatch"],
        icons=["server", "cloud", "graph-up-arrow"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#F0F2F6"},
            "icon": {"color": "#4CAF50", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "background-color": "#F0F2F6",
                "--hover-color": "#E8F5E9",
            },
            "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
        },
    )


if selected_tab == "EC2":
    st.header("EC2 Instance Management")

    # Use tabs instead of radio buttons
    tab1, tab2, tab3 = st.tabs(["Instance Information","Create Instance", "Manage Instances"])

    with tab1:
        st.subheader("Retrieve EC2 Instance Information")

        try:
            ec2_client = boto3.client("ec2", region_name=selected_region)
            response = ec2_client.describe_instances()
            running_instances = []

            # Filter only running instances
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        instance_name = 'Unknown'
                        if 'Tags' in instance:
                            for tag in instance['Tags']:
                                if tag['Key'] == 'Name':
                                    instance_name = tag['Value']
                        running_instances.append({
                            'Instance Name': instance_name,
                            'Instance ID': instance['InstanceId'],
                            'State': instance['State']['Name']
                        })

            if running_instances:
                # Display running instances in a table
                import pandas as pd
                df = pd.DataFrame(running_instances)  # Convert to DataFrame
                st.write(f"**Found {len(running_instances)} running instance(s):**")
                st.table(df)  # Display as table
            else:
                st.warning("No running instances found in this region.")

        except Exception as e:
            st.error(f"Error retrieving instances: {e}")

    with tab2:
        st.subheader("Launch a New EC2 Instance")

        security_groups = list_security_groups(selected_region)
        selected_security_group = st.selectbox("Choose a security group", security_groups)

        key_pairs = list_key_pairs(selected_region)
        key_pair_action = st.radio("Key Pair Options", ["Use Existing Key Pair", "Create New Key Pair"])

        if key_pair_action == "Use Existing Key Pair":
            selected_key_pair = st.selectbox("Choose a key pair", key_pairs)
        elif key_pair_action == "Create New Key Pair":
            new_key_name = st.text_input("Enter a name for the new key pair")
            if st.button("Create Key Pair") and new_key_name:
                selected_key_pair = create_key_pair(selected_region, new_key_name)
        else:
            selected_key_pair = None

        instance_types = ["t3.nano", "t3.micro", "t3.small"]
        selected_instance_type = st.selectbox("Choose an instance type", instance_types)

        instance_name = st.text_input("Enter a custom name for your EC2 instance")
        default_ami_id = "ami-08eb150f611ca277f"
        use_default_ami = st.checkbox(f"Use default AMI ID ({default_ami_id})", value=True)
        ami_id = default_ami_id if use_default_ami else st.text_input("Enter custom AMI ID")
        num_instances = st.number_input("Number of Instances", min_value=1, value=1)

        if st.button("Launch Instance"):
            if selected_key_pair and selected_security_group and instance_name:
                start_instance(
                    selected_region,
                    selected_key_pair,
                    selected_security_group,
                    selected_instance_type,
                    ami_id,
                    instance_name,
                    num_instances,
                )
            else:
                st.error("Please make sure all required inputs are provided!")

    with tab3:
        st.subheader("Manage EC2 Instances")
        instances = list_instances(selected_region)

        if instances:
            instance_options = [
                f"{instance['InstanceId']} ({instance['Name'] or 'Unnamed'}) - {instance['State']}"
                for instance in instances
            ]
            selected_instance = st.selectbox("Select an instance", instance_options)
            instance_id = selected_instance.split(" ")[0]  # Extract Instance ID

            if "running" in selected_instance:
                if st.button("Stop Instance"):
                    stop_instance_by_id(selected_region, instance_id)
            elif "stopped" in selected_instance:
                if st.button("Start Instance"):
                    start_instance_by_id(selected_region, instance_id)
            else:
                st.info("Selected instance is neither running nor stopped. No action can be performed.")
        else:
            st.warning("No instances found in this region.")

elif selected_tab == "S3":
    st.header("S3 Bucket Management")

    # Create tabs for the S3 actions
    tab1, tab2, tab3 = st.tabs(["Create Bucket", "Upload Object", "Delete Object"])

    with tab1:
        st.subheader("Create a New S3 Bucket")
        bucket_name = st.text_input("Enter Bucket Name")

        if st.button("Create Bucket"):
            if bucket_name:
                result = create_bucket(bucket_name, selected_region)
                st.success(result)
            else:
                st.error("Please provide both a bucket name and a region.")

    with tab2:
        st.subheader("Upload an Object to an S3 Bucket")

        # Initialize session state for controlling file uploader visibility
        if "show_file_uploader" not in st.session_state:
            st.session_state["show_file_uploader"] = False

        try:
            s3_client = boto3.client("s3", region_name=selected_region)
            buckets = s3_client.list_buckets()
            bucket_names = [bucket["Name"] for bucket in buckets.get("Buckets", [])]
        except ClientError as e:
            st.error(f"Error fetching buckets: {e.response['Error']['Message']}")
            bucket_names = []

        selected_bucket = st.selectbox("Select Bucket", bucket_names, key="upload_object_bucket")

        # Show "Upload File" button
        if st.button("Upload File"):
            st.session_state["show_file_uploader"] = True

        # Conditionally show file uploader
        if st.session_state["show_file_uploader"]:
            file = st.file_uploader("Drag and drop or select a file to upload", key="upload_file")
            if file and selected_bucket:
                file_name = file.name  # Use the uploaded file's name as the object name
                result = upload_file_to_s3_with_file(selected_bucket, file, file_name)
                if "successfully" in result:
                    st.success(result)
                    # Reset file uploader after successful upload
                    st.session_state["show_file_uploader"] = False
                else:
                    st.error(result)
            elif not selected_bucket:
                st.error("Please select a bucket.")
            elif not file:
                st.info("Please upload a file.")

    with tab3:
        st.subheader("Delete an Object from an S3 Bucket")

        try:
            buckets = boto3.client("s3", region_name=selected_region).list_buckets()
            bucket_names = [bucket["Name"] for bucket in buckets.get("Buckets", [])]
        except ClientError as e:
            st.error(f"Error fetching buckets: {e.response['Error']['Message']}")
            bucket_names = []

        selected_bucket = st.selectbox("Select Bucket", bucket_names, key="delete_object_bucket")

        if selected_bucket:
            try:
                objects = boto3.client("s3", region_name=selected_region).list_objects_v2(Bucket=selected_bucket)
                object_keys = [obj["Key"] for obj in objects.get("Contents", [])]
            except ClientError as e:
                st.error(f"Error fetching objects: {e.response['Error']['Message']}")
                object_keys = []

            if object_keys:
                selected_object = st.selectbox("Select Object to Delete", object_keys, key="delete_object_key")

                if st.button("Delete Object"):
                    if selected_object:
                        result = delete_object(selected_bucket, selected_object)
                        st.success(result)
                    else:
                        st.error("Please select an object to delete.")
            else:
                st.warning("No objects found in the selected bucket.")

# CloudWatch Tab for Monitoring
elif selected_tab == "CloudWatch":
    # CloudWatch view
    st.header("CloudWatch Monitoring")

    # Inputs for Instance ID and Refresh Interval
    instance_id = st.text_input("Instance ID", help="Enter the EC2 instance ID to monitor.")
    refresh_interval = st.slider("Refresh Interval (seconds)", min_value=10, max_value=120, value=30, step=10, help="Set the refresh interval for metric updates.")

    # Validate inputs
    if not instance_id or not selected_region:
        st.error("Please provide both the Instance ID and the Region.")
        st.stop()

    st.write(f"Monitoring Instance: `{instance_id}` in Region: `{selected_region}`")

    # Initialize session state for metrics data
    if 'metric_data' not in st.session_state:
        st.session_state.metric_data = {group: [] for group in metric_groups}

    # Create containers for each group to update dynamically
    graph_containers = {group_name: st.empty() for group_name in metric_groups}

    # Main loop
    while True:
        for group_name, metrics_to_monitor in metric_groups.items():
            metric_data = fetch_instance_metrics(selected_region, instance_id, metrics_to_monitor)
            if metric_data:
                st.session_state.metric_data[group_name].append({
                    'timestamp': datetime.utcnow(),
                    'data': metric_data
                })

                # Generate Plotly traces for the group
                traces = []
                for metric in metrics_to_monitor:
                    metric_name = metric['MetricName']
                    values = [
                        data_point['Average'] for record in st.session_state.metric_data[group_name]
                        for data_point in record['data']
                        if data_point['MetricName'] == metric_name
                    ]
                    timestamps = [
                        record['timestamp'] for record in st.session_state.metric_data[group_name]
                        for data_point in record['data']
                        if data_point['MetricName'] == metric_name
                    ]
                    trace = go.Scatter(x=timestamps, y=values, mode='lines+markers', name=metric_name)
                    traces.append(trace)

                # Create Plotly figure for the group
                layout = go.Layout(
                    title=f"{group_name} Metrics",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Metric Value"),
                    height=400,
                )
                fig = go.Figure(data=traces, layout=layout)

                # Update the graph in its container
                graph_containers[group_name].plotly_chart(fig, use_container_width=True)

        time.sleep(refresh_interval)
