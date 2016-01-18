# How to configure OAuth

All OAuth integrations require that you have a "domain" configured.

In addition, you'll need to register an Application with each OAuth partner
(Provider), and update a shared secret in `config.ini`.

## GitHub

Go to Settings -> (select the relevant Organization if applicable) ->
Applications -> Developer Applications -> Register New Application.

The first three fields are public information, and the last one - "Authorization
 callback URL" - is where GitHub will send users after the login. Set it to:

    <protocol>://<domain>/oauth/github/

For example, for KerbalStuff.com, it would be `https://kerbalstuff.com/oauth/github/`.

Once you register, you'll get a "Client ID" and "Client Secret"; Set these values
in config.ini as `gh-oauth-id` and `gh-oauth-secret` respectively.

