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

General
---------------------
General program options

The following options need to be configured:
*   `gen_html`: Generate and send an HTML version of the template as well as the markdown version (`true`/`false`). (requres the [markdown](https://pypi.python.org/pypi/Markdown) module).
*   `append_date`: Forces emails to be displayed in seperate threads by appending the current date and time to the subject line (`true`/`false`).

Other options related to markdown processing can be set here. See the [Markdown documentation](http://pythonhosted.org/Markdown/reference.html#markdown) for a list of options.

Example:
```json
"general":{
    "gen_html": true,
    "append_date": true,
    "output_format": "html4"
}
```

Server
--------------------
The server section holds the data needed to actually send the email.

The following options need to be configured:
*   `smtp`: The SMTP server, gmail is `smtp.gmail.com`.
*   `user`: The username to log in with.
*   `pass`: The password for the above username.
*   `port`: The port to use.
*   `ssl`:  Use SSL to deliver the message (`true`/`false`).
*   `tls`:  Use TLS to encrypt the  message (`true`/`false`).
*   `fr_addr`: The address the email will send from.
*   `fr_name`: The name the email will report.

Example:
```json
"server":{
    "smtp":    "smtp.example.com",
    "user":    "username",
    "pass":    "password",
    "port":    465,
    "ssl":     true,
    "tls":     false,
    "fr_addr": "notifybot@example.com",
    "fr_name": "Notifications"
}
```

Templates
---------
A template gets filled in using the arguments passed to program, then emailed to users.

Due to their length, the contents of the templates are stored in individual files in the `templates` subdirectory.

Formatting:
*   Numbers wrapped in curly braces (`{}`) in the subject or contents will be replaced with the corresponding argument.
*   This replacement is subject to normal Python formating syntax.
*   For example, a template of `{0} - {2:=^10} - {1:.3}` becomes `aaaaaa - ==cccccc== - bbb` when given arguments of `aaaaaa bbbbbb cccccc`.
*   If there aren't enough arguments, the string `[NO DATA]` is substituted.

A template config has the format `id: [email_subject, template_file]`

Config example:
```json
"templates":{
    "general": ["Incoming Notification", "general.md"],
    "data":    ["Incoming Datafile", "data.md"],
    "movie":   ["Incoming Movie ({1})", "movie.md"],
    "music":   ["Incoming Music ({1})", "music.md"]
}
```

Template file example (`templates/general.md`):
```
General: '{0}': _{1}_, __{2}__
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
*   If there are less arguments than there are conditions, the item will not match.
*   If there are less conditions than there are arguments, the extra arguments will be ignored (the item can still match).
*   By extension, if there are no conditionals (`[]` or `null`), the item will always match.

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
    "general":{
        "gen_html": true,
        "append_date": true,
        "output_format": "html4"
    },
    "server":{
        "smtp":    "smtp.example.com",
        "user":    "username",
        "pass":    "password",
        "port":    465,
        "ssl":     true,
        "tls":     false,
        "fr_addr": "notifybot@example.com",
        "fr_name": "Notifications"
    },
    "templates":{
        "general": ["Incoming Notification", "general.md"],
        "data":    ["Incoming Datafile", "data.md"],
        "movie":   ["Incoming Movie ({1})", "movie.md"],
        "music":   ["Incoming Music ({1})", "music.md"]
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

Template files
--------------
`general.md`:
```
General: '{0}': _{1}_, __{2}__
```

`data.md`:
```
Data in file '{2}'
```

`movie.md`:
```
Movie called '{1}' at '{2}'
```

`music.md`:
```
Music called '{1}' at '{2}'
```

Results
-------
*   `./emailNotify.py "n/a" "testing.dat" "/home/test/testing.dat"`
    *   test1@example.com:
        *   Subject: Incoming Datafile - Jan 01 00:00:00
        *   Contents: Data in file: '/home/test/testing.dat'
    *   test2@example.com:
        *   Subject: Incoming Notification - Jan 01 00:00:00
        *   Contents: General: 'n/a': _testing.dat_, __/home/test/testing.dat__

*   `./emailNotify.py "Label_movie" "My movie" "/home/test/video.mkv"`
    *   test1@example.com: Not sent an email.
    *   test2@example.com:
        *   Subject: Incoming Movie (My Movie) - Jan 01 00:00:00
        *   Contents: Movie called 'My Movie' at '/home/test/video.mkv'

*   `./emailNotify.py "Label_music" "My Song" "/home/test/music.mp3"`
    *   test1@example.com:
        *   Subject: Incoming Music (My Song) - Jan 01 00:00:00
        *   Contents: Music called 'My Song' at '/home/test/testing.dat'
    *   test2@example.com:
        *   Subject: Incoming Notification - Jan 01 00:00:00
        *   Contents: General: 'Label_music': _My Song_, __/home/test/music.mp3__
