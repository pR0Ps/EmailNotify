#!/usr/bin/python3

import json
import sys
import logging
import string
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_FILE = "config.dat"
ARG_PLACEHOLDER = "[NO DATA]"

class ConfigError(Exception):
    pass

class Template(object):
    """Represents a template"""

    def __init__(self, id_, subject, contents):
        self.id_ = id_
        self.subject = subject
        self.contents = contents

        self._check_valid()

    def _check_valid(self):
        """
        Determines if the template is a valid.
        Templates can only have numbers as placeholders.
        """
        for i in range(2):
            for x in string.Formatter().parse((self.subject, self.contents)[i]):
                #x[1] is the name of each placeholder
                try:
                    int(x[1])
                except ValueError:
                    raise ConfigError("Invalid placeholder '{{{0}}}' in template {1}".format(x[1], ("subject", "contents")[i]))
                except TypeError:
                    #x[1] is None, this is fine
                    pass

    def _num_placeholders(self):
        """Returns the number of placeholders needed to fill in the template"""
        return max({int(x[1]) for x in string.Formatter().parse(self.contents + self.subject) if x[1]}) + 1

    def get_filled(self, args):
        """Returns the filled out template as a (subject, contents) tuple"""
        to_add = self._num_placeholders() - len(args)

        temp_args = args[:]

        #Extend the args to match the number of placeholders
        if to_add > 0:
            logging.warning("Inserting placeholder '{0}' into template '{1}' ({2} too few arguments provided).".format(ARG_PLACEHOLDER, self.id_, to_add))
            temp_args.extend(to_add * [ARG_PLACEHOLDER])

        return (self.subject.format(*temp_args), self.contents.format(*temp_args))

class Item(object):
    """Represents an item"""

    def __init__(self, id_, conditions, template):
        self.id_ = id_
        self.template = template

        self._parse_conditions(conditions)

    def _parse_conditions(self, conditions):
        """Converts the conditions to regex objects"""
        self.conditions = []
        if conditions:
            for x in conditions:
                if not x:
                    self.conditions.append(None)
                else:
                    try:
                        self.conditions.append(re.compile(x))
                    except Exception as e:
                        raise ConfigError("Invalid condition '{0}' in item contents ({1})".format(x, e))
        
    def does_match(self, args):
        """Returns true if this item matches the arguments"""

        #Less args than conditions, can't match
        if len(args) < len(self.conditions):
            return False

        #Check the conditions
        for i in range(len(self.conditions)):
            if self.conditions[i] and not self.conditions[i].match(args[i]):
                return False
        
        return True

    def __eq__(self, other):
        return self.id_ == other.id_

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id_)

class User(object):
    """Represents a user"""

    def __init__(self, items):
        self.items = items

    def get_match(self, args):
        """Returns the first item to match the args (or None)."""
        for item in self.items:
            if item.does_match(args):
                return item
        return None

def build_structure(config):
    """
    Builds the data structure.
    Returns a list of users.
    """
    
    logging.info("Building data structure...")
    

    #build templates
    logging.info("Building templates...")
    templates = {}
    for id_, data in config["templates"].items():
        try:
            templates[id_] = Template(id_, *data)
        except ConfigError as e:
            logging.warn("Problem with config file - {0}. Skipping template '{1}'".format(e, id_))

    #build items
    logging.info("Building items...")
    items = {}
    for id_, data in config["items"].items():
        try:
            template = templates[data[1]]
            items[id_] = Item(id_, data[0], template)
        except KeyError as e:
            logging.warn("Problem with config file - Invalid template '{0}'. Skipping item '{1}'".format(data[1], id_))
        except ConfigError as e:
            logging.warn("Problem with config file - {0}. Skipping item '{1}'".format(e, id_))

    #build users
    logging.info("Building users...")
    users = {}
    for email, item_ids in config["users"].items():
        user_items = []
        for item_id in item_ids:
            try:
                user_items.append(items[item_id])
            except KeyError as e:
                logging.warn("Problem with config file - Invalid item '{0}' for user '{1}'".format(item_id, email))
        
        if len(set(user_items)) != len(user_items):
            logging.warn("Problem with config file - Duplicate items for user '{0}'".format(email))
        
        users[email] = User(user_items)

    
    return users

def load_config():
    """
    Load configuration data.
    Returns a dictionary representation of the config file.
    Does basic error checking.
    """
    logging.info("Loading the configuration file...")

    try:
        with open (CONFIG_FILE, "r") as f:
            config = json.load(f)

            #Check all sections are present
            if not all(k in config for k in ("server", "templates", "items", "users")):
                logging.critical("Incomplete configuration file")
                return None
            
            #check all server options are present
            if not all(k in config["server"] for k in ("smtp", "user", "pass", "port", "ssl", "tls", "fr_addr", "fr_name")):
                logging.critical("Incomplete server configuration")
                return None

            return config
    except EnvironmentError as e:
        logging.critical("Couldn't open config file, does it exist? {0}".format(e))
    except ValueError as e:
        logging.critical("Couldn't parse JSON, check the config file: {0}".format(e))
    return None

def send_email(conf, items, args):
    """Sends the email"""

    #Check if actually sending anything
    if not items:
        logging.info("No emails to send")
        return

    #Log into the SMTP server
    logging.info("Logging into the SMTP server...")

    try:
        if conf["ssl"]:
            server = smtplib.SMTP_SSL(conf["smtp"], conf["port"])
        else:
            server = smtplib.SMTP(conf["smtp"], conf["port"])
    except (EnvironmentError, smtplib.SMTPException) as e:
        logging.critical("Couldn't make a connection to the SMTP server: {0}".format(e))
        return

    if conf["user"] and conf["pass"]:
        if conf["tls"]:
            server.ehlo()
            server.starttls()
            server.ehlo()

        try:
            server.login(conf["user"], conf["pass"])
        except smtplib.SMTPException as e:
            logging.critical("Couldn't log into the SMTP server: {0}".format(e.args[1]))
            return

    logging.info("Sending email(s)...")
    
    for item, emails in items.items():

        subject, text = item.template.get_filled(args)

        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = "{0} <{1}>".format(conf["fr_name"], conf["fr_addr"])
        msg["Bcc"] = ", ".join(emails)
        msg.attach(MIMEText(text.encode('utf-8'), 'html', _charset='utf-8'))

        logging.info("Sending template '{0}' to '{1}'...".format(item.template.id_, msg["Bcc"]))

        try:
            server.sendmail(conf["fr_addr"], emails, msg.as_string())
            logging.info("Sent!")
        except smtplib.SMTPException as e:
            logging.warning ("Error while sending: {1}".format(e.args[1]))
            continue


    logging.info("Finished sending emails")
    server.quit()

def process_args(users, args):
    """
    Figures out which emails to send to which people.
    Returns a dictionary containing a list of users to email
    with the keys being the item that matched.
    """

    logging.info("Determining which emails to send to which users...")

    to_send = {}

    for email, user in users.items():
        item = user.get_match(args)
        if item:
            if not item in to_send:
                to_send[item] = []

            to_send[item].append(email)

    return to_send
        

def main():
    """Entry point of the program"""

    logging.basicConfig(format="[%(asctime)s][%(levelname)s]: %(message)s", level=logging.DEBUG)

    if len(sys.argv) == 1:
        print ("EmailNotify by pR0Ps")
        print ("See README.md for usage instructions")
        return

    args = sys.argv[1:]
    config = load_config()
    
    if not config:
        logging.critical("Couldn't load config, exiting")
        return

    users = build_structure(config)
    to_send = process_args(users, args)

    send_email(config["server"], to_send, args)
        

if __name__ == '__main__':
    main()
