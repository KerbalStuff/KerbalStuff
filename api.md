# Kerbal Stuff API Docs

Kerbal Stuff has a simple HTTP API that you can use to do various interesting
things. Feel free to help make it better by submitting pull requests that update
[api.py](https://github.com/SirCmpwn/KerbalStuff/blob/master/KerbalStuff/blueprints/api.py).

## API Wrappers

[Ruby API Wrapper, by RockyTV](https://github.com/RockyTV/KerbalStuffGem)

## Basics

Submit all POSTS with the request body encoded as
[multipart/form-data](https://www.ietf.org/rfc/rfc2388.txt). Your HTTP library
of choice probably handles that for you. All responses are JSON.

Changes to this API will happen occasionally and warning will be offered via an
email sent to all registered modders on the website and on the forum thread.

Please set your user agent to something that describes who you are and how to
contact the person operating the service.

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

    curl -F username=SirCmpwn -F password=example -c ./cookies "http://beta.kerbalstuff.com/api/login"

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

## Search

You can search the site without authentication.

**GET /api/search/mod?query=\<name>**

Searches the site for mods.

*Curl*

    curl "http://beta.kerbalstuff.com/api/search/mod?query=FAR"

*Parameters*

* `query`: Search terms

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
        "short_description": "..."
      }
    ]

**GET /api/search/user?query=\<name>**

Searches the site for public users.

*Curl*

    curl "http://beta.kerbalstuff.com/api/search/user?query=sircmpwn"

*Parameters*

* `query`: Search terms

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

    curl "http://beta.kerbalstuff.com/api/user/Xaiier"

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

    curl "http://beta.kerbalstuff.com/api/mod/21"

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
      "id": 21,
      "short_description": "..."
    }

**GET /api/mod/\<mod_id>/latest**

Returns the latest version of a mod.

*Curl*

    curl "http://beta.kerbalstuff.com/api/mod/21/latest"

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
        "http://beta.kerbalstuff.com/api/mod/create"

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
        "http://beta.kerbalstuff.com/api/mod/1234/update"

*Parameters*

* `version`: The friendly version number about to be created
* `changelog`: Markdown changelog
* `ksp-version`: The version of KSP this is compatible with
* `notify-followers`: If "yes", email followers about this update
* `zipball`: The actual mod's zip file
