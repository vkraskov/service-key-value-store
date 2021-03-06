import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pydantic.types import UUID4
from pymongo import errors

from MongoAPI import MongoAPI


data = {
    "database": os.environ['DB_DATABASE'],
    "collection": "keyvalues",
    "user": os.environ['DB_USER'],
    "password": os.environ['DB_PASSWORD'],
    "host": os.environ['DAT_HOST'],
    "port": os.environ['DAT_PORT'],
}

try:
    db = MongoAPI(data)
except errors.AutoReconnect as error:
    print("Conniction to Database failed")
    print("Message : ", error._message)
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database Unavilable ")
except errors.PyMongoError as error:
    print("Message: ", error._message)
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database Unavilable ")


app = FastAPI(title='TEXT SEARCH API')


class Document(BaseModel):
    table: str
    key: str
    value: object



@app.get('/')
async def base():
    return {"status": "up"}


@app.get('/api/{table}/get/{key}')
async def get_value(table: str, key: str):
    print("get_value", table, key)
    try:
        response = db.get_value(table, key)
    except errors.PyMongoError as error:
        print(error._message)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Connection error")
    #
    if response is None or response == []:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found!")
    return response


@app.post('/api/{table}/set/{key}')
async def set_value(table: str, key: str, doc: dict, status_code=201):
    print(f"set_value {table} {key} for {doc}")
    try:
        success = db.set_value(table, key, doc)
    except errors.DuplicateKeyError as error:
        print(error._message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document already exists")
    except errors.WriteError as error:
        print(error._message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Write error")
    except errors.PyMongoError as error:
        print(error._message)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Connection error")
    response = {'status': 'Successfully Inserted'}
    return response


@app.delete('/api/{table}/del/{key}')
async def mongo_delete(table: str, key: str):
    try:
        delete_count = db.delete_pair(table, key)
        if delete_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found!")
        return {'deleted': key}
    except errors.WriteError as error:
        print(error._message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document already exists")
    except errors.PyMongoError as error:
        print(error._message)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Connection error")


#
# @app.get('/api/doc/search')
# async def mongo_search(q: SearchQuery):
#     search_text = ""
#     if q.fuzzy:
#         search_text = fuzzy_text(clear(q.query))
#         print("Search text (fuzzy) = ", search_text)
#     else:
#         for i in clear(q.query):
#             search_text = search_text + "(?=.*" + i + ")"
#         print("Search text = ", search_text)
#         # search_text=q.query
#     try:
#         res = db.search(search_text, q.fuzzy, q.limit, q.threshold, q.user_id)
#     except errors.PyMongoError as error:
#         print(error._message)
#         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Connection error")
#
#     # print(a)
#     print(res)

    return res


if __name__ == '__main__':
    uvicorn.run('app:app', debug=True, reload=True, port=int(os.environ['APP_PORT']), host=os.environ['APP_HOST'])
