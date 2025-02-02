import matplotlib.pyplot as plt
import networkx as nx


def plot_neural_network(input_size, hidden_sizes, output_size):
    # Create a directed graph
    G = nx.DiGraph()

    # Define layer sizes
    layer_sizes = [input_size] + hidden_sizes + [output_size]

    # Add nodes to the graph (neurons)
    node_counter = 0
    positions = {}

    for layer_idx, size in enumerate(layer_sizes):
        for i in range(size):
            node = f"l{layer_idx}_n{i}"
            G.add_node(node)
            positions[node] = (layer_idx, i)
            node_counter += 1

    # Add edges (connections between neurons)
    for layer_idx in range(len(layer_sizes) - 1):
        for i in range(layer_sizes[layer_idx]):
            for j in range(layer_sizes[layer_idx + 1]):
                G.add_edge(f"l{layer_idx}_n{i}", f"l{layer_idx + 1}_n{j}")

    # Draw the graph
    plt.figure(figsize=(10, 7))
    nx.draw(G, pos=positions, with_labels=True, node_size=500, node_color="skyblue", font_size=10, font_weight="bold",
            arrowsize=15)
    plt.title("Neural Network Architecture")
    plt.show()


# Example usage
plot_neural_network(input_size=2, hidden_sizes=[4], output_size=1)
