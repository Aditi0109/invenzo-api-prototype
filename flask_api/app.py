from flask import Flask, request, jsonify
from mongoengine import connect, ValidationError
from models import Item

app = Flask(__name__)

# Connect explicitly to local MongoDB internship_dummy_db
connect(host='mongodb://127.0.0.1:27017/internship_dummy_db')


@app.route('/', methods=['GET'])
def index():
    return 'API is running smoothly!'


# 1. POST Endpoint: Insert new data
@app.route('/api/items', methods=['POST'])
def create_item():
    try:
        # Parse JSON like express.json() — require valid JSON body
        data = request.get_json()
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400

    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    try:
        new_item = Item(
            name=data.get('name'),
            category=data.get('category'),
            quantity=data.get('quantity')
        )
        new_item.save()

        item_dict = {
            'id': str(new_item.id),
            'name': new_item.name,
            'category': new_item.category,
            'quantity': new_item.quantity
        }

        return jsonify(item_dict), 201
    except ValidationError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as err:
        return jsonify({'error': str(err)}), 500


# 2. GET Endpoint: Fetch all data
@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        items = Item.objects()
        result = []
        for it in items:
            result.append({
                'id': str(it.id),
                'name': it.name,
                'category': it.category,
                'quantity': it.quantity
            })
        return jsonify(result), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
