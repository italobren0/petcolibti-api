from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import requests

app = Flask(__name__)
CORS(app)

DATABASE = 'petcolibti.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            brand TEXT,
            image_url TEXT,
            is_local INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT,
            address TEXT NOT NULL,
            cep TEXT NOT NULL,
            items TEXT NOT NULL,
            total_price REAL NOT NULL,
            shipping_cost REAL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

def load_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if products table is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products_data = [
            ('Ração Premium para Cães Adultos', 'Ração de alta qualidade para cães adultos de todas as raças.', 85.50, 'Rações', 'Royal Canin', 'https://example.com/racao_premium.jpg', 1),
            ('Brinquedo Mordedor para Cães', 'Brinquedo resistente para cães, ajuda na limpeza dos dentes.', 25.00, 'Brinquedos', 'Kong', 'https://example.com/brinquedo_mordedor.jpg', 1),
            ('Areia Sanitária para Gatos', 'Areia super absorvente com controle de odor.', 35.90, 'Higiene', 'Pipicat', 'https://example.com/areia_sanitaria.jpg', 1),
            ('Coleira Antipulgas e Carrapatos', 'Proteção eficaz por até 8 meses.', 120.00, 'Saúde', 'Seresto', 'https://example.com/coleira_antipulgas.jpg', 1),
            ('Shampoo para Cães Filhotes', 'Fórmula suave para filhotes, sem lágrimas.', 45.00, 'Higiene', 'Pet Society', 'https://example.com/shampoo_filhotes.jpg', 1),
            ('Cama Confortável para Gatos', 'Cama macia e aconchegante para o descanso do seu gato.', 99.90, 'Acessórios', 'São Pet', 'https://example.com/cama_gatos.jpg', 1),
            ('Comedouro Elevado para Cães', 'Melhora a postura e digestão do seu pet.', 60.00, 'Acessórios', 'Chalesco', 'https://example.com/comedouro_elevado.jpg', 1),
            ('Petisco Dental para Cães', 'Ajuda a reduzir o tártaro e refrescar o hálito.', 30.00, 'Petiscos', 'Pedigree', 'https://example.com/petisco_dental.jpg', 1),
            ('Ração para Gatos Castrados', 'Alimento completo para gatos adultos castrados.', 70.00, 'Rações', 'Whiskas', 'https://example.com/racao_gatos_castrados.jpg', 1),
            ('Arranhador para Gatos', 'Essencial para afiar as unhas e se exercitar.', 110.00, 'Brinquedos', 'Flicks', 'https://example.com/arranhador_gatos.jpg', 1),
            ('Ração Afiliado A - Cães', 'Ração de marca parceira para cães.', 90.00, 'Rações', 'Afiliado PetFood', 'https://example.com/racao_afiliado_a.jpg', 0),
            ('Brinquedo Afiliado B - Gatos', 'Brinquedo divertido de parceiro para gatos.', 20.00, 'Brinquedos', 'Afiliado Play', 'https://example.com/brinquedo_afiliado_b.jpg', 0),
            ('Coleira Afiliado C - Cães', 'Coleira estilosa de parceiro para cães.', 50.00, 'Acessórios', 'Afiliado Style', 'https://example.com/coleira_afiliado_c.jpg', 0),
            ('Ração Afiliado D - Gatos', 'Ração premium de parceiro para gatos.', 75.00, 'Rações', 'Afiliado CatFood', 'https://example.com/racao_afiliado_d.jpg', 0),
            ('Cama Afiliado E - Cães', 'Cama confortável de parceiro para cães.', 105.00, 'Acessórios', 'Afiliado Comfort', 'https://example.com/cama_afiliado_e.jpg', 0)
        ]
        cursor.executemany('INSERT INTO products (name, description, price, category, brand, image_url, is_local) VALUES (?, ?, ?, ?, ?, ?, ?)', products_data)
        conn.commit()

    conn.close()

@app.route('/')
def home():
    return 'Bem-vindo à API PetColibti!'

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cep = request.args.get('cep')

    if cep and cep.startswith('1333'): # CEPs de Indaiatuba começam com 1333x
        # Prioriza produtos locais para Indaiatuba
        cursor.execute('SELECT * FROM products ORDER BY is_local DESC, name')
    else:
        # Prioriza produtos de afiliados para outras cidades ou sem CEP
        cursor.execute('SELECT * FROM products ORDER BY is_local ASC, name')

    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Produto não encontrado'}), 404

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    categories = conn.execute('SELECT DISTINCT category FROM products').fetchall()
    conn.close()
    return jsonify([c['category'] for c in categories])

@app.route('/api/brands', methods=['GET'])
def get_brands():
    conn = get_db_connection()
    brands = conn.execute('SELECT DISTINCT brand FROM products').fetchall()
    conn.close()
    return jsonify([b['brand'] for b in brands])

@app.route('/api/cep/<cep>', methods=['GET'])
def check_cep(cep):
    # Esta é uma simulação. Em um ambiente real, você usaria uma API de CEP como ViaCEP.
    # Para simplificar, vamos considerar Indaiatuba como qualquer CEP que comece com '1333'
    is_indaiatuba = cep.startswith('1333')
    return jsonify({'cep': cep, 'is_indaiatuba': is_indaiatuba})

@app.route('/api/calculate_shipping', methods=['POST'])
def calculate_shipping():
    data = request.get_json()
    target_cep = data.get('cep')
    weight = data.get('weight', 1.0) # Peso em kg, padrão 1kg
    length = data.get('length', 20) # Comprimento em cm, padrão 20cm
    height = data.get('height', 10) # Altura em cm, padrão 10cm
    width = data.get('width', 15) # Largura em cm, padrão 15cm

    if not target_cep:
        return jsonify({'error': 'CEP de destino é obrigatório'}), 400

    # Simulação de cálculo de frete
    # Em um ambiente real, você integraria com a API dos Correios (Sigep Web) ou outras transportadoras
    # Para este exemplo, vamos usar uma lógica simples baseada no CEP

    # Exemplo de CEPs para simulação:
    # Indaiatuba: 13330-000 (ou qualquer 1333x-xxx)
    # São Paulo Capital: 01000-000
    # Rio de Janeiro: 20000-000

    shipping_cost = 0.0
    delivery_time = '5-7 dias úteis'

    if target_cep.startswith('1333'): # Indaiatuba e região próxima
        shipping_cost = 15.00
        delivery_time = '1-2 dias úteis'
    elif target_cep.startswith('01') or target_cep.startswith('02'): # São Paulo Capital
        shipping_cost = 25.00
        delivery_time = '2-3 dias úteis'
    elif target_cep.startswith('2'): # Rio de Janeiro
        shipping_cost = 35.00
        delivery_time = '3-4 dias úteis'
    else:
        shipping_cost = 45.00 + (weight * 5) # Custo base + por peso para outras regiões
        delivery_time = '5-10 dias úteis'

    return jsonify({
        'cep': target_cep,
        'shipping_cost': round(shipping_cost, 2),
        'delivery_time': delivery_time,
        'carrier': 'Simulado (Correios/Transportadora)'
    })

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    customer_name = data.get('customer_name')
    customer_email = data.get('customer_email')
    customer_phone = data.get('customer_phone')
    address = data.get('address')
    cep = data.get('cep')
    items = data.get('items') # Lista de produtos no carrinho
    total_price = data.get('total_price')
    shipping_cost = data.get('shipping_cost')

    if not all([customer_name, customer_email, address, cep, items, total_price]):
        return jsonify({'error': 'Dados do pedido incompletos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO orders (customer_name, customer_email, customer_phone, address, cep, items, total_price, shipping_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_name, customer_email, customer_phone, address, cep, str(items), total_price, shipping_cost)
        )
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Pedido criado com sucesso!', 'order_id': order_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    load_sample_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
