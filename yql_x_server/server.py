import sys
import os
import json
from pathlib import Path
from xml.etree import ElementTree
from fastapi import FastAPI, APIRouter, Response, Request
from fastapi.responses import PlainTextResponse
import uvicorn
from yql_x_server.YQL import YQL
from yql_x_server.XMLFactory import XMLStocksFactoryDGW, XMLWeatherFactoryYQL, XMLWeatherFactoryDGW
from yql_x_server.args import args
import requests

app = FastAPI()
sys.stdout.reconfigure(encoding='utf-8')

yql = YQL()
yql_router = APIRouter(default_response_class=PlainTextResponse)
dgw_router = APIRouter(default_response_class=PlainTextResponse)

@dgw_router.get('/dgw')
async def dgw_get():
    return Response("ok")

@dgw_router.post('/dgw')
async def dgw(request: Request):
    body = (await request.body()).decode()
    root = ElementTree.fromstring(body)
    api = root.attrib['api']
    if api == "finance":
        reqType = root[0].attrib['type']
        return XMLStocksFactoryDGW(root, reqType)
    elif api == 'weather':
        reqType = root[0].attrib['id']
        if reqType == "3":
            q = root[0][0].text
            return XMLWeatherFactoryDGW(q, yql, Search=True)
        if reqType == "30":
            return XMLWeatherFactoryDGW(root, yql)

@yql_router.get('/v1/yql')
def legacyWeatherYQL(request: Request): 
    return weatherEndpoint(request)

@yql_router.post('/yql/weather/dgw')
async def legacyWeatherDGW(request: Request):
    return dgw(request)

@yql_router.get('/yql/weather')
async def weatherEndpoint(request: Request):
    q = request.query_params.get('q')
    if q:
        if 'partner.weather.locations' and not 'yql.query.multi' in q:
            q = q[q.index('query="')+7:q.index('" a')]
            return XMLWeatherFactoryYQL(q, yql, Search=True)
        elif 'partner.weather.forecasts' in q:
            return XMLWeatherFactoryYQL(q, yql)
    return Response("Invalid Request", status_code=400)

def start():
    app.include_router(yql_router)
    app.include_router(dgw_router)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port
    )
