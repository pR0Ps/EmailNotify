EmailNotify
===========

Allows for sending customizable email notifications.


Usage
=====
Call the script with as many parameters as needed.
All the parameters will be checked against the conditions of the items.
If the conditions of the items match, an email will be sent out.

Format specification: `./emailNotify.py [data, ...]`

Configuration
=============

Server Configuration
--------------------
The server section holds the data needed to actually send the email.

The following parameters need to be configured:
*    `smtp`: The SMTP server, gmail is smtp.gmail.com.
*    `user`: The username to log in with.
*    `pass`: The password for the above username.
*    `port`: The port to use.
*    `ssl`:  Use SSL to deliver message? (true/false)
*    `fr_addr`: The address the email will send from.
*    `fr_name`: The name the email will report.

Example:
```json
"server":{
    "smtp":    "smtp.example.com",
    "user":    "username",
    "pass":    "password",
    "port":    465,
    "ssl":     true,
    "fr_addr": "notifybot@example.com",
    "fr_name": "Notifications"
}
```

Templates
---------
A template gets filled in using the arguments passed to progream, then emailed to users.


Numbers wrapped in curly braces (`{}`) will be replaced with the corresponding argument.

For example, a template of `{0} - {2} - {1}` becomes `a - c - b` when given arguments of `a b c`.

If there aren't enough arguments, the string `[NO DATA]` is substituted.

A template config has the format `id: [email_subject, email_contents]`

Example:
```json
"templates":{
    "general": ["Incoming Notification", "General: '{0}', '{1}', '{2}'"],
    "data":    ["Incoming Datafile", "Data in file '{2}'"],
    "movie":   ["Incoming Movie", "Movie called '{1}' at '{2}'"],
    "music":   ["Incoming Music", "Music called '{1}' at '{2}'"]
}
```

Conditions
----------
A condition is a regular expression that is matched against the provided arguments.

The condition is considered to be met if the arguments match the regular expression, OR if the condition is null.

Note that JSON uses the `\` character to designate escape sequences. If the backslash character is needed in your condition (or anywhere else), use `\\`.

Example: `".*\\.dat$"`

Items
-----
An item is a set of conditions that must be met in order for the user to be emailed, as well as the template to email if all the conditions match.

The specified conditions are matched directly from the arguments (the first argument matches the first condition, etc).

Special cases:
*    If there are less arguments than there are conditions, the item will not match.
*    If there are less conditions than there are arguments, the extra arguments will be ignored (the item can still match).
*    By extension, if there are no conditionals (`[]` or `null`), the item will always match.

An item config has the format `id: [[condition, ...], template_id]`

Example:
```json
"items":{
    "all":        [null, "general"],
    "datafiles":  [[null, ".*\\.dat$"], "data"],
    "moviefiles": [["Label_movie"], "movie"],
    "musicfiles": [["Label_music"], "music"]
}
```

Users
-----
A user is a person to send emails to.

They have an email address and a list of items to check. Items will be checked for a match in the order they are listed. Only the first matching item is processed.

A user config has the format `email: [item_id, ...]`

Example:
```json
"users":{
    "test1@example.com": ["datafiles", "musicfiles"],
    "test2@example.com": ["moviefiles", "all"]
}
```
Example
=======

Configuration file
------------------
```json
{
    "server":{
        "smtp":    "smtp.example.com",
        "user":    "username",
        "pass":    "password",
        "port":    465,
        "ssl":     true,
        "fr_addr": "notifybot@example.com",
        "fr_name": "Notifications"
    },
    "templates":{
        "general": ["Incoming Notification", "General: '{0}', '{1}', '{2}'"],
        "data":    ["Incoming Datafile", "Data in file '{2}'"],
        "movie":   ["Incoming Movie", "Movie called '{1}' at '{2}'"],
        "music":   ["Incoming Music", "Music called '{1}' at '{2}'"]
    },
    "items":{
        "all":        [null, "general"],
        "datafiles":  [[null, ".*\\.dat$"], "data"],
        "moviefiles": [["Label_movie"], "movie"],
        "musicfiles": [["Label_music"], "music"]
    },
    "users":{
        "test1@example.com": ["datafiles", "musicfiles"],
        "test2@example.com": ["moviefiles", "all"]
    }
}
```

Results
-------
*    `./emailNotify.py "n/a" "testing.dat" "/home/test/testing.dat"`
    *    test1@example.com:
        *    Subject: "Incoming Datafile"
        *    Contents: "Data in file: '/home/test/testing.dat'"
    *    test2@example.com:
        *    Subject: "Incoming Notification"
        *    Contents: "General: 'n/a', 'testing.dat', '/home/test/testing.dat'"

*    `./emailNotify.py "Label_movie" "My movie" "/home/test/video.mkv"`
    *    test1@example.com: Not sent an email.
    *    test2@example.com:
        *    Subject: "Incoming Movie"
        *    Contents: "Movie called 'My Movie' at '/home/test/video.mkv'"

*    `./emailNotify.py "Label_music" "My Song" "/home/test/music.mp3"`
    *    test1@example.com:
        *    Subject: "Incoming Music"
        *    Contents: "Music called 'My Song' at '/home/test/testing.dat'"
    *    test2@example.com:
        *    Subject: "Incoming Notification"
        *    Contents: "General: 'Label_music', 'My Song', '/home/test/music.mp3'"
