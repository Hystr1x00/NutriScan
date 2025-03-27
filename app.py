from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# API 
API_ENDPOINT = "https://world.openfoodfacts.org/cgi/search.pl"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_food():
    food_query = request.form.get('food_query')
    
    if not food_query:
        return jsonify({"error": "Query makanan tidak boleh kosong"}), 400
    
    params = {
        'search_terms': food_query,
        'search_simple': 1,
        'action': 'process',
        'json': 1,
        'page_size': 5 
    }
    
    try:
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()  
        
        data = response.json()
        
        if not data.get('products') or len(data.get('products', [])) == 0:
            return jsonify({"message": "Makanan tidak ditemukan"}), 404
        
        processed_data = []
        for product in data.get('products', []):
            nutrients = product.get('nutriments', {})
            
            calories = nutrients.get('energy-kcal_100g', 0)
            if calories == 0:
                energy_kj = nutrients.get('energy_100g', 0)
                if energy_kj > 0:
                    calories = energy_kj / 4.184 
            
            food_info = {
                'name': product.get('product_name', 'Tidak ada nama'),
                'category': product.get('categories_tags', ['unknown'])[0].replace('en:', '') if product.get('categories_tags') else 'Tidak ada kategori',
                'image_url': product.get('image_url', ''),
                'nutrients': {
                    'calories': round(calories, 2),
                    'protein': round(float(nutrients.get('proteins_100g', 0)), 2),
                    'fat': round(float(nutrients.get('fat_100g', 0)), 2),
                    'carbs': round(float(nutrients.get('carbohydrates_100g', 0)), 2),
                    'fiber': round(float(nutrients.get('fiber_100g', 0)), 2),
                    'sugar': round(float(nutrients.get('sugars_100g', 0)), 2),
                    'salt': round(float(nutrients.get('salt_100g', 0)), 2)
                },
                'serving_size': product.get('serving_size', 'Tidak ada informasi')
            }
            processed_data.append(food_info)
        
        return jsonify(processed_data)
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500

@app.route('/product/<barcode>', methods=['GET'])
def get_product_details(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 1:
            return jsonify({"error": "Produk tidak ditemukan"}), 404
        
        return jsonify(data)
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500

@app.route('/analyze', methods=['GET', 'POST'])
def analyze_food():
    if request.method == 'POST':
        foods = request.json.get('foods', [])
        
        if not foods:
            return jsonify({"error": "Daftar makanan tidak boleh kosong"}), 400
        
        total_nutrients = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbs': 0,
            'fiber': 0,
            'sugar': 0,
            'salt': 0
        }
        
        for food in foods:
            nutrients = food.get('nutrients', {})
            total_nutrients['calories'] += nutrients.get('calories', 0)
            total_nutrients['protein'] += nutrients.get('protein', 0)
            total_nutrients['fat'] += nutrients.get('fat', 0)
            total_nutrients['carbs'] += nutrients.get('carbs', 0)
            total_nutrients['fiber'] += nutrients.get('fiber', 0)
            total_nutrients['sugar'] += nutrients.get('sugar', 0)
            total_nutrients['salt'] += nutrients.get('salt', 0)
        
        analysis_result = {
            'foods': foods,
            'total_nutrients': total_nutrients,
            'recommendation': get_diet_recommendation(total_nutrients)
        }
        
        return jsonify(analysis_result)
    
    return render_template('analyze.html')

def get_diet_recommendation(nutrients):
    recommendations = []
    calories = nutrients['calories']
    if calories < 500:
        recommendations.append("Nilai kalori rendah. Pertimbangkan untuk menambah asupan makanan.")
    elif calories > 2000:
        recommendations.append("Nilai kalori tinggi. Pertimbangkan untuk menyeimbangkan dengan aktivitas fisik.")
    else:
        recommendations.append("Nilai kalori dalam rentang normal.")
    
    protein = nutrients['protein']
    if protein < 50:
        recommendations.append("Konsumsi protein kurang. Pertimbangkan untuk menambah asupan protein.")
    
    fat = nutrients['fat']
    if fat > 70:
        recommendations.append("Konsumsi lemak tinggi. Pertimbangkan untuk mengurangi asupan lemak.")
    
    carbs = nutrients['carbs']
    if carbs > 300:
        recommendations.append("Konsumsi karbohidrat tinggi. Pertimbangkan untuk menyeimbangkan dengan protein dan lemak sehat.")
    
    sugar = nutrients['sugar']
    if sugar > 50:
        recommendations.append("Konsumsi gula tinggi. Pertimbangkan untuk mengurangi asupan gula.")
    
    return recommendations

if __name__ == '__main__':
    app.run(debug=True)