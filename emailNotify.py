#!/usr/bin/python3

import json
import sys
import logging
import string
import re

CONFIG_FILE = "config.dat"
ARG_PLACEHOLDER = "[NO DATA]"


class ConfigError(Exception):
    pass

class Template(object):
    """Represents a template"""

    def __init__(self, subject, contents):
        self.subject = subject
        self.contents = contents

        self._check_valid()

    def _check_valid(self):
        """
        Determines if the template is a valid.
        Templates can only have numbers as placeholders.
        """
        for x in string.Formatter().parse(self.contents):
            #x[1] is the name of each placeholder
            if x[1]:
                try:
                    int(x[1])
                except ValueError:
                    raise ConfigError("Invalid placeholder '{{{0}}}' in template contents".format(x[1]))

    def _num_placeholders(self):
        """Returns the number of placeholders needed to fill in the template"""
        return max({int(x[1]) for x in string.Formatter().parse(self.contents) if x[1]}) + 1

    def get_filled(self, args):
        """Returns the filled out template"""
        num = self._num_placeholders()

        #Extend the args to match the nmber of placeholders
        if len(args) < num:
            args.extend((num - len(args)) * [ARG_PLACEHOLDER])

        return self.contents.format(args)

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
        return "{0}: {1}".format(self.id_, self.conditions)


class User(object):
    """Represents a user"""

    def __init__(self, items):
        self.items = items

    def get_match(self, args):
        """Returns the first item to match the args (or None)."""
        for x in self.items:
            if x.does_match(args):
                return x
        return None

def build_structure(config):
    """
    Builds the data structure.
    Returns a list of users.
    """
    #build templates
    templates = {}
    for id_, data in config["templates"].items():
        try:
            templates[id_] = Template(*data)
        except ConfigError as e:
            logging.warn("Problem with config file - {0}. Skipping template '{1}'".format(e, id_))

    #build items
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
    users = {}
    for email, item_ids in config["users"].items():
        user_items = []
        for item_id in item_ids:
            try:
                user_items.append(items[item_id])
            except KeyError as e:
                logging.warn("Problem with config file - Invalid item '{0}' for user '{1}'".format(item_id, email))
        users[email] = User(user_items) 
    
    return users

def load_config():
    """
    Load configuration data.
    Returns a dictionary of User objects.
    """
    try:
        with open (CONFIG_FILE, "r") as f:
            config = json.load(f)
            return build_structure(config)
    except EnvironmentError as e:
        logging.critical("Couldn't open config file, does it exist? {0}".format(e))
    except ValueError as e:
        logging.critical("Couldn't parse JSON, check the config file: {0}".format(e))
    return None


def send_email(server_conf, people, template, args):
    """Sends the email"""
    #TODO: create message, add data, send it
    pass

def process_args(users, args):
    """Figures out which emails to send to which people"""
    for email, user in users.items():
        item = user.get_match(args)

        #Debug
        if item:
            print (email + ":" + item.template.subject)

        

def main():
    """Entry point of the program"""
    logging.basicConfig(format="[%(asctime)s][%(levelname)s][in %(funcName)s]: %(message)s", level=logging.DEBUG)

    if len(sys.argv) == 1:
        #TODO: print help
        return

    users = load_config()
    if not users:
        logging.critical("Couldn't load config, exiting")
        return

    #Debug
    for email, user in users.items():
        print (email, str(user.items))
        for item in user.items:
            print (str(item.template))

    process_args(users, sys.argv[1:])
        

if __name__ == '__main__':
    main()


