"""
Send out email for Friday's lunch.
"""
import argparse
import datetime
import pathlib
import smtplib
import ssl
import sys
import urllib.request
from email.message import EmailMessage
from string import Template
from ruamel.yaml import YAML, YAMLError


def load_yaml(fname: str) -> dict:
    """Get configuration from file.

    Args:
        fname (str): Name of YAML file

    Returns:
        dict: Configuration from file. The configuration contains data
            necessary to format and to send the data. See the config.yaml
            example file for expected keys and documentation.
    """
    cfg = YAML(typ='safe')
    try:
        data = cfg.load(pathlib.Path(fname))
    except YAMLError as exc:
        print(exc)
        sys.exit()
    return data


def get_lunch_location(url: str, date: str) -> str:
    """
    Retrieve location of lunch for given date from URL.

    File contains lines of data the following format:
    yyyy-mm-dd  Location of lunch for this date

    Ex:
    2023-05-05  Cafe Joe on National Business Pkwy

    Args:
        url (str): Location of the lunch data file.
        date (str): Date of lunch to retrieve

    Returns:
        str: Location of lunch for that date
    """
    data = urllib.request.urlopen(url)
    for line in data:
        desc = line.decode('utf-8')  # 'line' is a bytestring.
        if desc.startswith(date):
            return desc[len(date):].strip()
    return None


def find_next_friday() -> str:
    """Return date of next Friday. If today is Friday, return today.

    Returns:
        str: Friday's date in the format of "yyyy-mm-dd".
    """
    today = datetime.date.today()
    current_weekday = today.weekday()
    days_ahead = (4 - current_weekday) % 7  # 4 represents Friday (Monday is 0).
    next_friday = today + datetime.timedelta(days=days_ahead)
    return str(next_friday)


def send_ssl_email(cfg: dict, body: str):
    """Send an SSL email

    Args:
        cfg (dict): Configuration info for sending (to, from, server, port)
        body (str): Text of message to send
    """
    msg = EmailMessage()
    msg["to"] = cfg["to"]
    msg["from"] = cfg["user"]
    msg['Subject'] = cfg["subject"]
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg["server"], cfg["port"], context=ctx) as smtp:
        smtp.login(cfg["user"], cfg["pwd"])
        smtp.send_message(msg)
        print('Email sent!!')


def get_args():
    """
    Define and parse arguments from command line.

    Returns:
        Arguments object
    """
    p = argparse.ArgumentParser()

    p.add_argument('config_file', type=str, help='path of configuration file')
    args = p.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()
    cfg = load_yaml(args.config_file)
    print(cfg['to'])
    data = {}  # Holds entries that may be used from the template in config.
    data['date'] = find_next_friday()
    uri = cfg['lunchfile']
    data['loc'] = get_lunch_location(uri, data['date'])
    if data['loc'] != None:
        t = Template(cfg['template'])
        body = t.substitute(data)
        print(body)
        send_ssl_email(cfg, body)
    else:
        print(f'Cannot find date {data["date"]} at beginning of a line')
        print(f'in {uri}. Lunch message NOT sent!!!!')
        exit()
