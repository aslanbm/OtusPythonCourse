#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Realize scoring API functionality."""

import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class CharField:
    def __init__(self, name, required, nullable):
        self.name = '_' + name
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, value):
        if (value is None) and (self.required):
            raise TypeError("Value is NONE, but this field is required.")
        if (not value) and (not self.nullable):
            raise TypeError("Value is EMPTY, but this field can't isn't nullable.")
        if value and (not isinstance(value, str)):
            raise TypeError(f"Value must be a string. Current type is {type(value)}.")
        setattr(instance, self.name, value)


class ArgumentsField:
    def __init__(self, name, required, nullable):
        self.name = '_' + name
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, value):
        if (value is None) and (self.required):
            raise TypeError("Value is NONE, but this field is required.")
        elif (value == {}) and (not self.nullable):
            raise TypeError("Value is EMPTY, but this field can't isn't nullable.")
        setattr(instance, self.name, value)


class EmailField(CharField):
    def __set__(self, instance, value):
        custom_condition = (
            value
            and isinstance(value, str)
            and ('@' in value)
        )
        if value and (not custom_condition):
            raise TypeError('Value has bad format!')
        super().__set__(instance, value)


class PhoneField:
    def __init__(self, name, required, nullable):
        self.name = '_' + name
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, value):
        custom_condition = (
            (isinstance(value, int) or isinstance(value, str))
            and (len(str(value)) == 11)
            and (str(value)[0] == '7')
        )
        if (value is None) and (self.required):
            raise TypeError("Value is NONE, but this field is required.")
        if (not value) and (not self.nullable):
            raise TypeError("Value is EMPTY, but this field can't isn't nullable.")
        if value and (not custom_condition):
            raise TypeError("Value has bad format.")
        setattr(instance, self.name, value)


class DateField:
    def __init__(self, name, required, nullable):
        self.name = '_' + name
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, date_string):
        if date_string:
            try:
                datetime.datetime.strptime(date_string, '%d.%m.%Y')
            except ValueError:
                raise ValueError("Incorrect data format, should be DD.MM.YYYY")
        setattr(instance, self.name, date_string)


class BirthDayField:
    def __init__(self, name, required, nullable):
        self.name = '_' + name
        self.required = required
        self.nullable = nullable

    @staticmethod
    def check_date_format(date_string, format):
        try:
            datetime.datetime.strptime(date_string, format)
        except:
            return False
        return True

    @staticmethod
    def days_diff(date_string, format):
        d1 = datetime.datetime.strptime(date_string, format)
        d2 = datetime.datetime.now()
        return (d2 - d1).days / 365.0


    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, value):
        custom_condition = (
            value
            and isinstance(value, str)
            and self.check_date_format(value, '%d.%m.%Y')
            and (self.days_diff(value, '%d.%m.%Y') <= 70)
        )

        if (value is None) and (self.required):
            raise TypeError("Value is NONE, but this field is required.")
        if (not value) and (not self.nullable):
            raise TypeError("Value is EMPTY, but this field can't isn't nullable.")
        if value and (not custom_condition):
            raise TypeError("Value has bad format.")

        setattr(instance, self.name, value)


class GenderField:
    def __init__(self, name, required, nullable):
        self.name = '_' + name
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, value):
        if (value is None) and (self.required):
            raise TypeError("Value is NONE, but this field is required.")
        if isinstance(value, int):
            if value not in (0, 1, 2):
                raise ValueError("Value has correct type, but wrong value.")
        else:
            if value is not None:
                raise TypeError("Value must be int, but it's not.")
        setattr(instance, self.name, value)


class ClientIDsField:
    def __init__(self, name, required):
        self.name = '_' + name
        self.required = required

    def __get__(self, instance, cls):
        return getattr(instance, self.name, None)

    def __set__(self, instance, lst):
        custom_condition = (
            lst
            and isinstance(lst, list)
            and all(isinstance(item, int) for item in lst)
        )
        if self.required and not custom_condition:
            raise TypeError("Value must be a list of int.")
        setattr(instance, self.name, lst)


class ClientsInterestsRequest:
    client_ids = ClientIDsField('client_ids', required=True)
    date = DateField('date', required=False, nullable=True)


class OnlineScoreRequest:
    first_name = CharField('first_name', required=False, nullable=True)
    last_name = CharField('last_name', required=False, nullable=True)
    email = EmailField('email', required=False, nullable=True)
    phone = PhoneField('phone', required=False, nullable=True)
    birthday = BirthDayField('birthday', required=False, nullable=True)
    gender = GenderField('gender', required=False, nullable=True)


class MethodRequest:
    account = CharField('account', required=False, nullable=True)
    login = CharField('login', required=True, nullable=True)
    token = CharField('token', required=True, nullable=True)
    arguments = ArgumentsField('arguments', required=True, nullable=True)
    method = CharField('method', required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    """Check authentication of current user."""
    content = None
    if request.is_admin:
        content = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
    else:
        content = request.account + request.login + SALT
    digest = hashlib.sha512(content.encode()).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    """Handle request method: online_score or client_interests."""
    response, code = None, None
    method_request = MethodRequest()
    init_args = ['account', 'login', 'token', 'arguments', 'method']
    bad_args = []
    for arg in init_args:
        try:
            setattr(method_request, arg, request['body'].get(arg))
        except Exception:
            bad_args.append(arg)

    if bad_args:
        return 'INVALID ARGUMENTS: ' + ', '.join(bad_args), INVALID_REQUEST

    if not check_auth(method_request):
        return "FORBIDDEN", FORBIDDEN

    if method_request.method == 'clients_interests':
        clients_interests_request = ClientsInterestsRequest()
        fields = ['client_ids', 'date']
        bad_fields = []
        for field in fields:
            try:
                setattr(clients_interests_request, field, method_request.arguments.get(field))
            except Exception:
                bad_fields.append(field)
        if bad_fields:
            return 'INVALID METHOD FIELDS: ' + ', '.join(bad_fields), INVALID_REQUEST

        client_ids = clients_interests_request.client_ids
        ctx['nclients'] = len(client_ids)
        response = {client_id: get_interests(store, client_id) for client_id in client_ids}
        code = 200
    elif method_request.method == 'online_score':
        online_score_request = OnlineScoreRequest()
        fields = ['phone', 'email', 'birthday', 'gender', 'first_name', 'last_name']
        bad_fields = []
        for field in fields:
            try:
                setattr(online_score_request, field, method_request.arguments.get(field))
            except Exception:
                bad_fields.append(field)
        if bad_fields:
            return 'INVALID METHOD FIELDS: ' + ', '.join(bad_fields), INVALID_REQUEST

        pair_condition = (
            (online_score_request.phone and online_score_request.email)
            or (online_score_request.first_name and online_score_request.last_name)
            or (online_score_request.birthday and (online_score_request.gender is not None))
        )
        if not pair_condition:
            return "No valid pairs for scoring.", INVALID_REQUEST

        ctx['has'] = [field for field in fields if getattr(online_score_request, field, None) is not None]
        cur_score = None
        if method_request.is_admin:
            cur_score = 42
        else:
            arg_list = [getattr(online_score_request, field, None) for field in fields]
            cur_score = get_score(store, *arg_list)

        response = {"score": cur_score}
        code = 200
    else:
        return "INVALID_REQUEST", INVALID_REQUEST
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
            print(request)
        except Exception as e:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode())
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
