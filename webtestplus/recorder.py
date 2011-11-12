from warnings import warn
from webtest import TestRequest, TestResponse


def get_record(filename, pos=0, RequestClass=TestRequest,
               ResponseClass=TestResponse):

    current = 0
    with open(filename, 'rb') as f:
        while 1:
            line = f.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                # Because we add a newline at the end of the request, a
                # blank line is likely here:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
            if not line.startswith('--Request:'):
                warn('Invalid line (--Request: expected) at byte %s in %s'
                     % (f.tell(), f))

            req = RequestClass.from_file(f)
            line = f.readline()
            if not line.strip():
                line = f.readline()

            if not line:
                return req

            line = line.strip()
            if not line:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
            if not line.startswith('--Response:'):
                warn('Invalid line (--Response: expected) at byte %s in %s'
                     % (f.tell(), f))

            resp = ResponseClass.from_file(f)
            resp.request = req
            req.response = resp
            if current == pos:
                return resp
            current += 1
