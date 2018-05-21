s3-cost-explorer
================
Retrieve the cost explorer data of your AWS account for the last 90 days and write it to S3. Send an email out through SES at 4 am every morning with the billing details from the day before. 

Installation
------------

Copy the Lambda code to a Python 3.6 function or use the attached SAM template. Make sure to grant the Lambda function with IAM permissions to access 'ce:*', 'ses:*' and 's3:PutObject'. Set a CloudWatch event to trigger the Lambda function so it retrieves the latest data and sends out an email with the latest report. 

Contact
-------

In case of questions or bugs, please raise an issue or reach out to @marekq!