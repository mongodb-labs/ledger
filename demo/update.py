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



# 2. Update the inserted document
inserted_id = sys.argv[1]
params = {"$set": {"Address": "1 Michigan Avenue", "City": "Chicago", "State": "IL"}}
mycol.update_one_ledger({"_id": inserted_id}, params, client)
