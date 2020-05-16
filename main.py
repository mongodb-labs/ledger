import os
import ledger
import pymongo
import sys

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

# # 2. Update the inserted document
# inserted_id = x.inserted_id
# params = {"$set": {"Address": "1 Michigan Avenue", "City": "Chicago", "State": "IL"}}
# mycol.update_one_ledger({"_id": inserted_id}, params, client)

# # 3. Update the inserted document again
# params = {"$set": {"name": "John 3"}}
# mycol.update_one_ledger({"_id": inserted_id}, params, client)

# # 4. Delete the document
# deleted = mycol.delete_one_ledger({"_id": inserted_id}, client)

# inserted_id = "64vP2xz+rrntaLbaSFhitsnG7Dng6y2+Qq08JrIPYzo="
# ret = mycol.verify_one_ledger({"_ledgermeta.orig_id": inserted_id}, client)
# print (ret)

# sys.exit()
