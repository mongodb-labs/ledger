# Implementing Cryptographically Verifiable Change History using MongoDB (aka Ledger)

## 1. Problem Statement

Organizations in industries such as finance, insurance, and supply chain have to (1) record complete changes to an information over time and (2) ensure that these changes have not been tampered with. The former requires storing all changes to a record over time. The later is often implemented with a combination of database auditing and security controls but it does not lead to easy verification. 


This is a proof-of-concept implementation of a library for implementing cryptographically verifiable change history of documents stored in MongoDB. The goals are two-fold:

1) Demonstrate creation of a document store with a cryptographically verifiable change history, while using MongoDB MQL and API.
2) Gather feedback on how such a functionality can address and simplify the data integrity needs of an application.


## 2. Common Questions

### 2.1 Does cyptographically verifiable change history constitute a Ledger?
Ledgers are potentially useful for applications in areas such as drug development, accounting, audit, HR, crypto, and compliance. 

A common underlying themes for applications in the aforementioned areas is that information is stored in append-only mode. The assumption is that once the information has been stored in a ledger, it would not later be changed by an unauthorized entity. If a change is made to the information stored in a ledger, the change can be detected (e.g., using offline or online techniques). Cryptographic verification of change history helps determine information tampering in an online manner (e.g., upon document read).


### 2.2 Why not use MongoDB Auditing for document change history?

In MongoDB, auditing can be enabled to record any changes made to documents. However, the audit records are generated in a separate file. To obtain the list of changes made to a single document, (1) MongoDB will need to be started with appropriate audit filters, and (2) the developer will have to sift through all the audit log entries to find the relevant changes for the document. This approach places additional burden on a developer.


## 3. Implementation Details

This proof-of-concept library is implemented in Python. It provides functions to store 
documents in a collection along with cryptographic tamper-evidence (presently, a SHA256 
over the document and its history (if any) along with document metadata created 
by the library). Any updates to an existing document automatically results into a new copy of 
the document being inserted. The current and previous versions of a document are 
stored in separate collection. The name of this separate collection is 
`collectionname_history`. Any insertion or updates in this `history` collection
are managed by the library.


Specifically, the libray defines the following five functions:

1) `insert_one_ledger`: inserts a document in a collection along with cryptographic tamper-evidence and metadata.
2) `update_one_ledger`: updates an existing document while preserving the previous document, and links the two versions through cryptographic tamper-evidence.
3) `delete_one_ledger`: deletes a document from the collection; the document is still retained within the `collectionname_history` collection.
4) `verify_one_ledger`: verifies that document history is unchanged.
5) `init_ledger`: binds the above four functions to the collection python object, so that a developer can invoke these functions on a collection object as it would do so for any other collection function.


## 4. Developing an Application

Clone the repository:
```
git clone git@github.com:salmanbaset/mdb_ledger.git
cd mdb_ledger
```

Setup virtualenv and install dependencies:
```
virtual env
pip install -r requirements.txt
```

Locally setup a MongoDB replica set or use Atlas to create a M10+ cluster. Since the library
uses Transactions, a replica set must be launched. It can be created on your local machine 
through the following command:
```
mlaunch --replicaset --name ledger-rs --port 27001
```

Import the ledger library, create connection to your Mongo instance, and call the `init_ledger` function on the collection that will act as a ledger. This function dynamically adds the functions mentioned above to the collection object.

```
import os
import ledger
import pymongo

uriString = 'mongodb://localhost:27001,localhost:27002,localhost:27003'
client = pymongo.MongoClient(uriString, replicaSet='ledger-rs')

mydb = client['mydatabase']
mycol = mydb['customers']

# initialize the ledger functions using function bindings
ledger.init_ledger(mycol)
```

### 5.1 Insert a document
Inserts a document into the specified collection. Another copy of the document is inserted into the history collection. History collection has a `_history` suffix with prefix being the collection name.

```
mydict = { "key": "v1" }
x = mycol.insert_one_ledger(mydict, client)
print (x.inserted_id)
```

### 5.2 Update a document
Applies the update operation, retrieves the updated doc, update hash,
and store it in the history collection.
```
params = {"$set": {"name": "John 2"}}
mycol.update_one_ledger({"_id": inserted_id}, params, client)
```

### 5.3 Delete a document
Delete a document from the ledger collection.
```
deleted = mycol.delete_one_ledger({"_id": inserted_id}, client)
```

### 5.4 Verify change history of a document
Verify change history of a document.
```
ret = mycol.verify_one_ledger({"_ledgermeta.orig_id": inserted_id}, client)
print (ret)
```

## 6. Can I use this code in production?

This code is a proof-of-concept implementation of cryptographically verifiable
change history using MongoDB. It is not meant for production usage.