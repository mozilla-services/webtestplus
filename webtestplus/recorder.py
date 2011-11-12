from warnings import warn
from webtest import TestRequest, TestResponse


def _matching(asked, stored):
    if asked.method != stored.method:
        return False

    if asked.path_info != stored.path_info:
        return False

    if asked.method not in ('GET', 'DELETE'):
        return asked.body == stored.body

    return True


def _read_recs(filename, req_class=TestRequest,
               resp_class=TestResponse):
    recs = []

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

            # reading the request
            req = req_class.from_file(f)

            line = f.readline()
            if not line.strip():
                line = f.readline()


            if not line:
                recs.append(req)

            line = line.strip()
            if not line:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
            if not line.startswith('--Response:'):
                warn('Invalid line (--Response: expected) at byte %s in %s'
                     % (f.tell(), f))

            resp = resp_class.from_file(f)
            resp.request = req
            req.response = resp
            recs.append(req)

    return recs


def get_record(filename, request, ):

    recs = _read_recs(filename)
    for rec in recs:
        if _matching(request, rec):
            return rec.response
