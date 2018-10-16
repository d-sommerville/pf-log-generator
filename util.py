import string
from random import randint, random, choice, getrandbits
from ipaddress import IPv4Network, IPv4Address
from datetime import datetime, timedelta


def timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]


def seconds_until(t=0):
    """
    Given an hour in 24-hour time, return the number of seconds until that hour.

    :param t: Integer from 0-23
    """
    d, t = divmod(t, 24)
    now = datetime.now()
    target = datetime(year=now.year, month=now.month, day=now.day, hour=t)
    if t < now.hour:
        target += timedelta(days=1)
    return round(target.timestamp() - now.timestamp())


class Mock:

    HOSTS = [
        'solsyspingfed1',
        'solsyspingfed2',
        'solsyspingfed3',
        'solsyspingfed4',
        'solsyspingfed5',
        'solsyspingfed6',
        'solsyspingfed7',
        'solsyspingfed8',
        'solsyspingfed9',
        'solsyspingfed10'
    ]

    SUBNETS = [
        IPv4Network("10.0.0.0/8"),
        IPv4Network("172.16.0.0/12"),
        IPv4Network("192.168.0.0/16"),
        IPv4Network("169.254.0.0/16")
    ]

    FIRST_NAMES = [
        'duncan',
        'santosh',
        'darren',
        'jeremy',
        'ryoji',
        'steve',
        'doug',
        'alan',
        'john',
        'jim'
    ]

    LAST_NAMES = [
        'sommerville',
        'krishna',
        'fuller',
        'adams',
        'betchaku',
        'manuel',
        'brown',
        'burns',
        'tobin',
        'liu'
    ]

    EMAIL_DOMAINS = [
        'gmail.com',
        'solsys.ca',
        'yahoo.ca',
        'hotmail.com',
        'mail.com',
        'aol.com'
    ]

    OAUTH_CLIENTS = [
        'analyzer',
        'portal'
        'api',
        'solsys_connect',
        'connect_api',
        'plethora',
        'solsys_showcase',
        'datafy',
        'conceptr',
        'jira',
        'remedy',
        'cloudera',
        'aws',
        'azure',
        'gcp',
        'fortify',
        'bitbucket'
    ]

    ADAPTERS = [
        'HTMLFormSimplePCV',
        'LDAPAuthenticator',
        'KerberosAuthenticator',
        'IWAAuth'
    ]

    @staticmethod
    def tid():
        return ''.join(choice(string.ascii_letters + string.digits + '-_') for _ in range(27))

    @staticmethod
    def response_time():
        return randint(5, 100) if random() < 0.95 else randint(1000, 5000)

    @staticmethod
    def host():
        return choice(Mock.HOSTS)

    @staticmethod
    def ip_address():
        subnet = choice(Mock.SUBNETS)
        bits = getrandbits(subnet.max_prefixlen - subnet.prefixlen)
        return str(IPv4Address(subnet.network_address + bits))

    @staticmethod
    def user():
        return '%s.%s@%s' % (choice(Mock.FIRST_NAMES), choice(Mock.LAST_NAMES), choice(Mock.EMAIL_DOMAINS))

    @staticmethod
    def client():
        return choice(Mock.OAUTH_CLIENTS)

    @staticmethod
    def adapter():
        return choice(Mock.ADAPTERS)
