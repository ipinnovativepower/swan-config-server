import requests
from flask import Response


def redirect_to_API_HOST(
    request, API_HOST
):  #, path NOTE var :path will be unused as all path we need will be read from :request ie from flask import request
    res = requests.request(  # ref. https://stackoverflow.com/a/36601467/248616
        method=request.method,
        url=request.url.replace(request.host_url, f'{API_HOST}'),
        headers={
            k: v
            for k, v in request.headers if k.lower() not in ['host', 'x-forwarded-for']
        },  # exclude 'host' header
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
    )

    #region exlcude some keys in :res response
    excluded_headers = [
        'content-encoding', 'content-length', 'transfer-encoding', 'connection'
    ]  #NOTE we here exclude all "hop-by-hop headers" defined by RFC 2616 section 13.5.1 ref. https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1
    headers = [(k, v) for k, v in res.raw.headers.items()
               if k.lower() not in excluded_headers]
    #endregion exlcude some keys in :res response

    response = Response(res.content, res.status_code, headers)
    return response
