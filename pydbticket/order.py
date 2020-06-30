import datetime
import random
from enum import Enum
from typing import List, Optional, Union

import requests
from lxml import etree


class Order:
    url = 'https://fahrkarten.bahn.de/mobile/dbc/xs.go'

    def __init__(self, order_id: str, **kwargs):
        self.order_id: str = order_id
        self.lastname: Optional[str] = kwargs.get('lastname')
        self.outward_legs: List[Leg] = kwargs.get('outward_legs', [])
        self.return_legs: List[Leg] = kwargs.get('return_legs', [])
        self.tickets: List[Ticket] = kwargs.get('tickets', [])
        self.bahncard: Optional[BahnCard] = kwargs.get('bahncard')
        self.category: Optional[OrderCategory] = kwargs.get('category')

    def get(self):
        """
        Requests the current Order and updates the details

        :return: The current Order
        """
        self.parse_xml(self.request_order())

        return self

    def request_order(self) -> str:
        """
        Creates the Order-Request

        :return: The body of the response
        """
        xml = f'<rqorder on="{self.order_id}"/><authname tln="{self.lastname}"/>'

        tnr = random.getrandbits(64)
        ts = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        request_body = f'<rqorderdetails version="2.0"><rqheader tnr="{tnr}" ts="{ts}" v="19100000" d="iPhone10,' \
                       f'4" os="iOS_13.1.3" app="NAVIGATOR"/>{xml}</rqorderdetails>'
        response = requests.post(self.url, data=request_body)

        return response.content

    def parse_xml(self,
                  content: Union[str,
                                 bytes,
                                 etree._Element,
                                 etree._ElementTree]):
        """
        Parses the XML-Tree of an Order

        :param content: The XML-Content that should be parsed
        """
        if isinstance(content, (str, bytes)):
            tree = etree.fromstring(content)
        elif isinstance(content, (etree._Element, etree._ElementTree)):
            tree = content
        else:
            raise TypeError()

        self.category = OrderCategory(int(tree.find('order').attrib['fkat']))

        if self.category == OrderCategory.BAHNCARD:
            raise NotImplementedError()
        elif self.category == OrderCategory.TICKET:
            for ticket_tree in tree.find('order').find(
                    'tcklist').findall('tck'):
                self.tickets.append(Ticket().parse_xml(ticket_tree))
            for leg_tree in tree.find('order').find('schedulelist').find(
                    'out').find('trainlist').findall('train'):
                self.outward_legs.append(Leg().parse_xml(leg_tree))
            for leg_tree in tree.find('order').find('schedulelist').find(
                    'ret').find('trainlist').findall('train'):
                self.return_legs.append(Leg().parse_xml(leg_tree))


def get(order_id: str, lastname: str) -> Order:
    """
    Requests the Order/Ticket

    :param order_id: Order-Number of the ticket (e.g. R8U4GK)
    :param lastname: Last name of the traveller
    :return: The requested Order
    """
    return Order(order_id, lastname=lastname).get()


class OrderCategory(Enum):
    TICKET = 5
    BAHNCARD = 7

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


class Ticket:
    def __init__(self, **kwargs):
        self.lastname: Optional[str] = kwargs.get('lastname')
        self.forename: Optional[str] = kwargs.get('forename')
        self.issuer: Optional[int] = kwargs.get('issuer')
        self.description: Optional[str] = kwargs.get('description')
        self.serial_number: Optional[str] = kwargs.get('serial_number')
        self.return_serial_number: Optional[str] = kwargs.get(
            'return_serial_number')
        self.flex_fare: Optional[bool] = kwargs.get('flex_fare')

    def parse_xml(self,
                  content: Union[str,
                                 bytes,
                                 etree._Element,
                                 etree._ElementTree]):
        """
        Parses the XML-Tree of a Ticket

        :param content: The XML-Content that should be parsed
        :return: The parsed Ticket
        """
        if isinstance(content, (str, bytes)):
            tree = etree.fromstring(content)
        elif isinstance(content, (etree._Element, etree._ElementTree)):
            tree = content
        else:
            raise TypeError()

        mtk = tree.find('mtk')

        self.forename = mtk.find('reisender_vorname').text
        self.lastname = mtk.find('reisender_nachname').text
        self.issuer = mtk.find('iss').text
        self.description = mtk.find('txt').text
        self.serial_number = mtk.find("ot_nr_hin").text
        if mtk.find("ot_nr_rueck") is not None:
            self.return_serial_number = mtk.find("ot_nr_rueck").text
        self.flex_fare = mtk.find("zb").text == "N"

        # TODO: Parse nvplist
        # TODO: Parse bc
        # TODO: Parse htdata

        return self


class Leg:
    def __init__(self, **kwargs):
        self.number: Optional[str] = kwargs.get('number')
        self.kind: Optional[str] = kwargs.get('kind')
        self.self_checkin: Optional[bool] = kwargs.get('self_checkin')
        self.departure: Optional[StopOver] = kwargs.get('departure')
        self.arrival: Optional[StopOver] = kwargs.get('arrival')

    def parse_xml(self,
                  content: Union[str,
                                 bytes,
                                 etree._Element,
                                 etree._ElementTree]):
        """
        Parses the XML-Tree of a Leg

        :param content: The XML-Content that should be parsed
        :return: The parsed Leg
        """
        if isinstance(content, (str, bytes)):
            tree = etree.fromstring(content)
        elif isinstance(content, (etree._Element, etree._ElementTree)):
            tree = content
        else:
            raise TypeError()

        self.kind = tree.find('gat').text
        self.number = tree.find('zugnr').text
        self.self_checkin = tree.find('sci').text == 'Y'

        self.departure = StopOver().parse_xml(tree.find('dep'))
        self.arrival = StopOver().parse_xml(tree.find('arr'))

        return self


class StopOver:
    def __init__(self, **kwargs):
        self.datetime: Optional[datetime.datetime] = kwargs.get('datetime')
        self.station_name: Optional[str] = kwargs.get('station_name')
        self.station_number: Optional[str] = kwargs.get('station_number')
        self.station_plz: Optional[str] = kwargs.get('station_plz')
        self.station_x: Optional[str] = kwargs.get('station_x')
        self.station_y: Optional[str] = kwargs.get('station_y')
        self.platform: Optional[str] = kwargs.get('platform')

    def parse_xml(self,
                  content: Union[str,
                                 bytes,
                                 etree._Element,
                                 etree._ElementTree]):
        """
        Parses the XML-Tree of a StopOver

        :param content: The XML-Content that should be parsed
        :return: The parsed StopOver
        """
        if isinstance(content, (str, bytes)):
            tree = etree.fromstring(content)
        elif isinstance(content, (etree._Element, etree._ElementTree)):
            tree = content
        else:
            raise TypeError()

        self.datetime = datetime.datetime.fromisoformat(
            'T'.join([tree.attrib['dt'].split('T')[0], tree.attrib['t']]))
        self.station_name = tree.find('n').text
        self.station_number = tree.find('nr').text
        self.station_x = tree.find('x').text
        self.station_y = tree.find('y').text
        if tree.find('plz') is not None:
            self.station_plz = tree.find('plz').text
        if tree.find('ptf') is not None:
            self.platform = tree.find('ptf').text

        return self


class Reservation:
    def __init__(self, **kwargs):
        raise NotImplementedError()


class BahnCard:
    def __init__(self, **kwargs):
        raise NotImplementedError()
