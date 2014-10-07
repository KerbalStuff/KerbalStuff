# Kerbal Stuff API Docs

Kerbal Stuff has a simple HTTP API that you can use to do various interesting
things. Feel free to help make it better by submitting pull requests that update
[api.py](https://github.com/SirCmpwn/KerbalStuff/blob/master/KerbalStuff/blueprints/api.py).

## API Wrappers

* [Ruby API Wrapper, by RockyTV](https://github.com/RockyTV/KerbalStuffGem)
* [KerbalStuffWrapper, in C#, by toadicus.](http://forum.kerbalspaceprogram.com/threads/94891)

## Basics

Submit all POSTS with the request body encoded as
[multipart/form-data](https://www.ietf.org/rfc/rfc2388.txt). Your HTTP library
of choice probably handles that for you. All responses are JSON.

Changes to this API will happen occasionally and warning will be offered via an
email sent to all registered modders on the website and on the forum thread.

Please set your user agent to something that describes who you are and how to
contact the person operating the service.

**Note on mod backgrounds**: The background image for each mod is hosted on
https://mediacru.sh. The string returned in API requests is the path to that
image relative to cdn.mediacru.sh - so if the path was "/example.png", the
image can be found at "https://cdn.mediacru.sh/example.png".

### Errors

All requests that might fail include an `error` property in the response, which
is a boolean that will be true if the request failed. If the request failed, a
`reason` property will also be included that explains why it failed.

## Authentication

Some endpoints require authentication. To authenticate, use the login endpoint
and you will be given a cookie, which you should include in all subsequent
requests.

**POST /api/login**

Logs into Kerbal Stuff.

*Curl*

    curl -F username=SirCmpwn -F password=example -c ./cookies "https://kerbalstuff.com/api/login"

*Parameters*

* `username`
* `password`

*Example Response*

Successful login:

    {
        "error": false
    }

Failed login:

    {
        "error": true,
        "reason": "Username or password is incorrect"
    }

## Browse

You can browse the site without authentication.

**GET /api/browse/new?page=<integer>**

Gets the newest mods on the site.

*Curl*

    curl "https://kerbalstuff.com/api/browse/new"

*Parameters*

* `page`: Which page of results to retrieve (1 indexed) [*optional*]

*Example Response*:

    [
      {
        "downloads": 27885,
        "name": "Ferram Aerospace Research",
        "followers": 177,
        "author": "ferram4",
        "default_version_id": 295,
        "versions": [
          {
            "changelog": "...",
            "ksp_version": "0.24.2",
            "download_path": "/mod/52/Ferram%20Aerospace%20Research/download/v0.14.1.1",
            "id": 151,
            "friendly_version": "v0.14.1.1"
          }
        ],
        "id": 52,
        "background": "...",
        "bg_offset_y": 1234,
        "short_description": "..."
      },
      ...continued...
    ]


**GET /api/browse/featured?page=<integer>**

Gets the latest featured mods on the site.

*Curl*

    curl "https://kerbalstuff.com/api/browse/featured"

*Parameters*

* `page`: Which page of results to retrieve (1 indexed) [*optional*]

*Example Response*:

    [
      {
        "downloads": 27885,
        "name": "Ferram Aerospace Research",
        "followers": 177,
        "author": "ferram4",
        "default_version_id": 295,
        "versions": [
          {
            "changelog": "...",
            "ksp_version": "0.24.2",
            "download_path": "/mod/52/Ferram%20Aerospace%20Research/download/v0.14.1.1",
            "id": 151,
            "friendly_version": "v0.14.1.1"
          }
        ],
        "id": 52,
        "background": "...",
        "bg_offset_y": 1234,
        "short_description": "..."
      },
      ...continued...
    ]

**GET /api/browse/top?page=<integer>**

Gets the most popular mods on the site.

*Curl*

    curl "https://kerbalstuff.com/api/browse/top"

*Parameters*

* `page`: Which page of results to retrieve (1 indexed) [*optional*]

*Example Response*:

    [
      {
        "downloads": 27885,
        "name": "Ferram Aerospace Research",
        "followers": 177,
        "author": "ferram4",
        "default_version_id": 295,
        "versions": [
          {
            "changelog": "...",
            "ksp_version": "0.24.2",
            "download_path": "/mod/52/Ferram%20Aerospace%20Research/download/v0.14.1.1",
            "id": 151,
            "friendly_version": "v0.14.1.1"
          }
        ],
        "id": 52,
        "background": "...",
        "bg_offset_y": 1234,
        "short_description": "..."
      },
      ...continued...
    ]

## Search

You can search the site without authentication.

**GET /api/search/mod?query=\<name>**

Searches the site for mods.

*Curl*

    curl "https://kerbalstuff.com/api/search/mod?query=FAR"

*Parameters*

* `query`: Search terms
* `page`: Which page of results to retrieve (1 indexed) [*optional*]

*Example Response*:

    [
      {
        "downloads": 27885,
        "name": "Ferram Aerospace Research",
        "followers": 177,
        "author": "ferram4",
        "default_version_id": 295,
        "versions": [
          {
            "changelog": "...",
            "ksp_version": "0.24.2",
            "download_path": "/mod/52/Ferram%20Aerospace%20Research/download/v0.14.1.1",
            "id": 151,
            "friendly_version": "v0.14.1.1"
          }
        ],
        "id": 52,
        "background": "...",
        "bg_offset_y": 1234,
        "short_description": "..."
      }
    ]

**GET /api/search/user?query=\<name>**

Searches the site for public users.

*Curl*

    curl "https://kerbalstuff.com/api/search/user?query=sircmpwn"

*Parameters*

* `query`: Search terms
* `page`: Which page of results to retrieve (1 indexed) [*optional*]

*Example Response*

    [
      {
        "username": "SirCmpwn",
        "twitterUsername": "sircmpwn",
        "mods": [],
        "redditUsername": "",
        "ircNick": "sircmpwn",
        "description": "Hi, I made this website.",
        "forumUsername": "SirCmpwn"
      }
    ]

## Users

You can query the API for information on individual public users.

**GET /api/user/\<username>**

Returns information about a specific user.

*Curl*

    curl "https://kerbalstuff.com/api/user/Xaiier"

*Example Response*

    {
      "username": "Xaiier",
      "twitterUsername": "",
      "mods": [
        {
          "downloads": 332,
          "name": "Time Control",
          "followers": 19,
          "author": "Xaiier",
          "default_version_id": 371,
          "id": 21,
          "short_description": "..."
        }
      ],
      "redditUsername": null,
      "ircNick": "Xaiier",
      "description": "",
      "forumUsername": "Xaiier"
    }

## Mods

You can query the API for information on a specific mod, a specific version, and
so on. This could be useful, for example, to implement an update checker. You can
also use the API to create new mods or update existing ones.

**GET /api/mod/\<mod_id>**

Returns information about a specific mod.

*Curl*

    curl "https://kerbalstuff.com/api/mod/21"

*Example Response*

    {
      "downloads": 332,
      "name": "Time Control",
      "followers": 19,
      "author": "Xaiier",
      "default_version_id": 371,
      "versions": [
        {
          "changelog": "...",
          "ksp_version": "0.24.2",
          "download_path": "/mod/21/Time%20Control/download/13.0",
          "id": 371,
          "friendly_version": "13.0"
        }
      ],
      "background": "...",
      "bg_offset_y": 1234,
      "description:" "...markdown...",
      "description_html": "...html...",
      "id": 21,
      "short_description": "...",
      "updated": "...date/time..."
    }

**GET /api/mod/\<mod_id>/latest**

Returns the latest version of a mod.

*Curl*

    curl "https://kerbalstuff.com/api/mod/21/latest"

*Example Response*

    {
      "changelog": "...",
      "ksp_version": "0.24.2",
      "download_path": "/mod/21/Time%20Control/download/13.0",
      "id": 371,
      "friendly_version": "13.0"
    }

**POST /api/mod/create**

Creates a new mod. **Requires authentication**.

*Curl*

    curl -c ./cookies \
        -F" name=Example Mod" \
        -F "short-description=this is your schort description" \
        -F "version=1.0" \
        -F "ksp-version=0.24" \
        -F "license=GPLv2" \
        -F "zipball=@ExampleMod.zip" \
        "https://kerbalstuff.com/api/mod/create"

*Parameters*

* `name`: Your new mod's name
* `short-description`: Short description of your mod
* `version`: The latest friendly version of your mod
* `ksp-version`: The KSP version this is compatible with
* `license`: Your mod's license
* `zipball`: The actual mod's zip file

*Example Response*

    {
      "url": "/mod/1234/Example Mod"
    }

*Notes*

This creates an unpublished mod. You must log into the actual site to publish
your mod.

**POST /api/mod/\<mod_id>/update**

Publishes an update to an existing mod. **Requires authentication**.

*Curl*

    curl -c ./cookies \
        -F "version=1.0" \
        -F "changelog=this is your changelog" \
        -F "ksp-version=0.24" \
        -F "notify-followers=yes" \
        -F "zipball=@ExampleMod.zip" \
        "https://kerbalstuff.com/api/mod/1234/update"

*Parameters*

* `version`: The friendly version number about to be created
* `changelog`: Markdown changelog
* `ksp-version`: The version of KSP this is compatible with
* `notify-followers`: If "yes", email followers about this update
* `zipball`: The actual mod's zip file
