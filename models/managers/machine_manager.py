from marshmallow import Schema, fields

from .base_manager import BaseManager


class MachineSchema(Schema):
    name = fields.String(required=True)
    max_size = fields.Integer(required=True)
    filled_size = fields.Integer(required=True)
    threshold = fields.Float(required=True, missing=0.8, default=0.8)

machine_schema = MachineSchema()


class MachineManager(BaseManager):
    KEY = 'machines'
    SCHEMA = machine_schema


