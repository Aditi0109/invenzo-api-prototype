from flask import Flask, request, jsonify
from mongoengine import connect, ValidationError
from models import Item
import os

app = Flask(__name__)

# Connect explicitly to local MongoDB internship_dummy_db
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/internship_dummy_db")
connect(host=MONGO_URI)


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
        # Support optional pagination and search query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 0))  # 0 means no limit
        search_query = request.args.get('search', '')

        # Build base queryset
        if search_query:
            query_set = Item.objects(name__icontains=search_query)
        else:
            query_set = Item.objects()

        total_items = query_set.count()

        # Apply pagination if limit > 0
        if limit > 0:
            skip_amount = (page - 1) * limit
            query_set = query_set.skip(skip_amount).limit(limit)

        result = []
        for it in query_set:
            result.append({
                'id': str(it.id),
                'name': it.name,
                'category': it.category,
                'quantity': it.quantity
            })

        # If pagination was requested, return metadata
        if limit > 0:
            return jsonify({
                'totalItems': total_items,
                'currentPage': page,
                'itemsPerPage': limit,
                'data': result
            }), 200

        return jsonify(result), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)