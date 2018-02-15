import Pyro4

Pyro4.config.SERIALIZER = 'pickle'


def PyroVectors(uri):
    return Pyro4.Proxy(uri)
