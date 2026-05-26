from mongoengine import Document, StringField, IntField


class Item(Document):
    name = StringField(required=False)
    category = StringField(required=False)
    quantity = IntField(required=False)

    meta = {'collection': 'items',
            'strict': False}
