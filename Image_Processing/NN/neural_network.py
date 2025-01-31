"""
Script Name - neural_network.py

Purpose - ??

Created by Michael Samelsohn, 31/01/25
"""

# Imports #
import numpy as np
from Settings.settings import log


# Define the neural network class
class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        log.debug("Initializing a neural network class")
        self.hidden_layer_input = None
        self.hidden_layer_output = None
        self.output_layer_input = None

        log.debug("Initialize weights randomly with mean 0")
        self.weights_input_hidden = np.random.uniform(-1, 1, (input_size, hidden_size))
        self.weights_hidden_output = np.random.uniform(-1, 1, (hidden_size, output_size))

        log.debug("Initialize biases")
        self.bias_hidden = np.zeros((1, hidden_size))
        self.bias_output = np.zeros((1, output_size))

    def feed_forward(self, x):
        """
        In the feedforward method, the data flows through the network. It calculates the weighted sums for the hidden
        and output layers and applies the activation function.
        """

        # Calculate activations for hidden layer.
        self.hidden_layer_input = np.dot(x, self.weights_input_hidden) + self.bias_hidden
        self.hidden_layer_output = self.activation_function(self.hidden_layer_input)

        # Calculate activations for output layer.
        self.output_layer_input = np.dot(self.hidden_layer_output, self.weights_hidden_output) + self.bias_output
        return self.activation_function(self.output_layer_input)

    def back_propagate(self, x, y, learning_rate):
        """
        Compute the gradients of the weights and biases by using the chain rule and update them accordingly. First
        calculating the error at the output layer and propagating that error backward to the hidden layer.
        """

        # Feed-forward to get predictions.
        output = self.feed_forward(x)

        # Calculate error.
        output_error = y - output
        output_delta = output_error * self.activation_function_derivative(output)

        # Calculate hidden layer error.
        hidden_error = output_delta.dot(self.weights_hidden_output.T)
        hidden_delta = hidden_error * self.activation_function_derivative(self.hidden_layer_output)

        # Update weights and biases.
        self.weights_hidden_output += self.hidden_layer_output.T.dot(output_delta) * learning_rate
        self.weights_input_hidden += x.T.dot(hidden_delta) * learning_rate
        self.bias_output += np.sum(output_delta, axis=0, keepdims=True) * learning_rate
        self.bias_hidden += np.sum(hidden_delta, axis=0, keepdims=True) * learning_rate

    def train(self, x, y, epochs, learning_rate):
        """
        Runs for a specified number of epochs, calling the back-propagation method on each epoch, and updating the
        weights and biases. Every 1000 epochs, the loss (mean squared error) is printed to show how the model is
        improving.
        """

        for epoch in range(epochs):
            self.back_propagate(x, y, learning_rate)
            if epoch % 1000 == 0:
                loss = np.mean(np.square(y - self.feed_forward(x)))  # Mean squared error loss
                log.info(f"Epoch {epoch}, Loss: {loss}")

    @staticmethod
    def activation_function(x, function="sigmoid"):
        """
        The function is used as the activation function for both the hidden layer and output layer.
        """

        match function:
            case "sigmoid":
                """
                The Sigmoid function is one of the most basic and commonly used activation functions for neural networks.
                Pros:
                1) Bounded Output - The sigmoid function outputs values between 0 and 1, which can be useful when you need 
                   to model probabilities (as in binary classification).
                2) Simple Derivative - The derivative of the sigmoid is simple, making it easier to compute gradients during 
                   back-propagation.
                Cons:
                1) Vanishing Gradient Problem - For very large or small inputs, the derivative of the sigmoid becomes 
                   extremely small. This leads to very small updates during backpropagation, slowing down learning and 
                   sometimes preventing the network from learning at all (especially for deep networks).
                2) Not Zero-Centered - The outputs of the sigmoid are always positive (between 0 and 1), which can lead to 
                   inefficient gradient updates and slower learning in deeper networks.
                """
                return 1 / (1 + np.exp(-x))
            case "ReLU":
                """
                ReLU (Rectified Linear Unit) is a non-linear activation function that outputs 0 for negative values and the 
                input itself for positive values. It’s much faster to compute than sigmoid and helps with the vanishing 
                gradient problem.
                Pros:
                1) Simple to calculate.
                2) It doesn't saturate in the positive domain, so it avoids the vanishing gradient problem.
                Cons:
                1) Can suffer from the "dying ReLU" problem, where neurons can stop learning if they fall into the negative 
                   region permanently (for example, all their outputs become zero).
                """
                return np.maximum(0, x)
            case "tanh":
                """
                The tanh function is similar to sigmoid but outputs values between -1 and 1, making it zero-centered. This 
                can speed up training compared to sigmoid in some cases.
                """
                return np.tanh(x)

    @staticmethod
    def activation_function_derivative(x, function="sigmoid"):
        """The function derivative is used during back-propagation for calculating gradients."""

        match function:
            case "sigmoid":
                return x * (1 - x)
            case "ReLU":
                return np.where(x > 0, 1, 0)
            case "tanh":
                return 1 - np.square(np.tanh(x))


# Example: AND problem (input, output)
x1 = np.array([[0, 0],
               [0, 1],
               [1, 0],
               [1, 1]])

y1 = np.array([[0],
               [0],
               [0],
               [1]])

# Create and train the neural network.
nn = NeuralNetwork(input_size=2, hidden_size=4, output_size=1)
nn.train(x=x1, y=y1, epochs=10000, learning_rate=0.1)

# Test the trained network.
log.debug("Predictions after training:")
log.print_data(data=nn.feed_forward(x1).tolist(), log_level="info")
