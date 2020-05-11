
class NodeError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
        
class LanguageError(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message