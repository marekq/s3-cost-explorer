import boto3, datetime, os, time

# set up connections with the cost explorer api and s3 api
c   = boto3.client('ce')
s   = boto3.client('s3')

def lambda_handler(event, context):
    # get the timestamps for today as the end date for the report and the 
    endd    = datetime.datetime.now()
    startd  = endd - datetime.timedelta(days = 180)
    
    # run a query against the cost api to retrieve the cost and usage reports
    z       = c.get_cost_and_usage(TimePeriod = {'Start': startd.strftime("%Y-%m-%d"), 'End': endd.strftime("%Y-%m-%d")}, GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}], Granularity = 'DAILY', Metrics = ['BlendedCost'])
    
    # iterate of the dates returned
    for x in z['ResultsByTime']:
        
        # create the headers for the csv file in a list
        csvf        = ['date,item,cost']

        # retrieve filename on the '/tmp' and create the directories if needed
        fname       = '/tmp/'+x['TimePeriod']['Start'].replace('-', '/')+'.csv'
        if not os.path.exists(os.path.dirname(fname)):
            os.makedirs(os.path.dirname(fname))
        
        # per record entry, retrieve the date, itemname and daily total cost
        for y in x['Groups']:
            dat     = x['TimePeriod']['Start']
            item    = y['Keys']
            cost    = y['Metrics']['BlendedCost']['Amount']
            citem   = dat+','+str(item[0])+','+str(cost)
            csvf.append(citem.strip())
        
        # open a file on the '/tmp' disk and write the report        
        tmp = open(fname, 'w')
        for item in csvf:
            tmp.write(item+'\n')        
        tmp.close()
    
        # upload the report to s3
        s.put_object(Bucket = os.environ['bucket'], Body = open(fname, 'rb'), Key = fname[5:], ContentType = 'text/plain')