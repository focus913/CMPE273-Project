from uuid import uuid4

from flask import Flask, jsonify, request, render_template, flash

from blockchain import Blockchain


# Instantiate the Node
app = Flask(__name__)
app.secret_key = 'cmep273_233333'

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Baby food registration does not include rewards for mining at this stage
    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    # blockchain.new_registration(
    #     sender="0",
    #     recipient=node_identifier,
    #     amount=1,
    # )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'products': block['products'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    flash(response['message'])
    return render_template('index.html', new_block = response)

@app.route('/registrations/new', methods=['POST'])
def new_registration():
    values = {
            'product_name': request.form['name'],
            'product_type': request.form['type'],
            'product_price': request.form['price'],
            'product_details': request.form['details']
    }

    # Check that the required fields are in the POST'ed data
    required = ['product_name', 'product_type', 'product_price', 'product_details']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new registration
    index = blockchain.new_registration(
        values['product_name'], values['product_type'], values['product_price'], values['product_details'])

    response = {'message': f'Registration will be added to Block {index}'}
    return render_template('index.html', new_registered = values)


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return render_template('index.html', chain = response)


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain,
            'length': len(blockchain.chain)
        }
    flash(response['message'])
    return render_template('index.html', chain = response)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
