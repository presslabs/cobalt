from flask_restful import fields


class PrefixRemovedString(fields.String):
    def __init__(self, prefix='', *args, **kwargs):
        super(PrefixRemovedString, self).__init__(*args, **kwargs)
        self.prefix = prefix

    def format(self, value):
        value = super(PrefixRemovedString, self).format(value)
        if value.startswith(self.prefix):
            return value[len(self.prefix):]
