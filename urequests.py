# Minimal HTTP client for MicroPython (subset of micropython-lib's urequests)

import usocket


class Response:
    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None

    @property
    def content(self):
        if self._cached is None:
            self._cached = self.raw.read()
            self.raw.close()
            self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)


def request(method, url, data=None, headers={}):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""

    if proto == "http:":
        port = 80
    elif proto == "https:":
        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    ai = ai[0]

    s = usocket.socket(ai[0], ai[1], ai[2])
    try:
        s.connect(ai[-1])
        if proto == "https:":
            import ussl
            s = ussl.wrap_socket(s, server_hostname=host)

        s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
        s.write(b"Host: %s\r\n" % host)
        for k in headers:
            s.write(k.encode())
            s.write(b": ")
            s.write(headers[k].encode())
            s.write(b"\r\n")
        if data:
            s.write(b"Content-Length: %d\r\n" % len(data))
        s.write(b"\r\n")
        if data:
            s.write(data)

        l = s.readline()
        l = l.split(None, 2)
        status = int(l[1])
        while True:
            l = s.readline()
            if not l or l == b"\r\n":
                break
    except OSError:
        s.close()
        raise

    resp = Response(s)
    resp.status_code = status
    return resp


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, data=None, **kw):
    return request("POST", url, data=data, **kw)
