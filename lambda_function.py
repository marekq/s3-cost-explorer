#!/usr/bin/python
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8

import boto3, datetime, os, re, time
from operator import itemgetter

# set up connections with the cost explorer api and s3 api
c   = boto3.client('ce')
s   = boto3.client('s3')
n   = boto3.client('ses')

def lambda_handler(event, context):
    # get the timestamps for today as the end date for the report and the 
    endd    = datetime.datetime.now()                   # today
    tomod   = endd + datetime.timedelta(days = 1)       # tomorrow
    yestd   = endd - datetime.timedelta(days = 1)       # yesterday
    startd  = endd - datetime.timedelta(days = 90)      # 90 days ago
    
    # run a query against the cost api to retrieve the cost and usage reports. since the query is done exclusive of the last day, we run it for tomorrow
    z       = c.get_cost_and_usage(TimePeriod = {'Start': startd.strftime("%Y-%m-%d"), 'End': tomod.strftime("%Y-%m-%d")}, GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}], Granularity = 'DAILY', Metrics = ['BlendedCost'])
    
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
        
    # open output file from yesterday
    l       = []
    res     = ''
    fn      = '/tmp/'+yestd.strftime('%Y-%m-%d').replace('-', '/')+'.csv'
    f       = open(fn.strip(), 'r')
    
    # read the cost and value from the file and store in list, which we will sort later
    for line in f:
        x   = line.split(',')
        l.append([x[1], x[2]])
    f.close()
    
    # create an html header
    html = '<html><head>'+open('style.css').read()+'</head><body><h1>AWS cost report for '+yestd.strftime('%Y-%m-%d')+'</h1><table>'
    
    # sort the list and count total daily costs
    tot     = float(0)
    for x in sorted(l, key = itemgetter(1), reverse = True):
        if not re.search('cost', str(x)):
            html    += '<tr><td>'+x[0]+'</td><td>$ '+x[1][:6]+'</td></tr>'
            tot     += float(x[1])

    # print the total daily costs and print html footer
    html += '<tr><td>Total Cost</td><td>$ '+str(tot)[:6]+'</td></tr></table></body></html>'

    # send an email containing the table
    n.send_email(
        Source = os.environ['from_email'],
        Destination = {'ToAddresses': [os.environ['to_email']]},
        Message = {
            'Subject': {
                'Data': 'AWS - '+yestd.strftime("%Y-%m-%d")+' cost report',
                'Charset': 'utf8'},
            'Body': {
                'Html': {
                    'Data': html,
                    'Charset': 'utf8'
                }
            }
        }
    )
