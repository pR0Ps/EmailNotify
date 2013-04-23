#!/usr/bin/python3

import json
import sys
import logging
import string
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
html2text = None

CONFIG_FILE = "config.dat"
TEMPLATE_DIR = "templates"
ARG_PLACEHOLDER = "[NO DATA]"

VALID_H2T_OPTS = ("unicode_snob", "escape_snob", "links_each_paragraph", "body_width",
                "skip_internal_links", "inline_links", "ignore_links","ignore_images",
                "ignore_emphasis", "ul_item_mark", "emphasis_mark", "strong_mark")

CONFIG_REQS = ("general", "server", "templates", "items", "users")
CONFIG_GEN_REQS = ["gen_plaintext"]
CONFIG_SERVER_REQS = ("smtp", "user", "pass", "port", "ssl", "tls", "fr_addr", "fr_name")

class ConfigError(Exception):
    pass

class Template(object):
    """Represents a template"""

    def __init__(self, id_, subject, filename):
        self.id_ = id_
        self.subject = subject

        self._load_file(filename)
        self._check_valid()

    def _load_file(self, filename):
        """Loads the contents of the template file"""
        try:
            path = os.path.join(TEMPLATE_DIR, filename)
            logging.debug("Loading template '{0}' from file '{1}'".format(self.id_, path))
            with open (os.path.join(HOME_DIR, path), "r") as f:
                self.contents = f.read()
        except EnvironmentError as e:
            raise ConfigError("Couldn't load template '{0}': {1}".format(self.id_, e))

    def _check_valid(self):
        """
        Determines if the template is a valid.
        Templates can only have numbers as placeholders.
        """
        logging.debug("Checking if template '{0}' is valid".format(self.id_))
        for i in range(2):
            for x in string.Formatter().parse((self.subject, self.contents)[i]):
                #x[1] is the name of each placeholder
                try:
                    int(x[1])
                except ValueError:
                    raise ConfigError("Invalid placeholder '{{{0}}}' in template {1}".format(x[1], ("subject", "file")[i]))
                except TypeError:
                    #x[1] is None, this is fine
                    pass

    def _num_placeholders(self):
        """Returns the number of placeholders needed to fill in the template"""
        return max({int(x[1]) for x in string.Formatter().parse(self.contents + self.subject) if x[1]}) + 1

    def get_filled(self, args):
        """Returns the filled out template as a (subject, contents) tuple"""
        num = self._num_placeholders()
        to_add = num - len(args)

        logging.debug("Filling out template '{0}': {1} placeholder(s), {2} arg(s) provided".format(self.id_, num, len(args)))

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
        logging.debug("Compiling conditions to regular expression objects")

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

        if not any(self.conditions):
            logging.debug("No conditions found")
            self.conditions = []
        
    def does_match(self, args):
        """Returns true if this item matches the arguments"""
        
        logging.debug("Checking if item matches. Conditions: {0} Args: {1}".format([p.pattern for p in self.conditions], args))

        #Less args than conditions, can't match
        if len(args) < len(self.conditions):
            logging.debug("Item doesn't match - more conditions than args")
            return False

        #Check the conditions
        if not self.conditions:
            logging.debug("No conditions, therefore item matches")
            return True
        else:
            for i in range(len(self.conditions)):
                if self.conditions[i] and not self.conditions[i].match(args[i]):
                    logging.debug("Item doesn't match - condition {0} ('{1}') doesn't match arg '{2}'".format(i, self.conditions[i].pattern, args[i]))
                    return False
        
        logging.debug("All item conditions match")
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
        logging.debug("Building template '{0}'".format(id_))
        try:
            templates[id_] = Template(id_, *data)
        except ConfigError as e:
            logging.warn("Problem with config file - {0}. Skipping template '{1}'".format(e, id_))

    #build items
    logging.info("Building items...")
    items = {}
    for id_, data in config["items"].items():
        logging.debug("Building item '{0}'".format(id_))
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
        logging.debug("Building user '{0}'".format(email))
        user_items = []

        for item_id in item_ids:
            try:
                user_items.append(items[item_id])
            except KeyError as e:
                logging.warn("Problem with config file - Invalid item '{0}' for user '{1}'".format(item_id, email))

        #Check for duplicates
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
        with open (os.path.join(HOME_DIR, CONFIG_FILE), "r") as f:
            config = json.load(f)

            logging.debug("Checking all config sections are present")
            if not all(k in config for k in CONFIG_REQS):
                logging.critical("Incomplete configuration file")
                return None
            
            logging.debug("Checking all 'general' configuration options are present")
            if not all(k in config["general"] for k in CONFIG_GEN_REQS):
                logging.critical("Incomplete general configuration")
                return None
            
            logging.debug("Checking all 'server' configuration options are present")
            if not all(k in config["server"] for k in CONFIG_SERVER_REQS):
                logging.critical("Incomplete server configuration")
                return None

            return config
    except EnvironmentError as e:
        logging.critical("Couldn't open config file, does it exist? {0}".format(e))
    except ValueError as e:
        logging.critical("Couldn't parse JSON, check the config file: {0}".format(e))
    return None

def generate_plaintext(conf, html):
    """Returns a plaintext version of the template"""

    logging.debug("Generating a plaintext version of:\n{0}".format(html))

    h = html2text.HTML2Text()

    #Set a subset of relevant options for html2text parser
    for opt in VALID_H2T_OPTS:
        if opt in conf:
            setattr(h, opt, conf[opt])

    ret = h.handle(html)
    logging.debug("Generated plaintext:\n{0}".format(ret))
    return ret

def send_email(conf, server, items, args):
    """Sends the email"""

    #Check if actually sending anything
    if not items:
        logging.info("No emails to send")
        return

    #Log into the SMTP server
    logging.info("Connecting to the SMTP server...")

    try:
        if server["ssl"]:
            smtp_server = smtplib.SMTP_SSL(server["smtp"], server["port"])
        else:
            smtp_server = smtplib.SMTP(server["smtp"], server["port"])
    except (EnvironmentError, smtplib.SMTPException) as e:
        logging.critical("Couldn't make a connection to the SMTP server: {0}".format(e))
        return

    if server["user"] and server["pass"]:
        logging.debug("Logging into the SMTP server")

        try:
            if server["tls"]:
                logging.debug("Attempting to use TLS")
                smtp_server.ehlo()
                smtp_server.starttls()
                smtp_server.ehlo()

            smtp_server.login(server["user"], server["pass"])
        except smtplib.SMTPException as e:
            logging.critical("Couldn't log into the SMTP server: {0}".format(e.args[1]))
            return

    logging.info("Sending email(s)...")

    for item, emails in items.items():

        logging.debug("Setting up email object")

        subject, text = item.template.get_filled(args)

        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = "{0} <{1}>".format(server["fr_name"], server["fr_addr"])
        
        #Add text - According to RFC 2046 the last attached part is preferred (HTML)
        if conf["gen_plaintext"]:
            msg.attach(MIMEText(generate_plaintext(conf, text).encode('utf-8'), 'plain', _charset='utf-8'))
        msg.attach(MIMEText(text.encode('utf-8'), 'html', _charset='utf-8'))

        logging.info("Sending template '{0}' to '{1}'...".format(item.template.id_, ", ".join(emails)))

        try:
            smtp_server.sendmail(server["fr_addr"], emails, msg.as_string())
            logging.info("Sent!")
        except smtplib.SMTPException as e:
            logging.warning ("Error while sending: {1}".format(e.args[1]))
            continue


    logging.info("Finished sending emails")
    smtp_server.quit()

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
    """Start processing"""

    logging.debug("Detected script directory: {0}".format(HOME_DIR))

    config = load_config()
    
    if len(sys.argv) == 1:
        print ("EmailNotify by pR0Ps")
        print ("See README.md for usage instructions")
        if not config:
            logging.critical("Couldn't load config data, program will not run")
        return

    args = sys.argv[1:]
    
    if not config:
        logging.critical("Couldn't load config data, exiting")
        return

    if config["general"]["gen_plaintext"]:
        logging.debug("Plaintext option enabled, attempting to load the 'html2text' module")
        try:
            global html2text
            import html2text
            logging.debug("Loaded 'html2text' module successfully")
        except ImportError as e:
            logging.warning("Couldn't load 'html2text' module, no plaintext email will be generated")
            config["general"]["gen_plaintext"] = False

    users = build_structure(config)
    to_send = process_args(users, args)

    send_email(config["general"], config["server"], to_send, args)
        

if __name__ == '__main__':
    """Entry point of the program"""
    global HOME_DIR

    try:
        HOME_DIR = os.path.dirname(os.path.abspath(__file__))
    except EnvironmentError as e:
        print("WARNING: Couldn't get the directory the script is in: {0}".format(e))
        HOME_DIR = "."
        
    #logging.basicConfig(filename=os.path.join(HOME_DIR, "EmailNotify.log"), format="[%(asctime)s][%(levelname)s]: %(message)s", level=logging.WARN)
    logging.basicConfig(format="[%(asctime)s][%(levelname)s]: %(message)s", level=logging.DEBUG)

    main()
