class Router:
    def __init__(self):
        '''
        routes is a dictionary that stores the the mapping between (method, path) and the handler function
        '''
        self.routes = {}

    def register(self, method, path, handler):
        '''
        This function is used to register a new route
        '''
        self.routes[(method.upper(), path)] = handler

    def resolve(self, method, path):
        '''
        This function is used to resolve the route
        '''
        handler = self.routes.get((method.upper(), path))
        return handler