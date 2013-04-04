#!/usr/bin/python3

import json
import sys
import logging

CONFIG_FILE = "config.dat"

class Template(object):
    """Represents a template"""

    def __init__(self, subject, contents):
        self.subject = subject
        self.contents = contents

    def get_filled(self, args):
        """Returns the filled out template"""
        #TODO: error handling
        return self.contents.format(args)

class Item(object):
    """Represents an item"""

    def __init__(self, id_, conditions, template):
        self.id_ = id_
        self.conditions = conditions
        self.template = template

    def does_match(self, args):
        """Returns true if this item matches the arguments"""
        #TODO: logic
        return False

    def get_template(self, args):
        """
        Returns the filled out template for this item.
        Returns None if the conditions don't match the args.
        """
        if self.does_match(args):
            return template.get_filled(args)
        return None

    def __eq__(self, other):
        return self.id_ == other.id_

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "{0}: {1}".format(self.id_, str(self.conditions))


class User(object):
    """Represents a user"""

    def __init__(self, items):
        self.items = items

    def get_match(self, args):
        """Returns the first item to match the args (or None)."""
        for x in items:
            if x.does_match(args):
                return x
        return None


def load_config():
    """Load configuration data"""
    try:
        with open (CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config
    except EnvironmentError as e:
        logging.critical("Couldn't open config file, does it exist? " + str(e))
    except ValueError as e:
        logging.critical("Couldn't parse JSON, check the config file: " + str(e))
    return None


def send_email(server_conf, people, template, args):
    """Sends the email"""
    #TODO: create message, add data, send it
    pass

def process_args(users, args):
    """Figures out which emails to send to which people"""
    #TODO: Collect identical items, group users, call send_email
    pass

def build_structure(config):
    """
    Builds the data structure.
    Returns a list of users.
    """
    #build templates
    templates = {}
    for key, val in config["templates"].items():
        templates[key] = Template(*val)

    #build items
    items = {}
    for key, val in config["items"].items():
        try:
            tmpl = templates[val[1]]
        except KeyError as e:
            logging.warn("Problem with config file - invalid template '{0}'. Skipping item '{1}'...".format(val[1], key))
            continue
        items[key] = Item(key, val[0], tmpl)

    #build users
    users = {}
    for key, val in config["users"].items():
        user_items = []
        for i in val:
            try:
                user_items.append(items[i])
            except KeyError as e:
                logging.warn("Problem with config file - invalid item '{0}' for user '{1}'".format(i, key))
        users[key] = User(user_items) 
    
    return users
        

def main():
    """Entry point of the program"""
    logging.basicConfig(format="[%(asctime)s][%(levelname)s][in %(funcName)s]: %(message)s", level=logging.DEBUG)

    if len(sys.argv) == 1:
        #TODO: print help
        return

    config = load_config()
    if not config:
        return

    users = build_structure(config)

    #Debug
    for email, user in users.items():
        print (email, str(user.items))
        for item in user.items:
            print (str(item.template))

    process_args(users, sys.argv[1:])
        

if __name__ == '__main__':
    main()


