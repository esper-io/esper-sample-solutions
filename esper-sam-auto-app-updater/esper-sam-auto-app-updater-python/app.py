import json
import os
import re

from esper.esper import EsperAutoAppUpdater


def create_return_json(http_code, body_dict):
    """Returns json that is acceptable for the API gateway to interpret the
    results and pass it on to the caller.
    
    Arguments:
        http_code {int} -- [description]
        body_dict {dict} -- [description]
    
    Returns:
        dict -- dict that can be converted to json for sending back to the API gateway
    """
    retval = {
        "statusCode": http_code,
        "body": json.dumps(body_dict)
    }
    return retval


def extract_body(event):
    """Extracts the body of the event for which this lambda is called.
    
    Arguments:
        event {dict} -- The event as received by this lambda handler
    
    Returns:
        dict -- JSON of the body, or None if the body cannot be found
    """
    body = None
    if 'body' in event:
        body = json.loads(event['body'])
    return body


def get_device_id_from_body(body):
    """Extracts the device ID from the given body.
    
    Arguments:
        body {dict} -- The body as extracted by `extract_body()`
    
    Returns:
        str -- The device ID if given. If there's an error extracting this
               or if the id is malformed, None is returned.
    """
    if 'device_id' in body:
        device_id = body['device_id']
        if re.match("^[a-zA-Z0-9]{3,4}-[a-zA-Z0-9]{3,4}-[a-zA-Z0-9]{4}$", device_id):
            return device_id
    return None


def get_pkg_from_body(body):
    """Extracts the pkg name from the given body.
    
    Arguments:
        body {dict} -- The body as extracted by `extract_body()`
    
    Note:
        https://stackoverflow.com/questions/40772067/regular-expression-matching-android-package-name

    Returns:
        str -- The pkg name if given. If there's an error extracting this
               or if the name is malformed, None is returned.
    """
    if 'pkg' in body:
        pkg = body['pkg']
        if re.match("^([a-zA-Z]{1}[a-zA-Z\d_]*\.)+[a-zA-Z][a-zA-Z\d_]*$", pkg):
            return pkg
    return None


def get_build_number_from_body(body):
    """Extracts the build number from the given body.
    
    Arguments:
        body {dict} -- The body as extracted by `extract_body()`
    
    Returns:
        str -- The build number if given. If there's an error extracting this
               or if the build number is malformed, None is returned.
    """
    if 'build_number' in body:
        build_number = body['build_number']
        if re.match("^[1-9][0-9]*$", build_number):
            return build_number
    return None


def lambda_handler(event, context):
    """The main handler for the lambda.
    
    Arguments:
        event {dict} -- See AWS docs
        context {dict} -- See AWS docs
    
    Returns:
        str -- JSON string of the handler's results.
    """

    #
    # Extract env vars, and make sure they exist
    #
    epname = os.environ.get('EP_NAME')
    if epname is None:
        return create_return_json(500, {"status": "Request failed", "reason": "Bad environment: endpoint name"})
    print(f"Env: epname - {epname}")

    api_key = os.environ.get('API_KEY')
    if api_key is None:
        return create_return_json(500, {"status": "Request failed", "reason": "Bad environment: esper api creds"})

    eid = os.environ.get('ENT_ID')
    if eid is None:
        return create_return_json(500, {"status": "Request failed", "reason": "Bad environment: enterprise id"})

    # This handler will be called via a POST call. So extract the body for the given payload.
    body = extract_body(event)
    if body is None:
        return create_return_json(400, {"status": "Request failed", "reason": "Bad post payload"})

    #
    # Extract required payload parms
    #
    device_id = get_device_id_from_body(body)
    if device_id is None:
        return create_return_json(400, {"status": "Request failed",
                                        "reason": "Payload is missing Device ID, or the device ID is malformed"})
    print(f"POST: device_id - {device_id}")

    pkg = get_pkg_from_body(body)
    if pkg is None:
        return create_return_json(400, {"status": "Request failed",
                                        "reason": "Payload is missing pakage name, or the package name is malformed"})
    print(f"POST: pkg - {pkg}")

    build_number = get_build_number_from_body(body)
    if pkg is None:
        return create_return_json(400, {"status": "Request failed",
                                        "reason": "Payload is missing build number, or the build number is malformed"})
    print(f"POST: build_number - {build_number}")

    # finally use the EsperAutoUpdater class to do the honors and return the results
    eaau = EsperAutoAppUpdater(epname, api_key, eid)
    status, msg = eaau.push_latest_app_version_if_needed(pkg, device_id, build_number)

    if "Succeeded" == status:
        return create_return_json(200, {"status": "Request succeeded", "msg": msg})
    else:
        return create_return_json(400, {"status": "Request failed", "msg": msg})
