import boto3

s3_client = boto3.client('s3')
s3_client.generate_presigned_url(
            ClientMethod="get",
            Params={'Bucket': "d", 'Key': "sss"},
            ExpiresIn=800)