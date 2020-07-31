#!/usr/bin/env python
# -*- coding: utf-8 -*-

def http_error_handler(http_status_code):

    '''Displays reason for http status code

    Args:
        http_status_code (int): The status code output by the request

    Return:
        None: Don't raise any exception if the status code isn't any of these.
              (for now)
    '''

    if http_status_code == 400:
        raise Exception("400: The URL parameters or the JSON body in the"
                         "request are invalid.")
    elif http_status_code == 401:
        raise Exception("401: The request requires user authentication.")
    elif http_status_code == 404:
        raise Exception("404: The requested resource is not found.")
    elif http_status_code == 403:
        raise Exception("403: You do not have access to this call")
    elif http_status_code == 500:
        raise Exception("500: Servers refuse to work. Either systems are not"
                         "operational, or it is a service bug which is worth a"
                         "report at"
                         "https://github.com/mapillary/mapillary_issues")
    else:
        return None
