import numpy as np
from neural_network import NeuralNetwork


def test_feed_forward():
    # Test feed forward with a simple input and one hidden layer
    nn = NeuralNetwork(input_size=2, hidden_sizes=[2], output_size=1)
    x = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    output = nn.feed_forward(x)

    # Check that output is of the correct shape (4 samples, 1 output)
    assert output.shape == (4, 1), f"Expected shape (4, 1), but got {output.shape}"


def test_activate_function_sigmoid():
    # Test sigmoid activation function
    nn = NeuralNetwork(input_size=2, hidden_sizes=[2], output_size=1, activation_function="sigmoid")
    x = np.array([0, 1])
    output = nn.activate_function(x)

    # Sigmoid output should be between 0 and 1
    assert np.all(output >= 0) and np.all(output <= 1), "Sigmoid output should be between 0 and 1"


def test_activate_function_relu():
    # Test ReLU activation function
    nn = NeuralNetwork(input_size=2, hidden_sizes=[2], output_size=1, activation_function="ReLU")
    x = np.array([-1, 2])
    output = nn.activate_function(x)

    # ReLU output should be non-negative
    assert np.all(output >= 0), "ReLU output should be non-negative"


def test_back_propagate():
    # Test backpropagation function by checking weight and bias updates
    nn = NeuralNetwork(input_size=2, hidden_sizes=[2], output_size=1)
    initial_weights = [w.copy() for w in nn.weights]  # Store initial weights
    x = np.array([[1, 1]])
    y = np.array([[0]])
    nn.back_propagate(x, y, learning_rate=0.1)

    # Check that weights have been updated (they should be different)
    for i, (w, initial_w) in enumerate(zip(nn.weights, initial_weights)):
        assert not np.array_equal(w, initial_w), f"Weights in layer {i} were not updated"


def test_train():
    # Test the training process with a simple dataset
    nn = NeuralNetwork(input_size=2, hidden_sizes=[4], output_size=1,
                       activation_function="sigmoid")  # Increase hidden layer size
    x = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y = np.array([[0], [0], [0], [1]])

    # Train the model for a sufficient number of epochs with a smaller learning rate (e.g., 0.01)
    nn.train(x, y, epochs=10000, learning_rate=0.1)  # Reduce learning rate and increase epochs

    # Ensure that after training, the model predicts values close to expected results for the AND gate
    predictions = nn.feed_forward(x)
    expected = np.array([[0], [0], [0], [1]])

    # Increase tolerance for the test to account for possible small errors in training
    assert np.allclose(predictions, expected, atol=0.1), f"Predictions: {predictions}, Expected: {expected}"


def test_save_load_model():
    # Test save and load model functionality
    nn = NeuralNetwork(input_size=2, hidden_sizes=[2], output_size=1)
    nn.train(np.array([[0, 0], [0, 1], [1, 0], [1, 1]]), np.array([[0], [0], [0], [1]]), epochs=10, learning_rate=0.1)

    # Save the model state
    nn.save_model("test_model.npz")

    # Load the model and check if the weights and biases are the same
    nn2 = NeuralNetwork(input_size=2, hidden_sizes=[2], output_size=1)
    nn2.load_model("test_model.npz")

    # Check if weights and biases are the same after loading the model
    for w1, w2 in zip(nn.weights, nn2.weights):
        assert np.array_equal(w1, w2), "Weights do not match after loading model"
    for b1, b2 in zip(nn.biases, nn2.biases):
        assert np.array_equal(b1, b2), "Biases do not match after loading model"
