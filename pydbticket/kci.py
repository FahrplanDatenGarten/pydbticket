import datetime
import json
import random

import jwt
import requests
from lxml import etree


def checkin(order, name, train_nr, waggon, seat):
    """
    Makes a SelfCheckIn-Request

    :param order: Order-Number of the ticket (e.g. R8U4GK)
    :param name: Last name of the traveller
    :param train_nr: Position of the current train in the list of trains in the ticket
    :param waggon: The Waggon Number
    :param seat: The Seat Number
    :return: The JSON-Body of the response
    """

    url = 'https://kanalbackend-navigator-prd-default-kci-tck.dbv.noncd.db.de/sci_sci'

    request_headers = {
        'User-Agent': 'DB Navigator Beta/20.08.s22.30 (Android REL 28)',
        'Content-Type': 'application/json; charset=utf-8'
    }

    parsed_response = request_order(order, name)

    if parsed_response.tag != "rperror":
        tkey = parsed_response.find('order').find(
            'tcklist').find('tck').find('mtk').find('tkey').text
        ot_nummer = parsed_response.find('order').find(
            'tcklist').find('tck').find('mtk').find('ot_nr_hin').text
        vorname = parsed_response.find('order').find('tcklist').find(
            'tck').find('mtk').find('reisender_vorname').text
        issuer = parsed_response.find('order').find(
            'tcklist').find('tck').find('mtk').find('iss').text

        train = parsed_response.find('order').find(
            'schedulelist').find('out').find('trainlist')[train_nr]

        dep = train.find("dep")
        arr = train.find("arr")

        zugnr = train.find('zugnr').text
        zuggat = train.find('gat').text
    else:
        print('error')

    jwt_message = {
        "zug": {
            "nr": zugnr,
            "gat": zuggat
        },
        "ticket": {
            "tkey": tkey,
            "issuer": int(issuer)
        },
        "version": 1
    }

    token = gen_token(jwt_message)

    body = {
        "sci_sci_rq": {
            "anz_kind": 0,
            "anz_res": 0,
            "ticket": {
                "reisender_nachname": name,
                "ot_nummer": ot_nummer,
                "bcb_erforderlich": "N",
                "tkey": tkey,
                "issuer": int(issuer),
                "reisender_vorname": vorname
            },
            "zug": {
                "nr": zugnr,
                "gat": zuggat,
            },
            "kl": 2,
            "token": token,
            "ver": 1,
            "bcs": [],
            "anz_erw": 1,
            "abfahrt": {
                "ebhf_nr": dep.find('ebhf_nr').text,
                "zeit": "2020-06-28T19:28:00Z",
                "ebhf_name": dep.find('ebhf_name').text,
                "eva_name": dep.find('ebhf_name').text,
                "eva_nr": dep.find('ebhf_nr').text
            },
            "ankunft": {
                "ebhf_nr": arr.find('ebhf_nr').text,
                "zeit": "2020-06-28T20:54:00Z",
                "ebhf_name": arr.find('ebhf_name').text,
                "eva_name": arr.find('ebhf_name').text,
                "eva_nr": dep.find('ebhf_nr').text
            },
            "bc_rabatts": [],
            "plaetze": [
                {
                    "wagennr": int(waggon),
                    "platznr": int(seat)
                }
            ]
        }
    }

    request_body = json.dumps(body)

    response = requests.post(
        url,
        data=request_body,
        headers=request_headers).content
    return response


def request_order(nr, name):
    """
    Requests the Ticketdetails

    :param nr: Order-Number of the ticket (e.g. R8U4GK)
    :param name: Last name of the traveller
    :return: lxml.etree._Element of the response
    """
    xml = '<rqorder on="{}"/><authname tln="{}"/>'.format(
        nr, name)

    url = 'https://fahrkarten.bahn.de/mobile/dbc/xs.go'
    tnr = random.getrandbits(64)
    ts = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    request_body = '<rqorderdetails version="2.0"><rqheader tnr="{0}" ts="{1}" v="19100000" d="iPhone10,4" os="iOS_13.1.3" app="NAVIGATOR"/>{2}</rqorderdetails>'.format(
        tnr,
        ts,
        xml)
    response = requests.post(url, data=request_body).content
    return etree.fromstring(response)


def gen_token(message):
    secret = 'nougat20maybe17bonus'

    return jwt.encode(message, secret, algorithm='HS256').decode("utf-8")
