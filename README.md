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
*    `gen_plaintext`: Generate and send a plaintext version of the template as well as the html version (true/false). (requres the [`html2text`](https://pypi.python.org/pypi/html2text) module)

The following options are optional and only used if `gen_plaintext` is enabled:
*    `unicode_snob`: Use Unicode characters instead of their ascii psuedo-replacements (true/false, default false).
*    `escape_snob`: Escape all special characters (true/false, default false) Output is less readable, but avoids corner case formatting issues.
*    `links_each_paragraph`: Put the links after each paragraph instead of at the end (true/false, default false).
*    `body_width`: Wrap long lines at this position. 0 for no wrapping, default 78.
*    `skip_internal_links`: Don't show internal links (`href="#local-anchor"`) (default true).
*    `inline_links`: Use inline, rather than reference, formatting for images and links (default true).
*    `ignore_links`: Ignore all anchor tags (default false).
*    `ignore_images`: Ignore all imgage tags (default false).
*    `ignore_emphasis`: Ignore all emphasis tags (default false).
*    `ul_item_mark`: The string to begin list items with (default `*`).
*    `emphasis_mark`: The string to surround emphasized text with (default `_`).
*    `strong_mark`: The string to surround bolded text with (default `**`).

Server
--------------------
The server section holds the data needed to actually send the email.

The following options need to be configured:
*    `smtp`: The SMTP server, gmail is smtp.gmail.com.
*    `user`: The username to log in with.
*    `pass`: The password for the above username.
*    `port`: The port to use.
*    `ssl`:  Use SSL to deliver the message (true/false).
*    `tls`:  Use TLS to encrypt the  message (true/false).
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
*	Numbers wrapped in curly braces (`{}`) in the subject or contents will be replaced with the corresponding argument.
*	For example, a template of `{0} - {2} - {1}` becomes `a - c - b` when given arguments of `a b c`.
*	If there aren't enough arguments, the string `[NO DATA]` is substituted.

A template config has the format `id: [email_subject, template_file]`

Config example:
```json
"templates":{
    "general": ["Incoming Notification", "general.html"],
    "data":    ["Incoming Datafile", "data.html"],
    "movie":   ["Incoming Movie ({1})", "movie.html"],
    "music":   ["Incoming Music ({1})", "music.html"]
}
```

Template file example (`templates/general.html`):
```html
General: '{0}': <em>{1}</em>, <b>{2}</b>
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
        "tls":     false,
        "fr_addr": "notifybot@example.com",
        "fr_name": "Notifications"
    },
    "templates":{
        "general": ["Incoming Notification", "general.html"],
        "data":    ["Incoming Datafile", "data.html"],
        "movie":   ["Incoming Movie ({1})", "movie.html"],
        "music":   ["Incoming Music ({1})", "music.html"]
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
`general.html`:
```html
General: '{0}': <em>{1}</em>, <b>{2}</b>
```

`data.html`:
```html
Data in file '{2}'
```

`movie.html`:
```html
Movie called '{1}' at '{2}'
```

`music.html`:
```html
Music called '{1}' at '{2}'
```

Results
-------
*    `./emailNotify.py "n/a" "testing.dat" "/home/test/testing.dat"`
    *    test1@example.com:
        *    Subject: Incoming Datafile
        *    Contents: Data in file: '/home/test/testing.dat'
    *    test2@example.com:
        *    Subject: Incoming Notification
        *    Contents: General: 'n/a': <em>testing.dat</em>, <b>/home/test/testing.dat</b>

*    `./emailNotify.py "Label_movie" "My movie" "/home/test/video.mkv"`
    *    test1@example.com: Not sent an email.
    *    test2@example.com:
        *    Subject: Incoming Movie (My Movie)
        *    Contents: Movie called 'My Movie' at '/home/test/video.mkv'

*    `./emailNotify.py "Label_music" "My Song" "/home/test/music.mp3"`
    *    test1@example.com:
        *    Subject: Incoming Music (My Song)
        *    Contents: Music called 'My Song' at '/home/test/testing.dat'
    *    test2@example.com:
        *    Subject: Incoming Notification
        *    Contents: General: 'Label_music': <em>My Song</em>, <b>/home/test/music.mp3</b>
