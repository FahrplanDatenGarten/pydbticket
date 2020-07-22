import json
from typing import Union

import jwt
import requests

from pydbticket.order import Leg, Order, Ticket


def checkin(ticket: Ticket, leg: Leg,
            coach: Union[int, str], seat: Union[int, str]):
    """
    Makes a SelfCheckIn-Request

    :param ticket: A valid ticket for the leg
    :param leg: The leg of the order, wich should be checked in
    :param coach: The Waggon Number
    :param seat: The Seat Number
    :return: The JSON-Body of the response
    """

    url = 'https://kanalbackend-navigator-prd-default-kci-tck.dbv.noncd.db.de/sci_sci'

    request_headers = {
        'User-Agent': 'DB Navigator Beta/20.08.s22.30 (Android REL 28)',
        'Content-Type': 'application/json; charset=utf-8'
    }

    jwt_message = {
        "zug": {
            "nr": leg.number,
            "gat": leg.kind
        },
        "ticket": {
            "tkey": ticket.key,
            "issuer": ticket.issuer
        },
        "version": 1
    }

    token = gen_token(jwt_message)

    body = {
        "sci_sci_rq": {
            "anz_kind": 0,
            "anz_res": 0,
            "ticket": {
                "reisender_nachname": ticket.lastname,
                "ot_nummer": ticket.serial_number,
                "bcb_erforderlich": "N",
                "tkey": ticket.key,
                "issuer": ticket.issuer,
                "reisender_vorname": ticket.forename,
            },
            "zug": {
                "nr": leg.number,
                "gat": leg.kind,
            },
            "kl": 2,
            "token": token,
            "ver": 1,
            "bcs": [],
            "anz_erw": 1,
            "abfahrt": {
                "ebhf_nr": leg.departure.station_number,
                "zeit": pytz.UTC.normalize(
                    leg.departure.datetime).replace(
                    tzinfo=None).isoformat() + 'Z',
                "ebhf_name": leg.departure.station_name,
                "eva_name": leg.departure.station_name,
                "eva_nr": leg.departure.station_number},
            "ankunft": {
                "ebhf_nr": leg.arrival.station_number,
                "zeit": leg.arrival.datetime.isoformat() + 'Z',
                "ebhf_name": leg.arrival.station_name,
                "eva_name": leg.arrival.station_name,
                "eva_nr": leg.arrival.station_number,
            },
            "bc_rabatts": [],
            "plaetze": [
                {
                    "wagennr": int(coach),
                    "platznr": int(seat),
                },
            ],
        },
    }

    request_body = json.dumps(body)

    response = requests.post(
        url,
        data=request_body,
        headers=request_headers).content
    return response


def gen_token(message):
    secret = 'nougat20maybe17bonus'

    return jwt.encode(message, secret, algorithm='HS256').decode("utf-8")
