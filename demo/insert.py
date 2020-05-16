import os
import pymongo
import sys

sys.path.append("..")
import ledger


uriString = 'mongodb://localhost:27017,localhost:27018,localhost:27019'
client = pymongo.MongoClient(uriString, replicaSet='ledger-rs')

mydb = client['mydatabase']
mycol = mydb['customers']

#0. Initialize the ledger functions using function bindings
ledger.init_ledger(mycol)

# 1. Insert first document
mydict = { 
  "First name": "Jane",
  "Last name": "Hill",
  "Address": "1 Broadway",
  "City": "New York",
  "State": "NY"
}


# 1. insert the document in the ledger
x = mycol.insert_one_ledger(mydict, client)
print (x.inserted_id)
