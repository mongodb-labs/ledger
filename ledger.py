import pymongo
import types
from base64 import b64encode
from os import urandom
import json
import hashlib
import types
import sys


# inserts single document
# creates an id for the doc if not present.
# W + W
def insert_one_ledger(self, params, client):

    db = self.database

    history_col_name = self.name + "_history"
    history_col = db[history_col_name]

    random_bytes = urandom(32)
    doc_id = b64encode(random_bytes).decode("utf-8")

    random_bytes = urandom(32)
    nonce = b64encode(random_bytes).decode("utf-8")

    if "_id" not in params.keys():
        params["_id"] = doc_id

    params["_ledgermeta"] = {}
    params["_ledgermeta"]["prev_hash"] = ""
    params["_ledgermeta"]["orig_id"] = params["_id"]
    params["_ledgermeta"]["nonce"] = nonce
    params["_ledgermeta"]["op"] = "INSERTONE"
    params["_ledgermeta"]["seqno"] = 1
    del params["_id"] # to make it easy to verify updates to a document

    # get json string with keys sorted
    json_str = json.dumps(params, sort_keys=True).encode("utf-8")
    digestsha256 = hashlib.sha256(json_str)

    params["_ledgermeta"]["hash"] = digestsha256.hexdigest()
    params["_id"] = params["_ledgermeta"]["orig_id"] #readd id

    # Start transaction
    col_ret = None
    with client.start_session() as s:
        s.start_transaction()
        # insert in main collection
        col_ret = self.insert_one(params)

        # insert in ledger
        del params["_id"]
        history_col.insert_one(params)
        s.commit_transaction()

    ##TODO: what happens if either there is an error in col_ret or history_col_ret 
    return col_ret

# updates single document
# not thread safe
# requires that _id must be present in query. all other query parameters ignored
# W + R + W
def update_one_ledger(self, query, params, client):

    db = self.database
    history_col_name = self.name + "_history"
    history_col = db[history_col_name]

    random_bytes = urandom(32)
    nonce = b64encode(random_bytes).decode("utf-8")

    query = {"_id": query["_id"]}

    params["$set"]["_ledgermeta.nonce"] = nonce
    params["$set"]["_ledgermeta.op"] = "UPDATEONE"
    params["$inc"] = {"_ledgermeta.seqno": 1}


    ret = None
    with client.start_session() as s:
        s.start_transaction()
        # update in main collection
        # we update it first in order to let mongo take care of all the query syntax
        ret = self.update_one(query, params)
        if ret is None:
            return None

        # now update in collection ledger
        item = self.find_one(query)

        item["_ledgermeta"]["prev_hash"] = item["_ledgermeta"]["hash"]

        del item["_id"]
        del item["_ledgermeta"]["hash"]

        # get json string with keys sorted
        json_str = json.dumps(item, sort_keys=True).encode("utf-8")
        digestsha256 = hashlib.sha256(json_str)
        item["_ledgermeta"]["hash"] = digestsha256.hexdigest()

        # add this document to history collection
        history_col.insert_one(item)

        # update this item again with new hash in main collection
        item["_id"] = item["_ledgermeta"]["orig_id"]
        newparams = {"$set": {}}
        newparams["$set"]["_ledgermeta.prev_hash"] = item["_ledgermeta"]["prev_hash"]
        newparams["$set"]["_ledgermeta.hash"] = item["_ledgermeta"]["hash"]
        self.update_one(query, newparams)

        s.commit_transaction()

    return ret

# delete document based on id
# not thread safe
# requires that _id must be present in query. all other query parameters ignored
# R + D + W
def delete_one_ledger(self, query, client):

    db = self.database
    history_col_name = self.name + "_history"
    history_col = db[history_col_name]

    random_bytes = urandom(32)
    nonce = b64encode(random_bytes).decode("utf-8")

    query = {"_id": query["_id"]}

    # now update in collection ledger
    item = self.find_one(query)

    item["_ledgermeta"]["nonce"] = nonce
    item["_ledgermeta"]["prev_hash"] = item["_ledgermeta"]["hash"]
    item["_ledgermeta"]["op"] = "DELETEONE"
    item["_ledgermeta"]["seqno"] = item["_ledgermeta"]["seqno"] + 1

    del item["_id"]
    del item["_ledgermeta"]["hash"]

    # get json string with keys sorted
    json_str = json.dumps(item, sort_keys=True).encode("utf-8")
    digestsha256 = hashlib.sha256(json_str)
    item["_ledgermeta"]["hash"] = digestsha256.hexdigest()

    ret = self.delete_one(query)
    history_col.insert_one(item)

    return ret

# returns a boolean: True or False
# not thread safe
# if no items found, True is returned
def verify_one_ledger(self, query, client):

    items_found = False # flag checks if query returned any items

    db = self.database
    history_col_name = self.name + "_history"
    history_col = db[history_col_name]

    items = history_col.find(query).sort("_ledgermeta.seqno", 1)

    if items is None:
        return None

    hashes_match = True
    for item in items:
        items_found = True
        orig_hash = item["_ledgermeta"]["hash"]
        del item["_id"]
        del item["_ledgermeta"]["hash"]

        json_str = json.dumps(item, sort_keys=True).encode("utf-8")
        computed_hash = hashlib.sha256(json_str).hexdigest()

        if ( orig_hash != computed_hash):
            hashes_match = False
            return hashes_match

    return hashes_match & items_found



def init_ledger(mycol):
    mycol.insert_one_ledger = types.MethodType( insert_one_ledger, mycol )
    mycol.update_one_ledger = types.MethodType( update_one_ledger, mycol )
    mycol.delete_one_ledger = types.MethodType( delete_one_ledger, mycol )
    mycol.verify_one_ledger = types.MethodType( verify_one_ledger, mycol )
