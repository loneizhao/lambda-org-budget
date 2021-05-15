import json
import urllib
import boto3
import gzip
import io

print('Loading function')

# General services
s3 = boto3.client('s3')
organizations = boto3.client('organizations')
budgets = boto3.client('budgets')
# Values

rootorg = "r-u8ln"    #root organization ID
targetorg = "ou-u8ln-vhyij8z9" # target organization unit ID
payeraccountid = "9xxxxxxxxxxx" # 12 bit Payer account ID
SNSARN = "arn:aws:sns:us-east-1:9xxxxxxxxxxx:mytopic" #SNS topic ARN

def decompress(data):
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
        return f.read()


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'],encoding='utf-8',errors='replace')
    try:
        s3_object = s3.get_object(Bucket=bucket, Key=key)
        s3_object_content = s3_object['Body'].read()
        s3_object_unzipped_content = decompress(s3_object_content)
        json_object = json.loads(s3_object_unzipped_content)
        for record in json_object['Records']:
            if record['eventName'] == "AcceptHandshake":
                accountId = record['userIdentity']['accountId']
#                print ("Accountid is " ,accountId)
                response = organizations.move_account(
             AccountId=accountId,
             SourceParentId=rootorg,
             DestinationParentId=targetorg
             )
             #print(response)
                response = budgets.create_budget(
             AccountId=payeraccountid,
             Budget={
             'BudgetName': accountId,
             'BudgetLimit': {
             'Amount': '500',
             'Unit': 'USD'
              },
              'CostFilters': {
              'LinkedAccount': [
                accountId,
                  ]
               },
        'CostTypes': {
            'IncludeTax': True,
            'IncludeSubscription': True,
            'UseBlended': False,
            'IncludeRefund': False,
            'IncludeCredit': False,
            'IncludeUpfront': False,
            'IncludeRecurring': True,
            'IncludeOtherSubscription': True,
            'IncludeSupport': True,
            'IncludeDiscount': False,
            'UseAmortized': False
        },
        'TimeUnit': 'ANNUALLY',
#        'TimePeriod': {
#            'Start': datetime(2015, 1, 1),
#            'End': datetime(2115, 1, 1)
#        },
        'CalculatedSpend': {
            'ActualSpend': {
                'Amount': '500',
                'Unit': 'USD'
            },
            'ForecastedSpend': {
                'Amount': '500',
                'Unit': 'USD'
            }
        },
        'BudgetType': 'COST',
#        'LastUpdatedTime': datetime(2015, 1, 1)
    },
             NotificationsWithSubscribers=[
        {
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 90,
                'ThresholdType': 'PERCENTAGE',
                'NotificationState': 'ALARM'
            },
            'Subscribers': [
                {
                    'SubscriptionType': 'SNS',
                    'Address': SNSARN
                },
            ]
        },
    ]
)
   

    except Exception as e:
        print(e)
        raise e
