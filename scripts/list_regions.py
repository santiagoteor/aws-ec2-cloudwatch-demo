import boto3
from botocore.exceptions import ClientError

def list_regions():
    ec2 = boto3.client('ec2')

    try:
        regions = ec2.describe_regions()['Regions']
        print(f"{'Region Name':<20}{'Endpoint':<40}")
        for region in regions:
            print(f"{region['RegionName']:<20}{region['Endpoint']:<40}")
    except ClientError as e:
        print(f"ClientError: {e.response['Error']['Message']}")

if __name__ == "__main__":
    print("Listing AWS Regions and Endpoints")
    list_regions()

