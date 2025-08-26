import boto3
from datetime import datetime, timedelta
import time

def monitor_instance_metrics_realtime(region, instance_id, refresh_interval=60):
    try:
        # Initialize the CloudWatch client for the specified region
        cloudwatch_client = boto3.client('cloudwatch', region_name=region)

        # Define the metrics to monitor
        metrics_to_monitor = [
            {'MetricName': 'CPUUtilization', 'Namespace': 'AWS/EC2', 'Unit': 'Percent'},
            {'MetricName': 'DiskReadOps', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
            {'MetricName': 'DiskWriteOps', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
            {'MetricName': 'DiskReadBytes', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'},
            {'MetricName': 'DiskWriteBytes', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'},
            {'MetricName': 'NetworkIn', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'},
            {'MetricName': 'NetworkOut', 'Namespace': 'AWS/EC2', 'Unit': 'Bytes'},
            {'MetricName': 'StatusCheckFailed', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
            {'MetricName': 'StatusCheckFailed_Instance', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
            {'MetricName': 'StatusCheckFailed_System', 'Namespace': 'AWS/EC2', 'Unit': 'Count'},
            {'MetricName': 'MemoryUtilization', 'Namespace': 'CWAgent', 'Unit': 'Percent'},
            {'MetricName': 'SwapUsage', 'Namespace': 'CWAgent', 'Unit': 'Bytes'},
            {'MetricName': 'FreeStorageSpace', 'Namespace': 'CWAgent', 'Unit': 'Bytes'}
        ]

        print(f"Starting real-time monitoring for instance {instance_id} in region {region}...")
        print("Press Ctrl+C to stop the monitoring.")

        while True:
            # Define the time range for the current fetch
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)  # Fetch data for the last 5 minutes

            print(f"\n[Real-Time Update: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC]")
            for metric in metrics_to_monitor:
                try:
                    response = cloudwatch_client.get_metric_statistics(
                        Namespace=metric['Namespace'],
                        MetricName=metric['MetricName'],
                        Dimensions=[
                            {'Name': 'InstanceId', 'Value': instance_id}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,  # Data points every 5 minutes
                        Statistics=['Average'],
                        Unit=metric['Unit']
                    )

                    # Print the latest data point, if available
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        latest_point = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
                        print(f"Metric: {metric['MetricName']}, Average Value: {latest_point['Average']} {metric['Unit']}")
                    else:
                        print(f"Metric: {metric['MetricName']}, No data available for the last 5 minutes.")
                except Exception as e:
                    print(f"Error retrieving metric {metric['MetricName']}: {e}")

            # Wait for the next refresh
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\nReal-time monitoring stopped.")
    except Exception as e:
        print(f"Error in real-time monitoring: {e}")



region = 'eu-north-1'
instance_id = 'i-0fde582b868f11d61'
monitor_instance_metrics_realtime(region, instance_id)
monitor_instance_metrics_realtime(region, instance_id, refresh_interval=30)
