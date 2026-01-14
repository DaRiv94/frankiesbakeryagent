import azure.functions as func
import logging
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="get_products", methods=["GET"])
def get_products(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Frankie\'s Bakery - Get Products function processed a request.')

    # Demo products for Frankie's Bakery
    products = [
        {"id": 1, "name": "Chocolate Chip Cookies", "price": 8.99, "category": "Cookies"},
        {"id": 2, "name": "Sourdough Bread", "price": 6.50, "category": "Bread"},
        {"id": 3, "name": "Blueberry Muffins", "price": 12.99, "category": "Muffins"},
        {"id": 4, "name": "Cinnamon Rolls", "price": 10.99, "category": "Pastries"},
        {"id": 5, "name": "Croissants", "price": 9.99, "category": "Pastries"},
        {"id": 6, "name": "Apple Pie", "price": 18.99, "category": "Pies"},
        {"id": 7, "name": "Banana Bread", "price": 7.99, "category": "Bread"},
        {"id": 8, "name": "Red Velvet Cupcakes", "price": 15.99, "category": "Cupcakes"}
    ]

    return func.HttpResponse(
        json.dumps(products, indent=2),
        mimetype="application/json",
        status_code=200
    )

@app.route(route="place_order", methods=["POST"])
def place_order(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Frankie\'s Bakery - Place Order function processed a request.')

    try:
        req_body = req.get_json()
        product_name = req_body.get('product_name')
        product_quantity = req_body.get('product_quantity')

        if not product_name or not product_quantity:
            return func.HttpResponse(
                json.dumps({"error": "Please provide both product_name and product_quantity"}),
                mimetype="application/json",
                status_code=400
            )

        response = {
            "message": f"Order confirmed! You ordered {product_quantity} of {product_name}. Thank you for your business!",
            "order_details": {
                "product": product_name,
                "quantity": product_quantity
            }
        }

        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            mimetype="application/json",
            status_code=400
        )