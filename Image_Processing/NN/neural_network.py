"""
Script Name - neural_network.py

Purpose - A simple feedforward neural network implementation with backpropagation, activation functions, and multiple
loss functions.

Created by Michael Samelsohn, 31/01/25
"""

# Imports #
import numpy as np
from Settings.settings import log


class NeuralNetwork:
    def __init__(self, input_size, hidden_sizes, output_size, activation_function="sigmoid", loss_function="MSE"):
        log.debug("Initializing a neural network class")
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.activation_function = activation_function
        self.loss_function = loss_function

        self.activations = None

        self.layers = len(hidden_sizes) + 1  # Hidden layers + output layer.

        # Initialize weights and biases for each layer.
        self.weights = []
        self.biases = []

        log.debug("Initializing weights and biases for connections of input layer to first hidden layer")
        self.weights.append(np.random.uniform(-1, 1, (self.input_size, self.hidden_sizes[0])))
        self.biases.append(np.zeros((1, self.hidden_sizes[0])))

        log.debug("Initializing weights and biases for connections of hidden layers")
        for i in range(1, len(self.hidden_sizes)):
            self.weights.append(np.random.uniform(-1, 1, (self.hidden_sizes[i - 1], self.hidden_sizes[i])))
            self.biases.append(np.zeros((1, self.hidden_sizes[i])))

        log.debug("Initializing weights and biases for connections of last hidden layer to output layer")
        self.weights.append(np.random.uniform(-1, 1, (self.hidden_sizes[-1], self.output_size)))
        self.biases.append(np.zeros((1, self.output_size)))

        log.debug("Weights and biases initialized")

    def feed_forward(self, x):
        """
        In the feedforward method, the data flows through the network. It calculates the weighted sums for the hidden
        and output layers and applies the activation function.
        """

        self.activations = [x]  # Store input as the activation of the first layer.

        for i in range(self.layers - 1):  # Loop through all hidden layers.
            layer_input = np.dot(self.activations[i], self.weights[i]) + self.biases[i]
            activation_output = self.activate_function(layer_input)
            self.activations.append(activation_output)  # Store activation for the next layer.

        # For output layer.
        output_layer_input = np.dot(self.activations[-1], self.weights[-1]) + self.biases[-1]
        return self.activate_function(output_layer_input)

    def activate_function(self, x):
        """
        The function is used as the activation function for both the hidden layer and output layer.
        """

        match self.activation_function:
            case "sigmoid":
                """
                The Sigmoid function is one of the most basic and commonly used activation functions for neural 
                networks.
                Pros:
                1) Bounded Output - The sigmoid function outputs values between 0 and 1, which can be useful when you 
                   need to model probabilities (as in binary classification).
                2) Simple Derivative - The derivative of the sigmoid is simple, making it easier to compute gradients 
                   during back-propagation.
                Cons:
                1) Vanishing Gradient Problem - For very large or small inputs, the derivative of the sigmoid becomes 
                   extremely small. This leads to very small updates during backpropagation, slowing down learning and 
                   sometimes preventing the network from learning at all (especially for deep networks).
                2) Not Zero-Centered - The outputs of the sigmoid are always positive (between 0 and 1), which can lead 
                   to inefficient gradient updates and slower learning in deeper networks.
                """
                return 1 / (1 + np.exp(-x))
            case "ReLU":
                """
                ReLU (Rectified Linear Unit) is a non-linear activation function that outputs 0 for negative values and 
                the input itself for positive values. It’s much faster to compute than sigmoid and helps with the 
                vanishing gradient problem.
                Pros:
                1) Simple to calculate.
                2) It doesn't saturate in the positive domain, so it avoids the vanishing gradient problem.
                Cons:
                1) Can suffer from the "dying ReLU" problem, where neurons can stop learning if they fall into the 
                   negative region permanently (for example, all their outputs become zero).
                """
                return np.maximum(0, x)
            case "tanh":
                """
                The tanh function is similar to sigmoid but outputs values between -1 and 1, making it zero-centered. 
                This can speed up training compared to sigmoid in some cases.
                """
                return np.tanh(x)

    def back_propagate(self, x, y, learning_rate):
        """
        Compute the gradients of the weights and biases by using the chain rule and update them accordingly. First
        calculating the error at the output layer and propagating that error backward to the hidden layer.
        """

        # Feed-forward to get predictions.
        output = self.feed_forward(x)

        # Calculate error at the output layer.
        output_error = y - output
        output_delta = output_error * self.activation_function_derivative(output)

        # Store deltas for each layer.
        deltas = [output_delta]

        # Back-propagate through hidden layers.
        for i in range(self.layers - 2, -1, -1):
            hidden_error = deltas[-1].dot(self.weights[i + 1].T)
            hidden_delta = hidden_error * self.activation_function_derivative(self.activations[i + 1])
            deltas.append(hidden_delta)

        # Reverse the deltas (since we back-propagate from output to input).
        deltas.reverse()

        # Update weights and biases.
        for i in range(self.layers):
            self.weights[i] += self.activations[i].T.dot(deltas[i]) * learning_rate
            self.biases[i] += np.sum(deltas[i], axis=0, keepdims=True) * learning_rate

    def activation_function_derivative(self, x):
        """
        The function derivative is used during back-propagation for calculating gradients.
        """

        match self.activation_function:
            case "sigmoid":
                return x * (1 - x)
            case "ReLU":
                return np.where(x > 0, 1, 0)
            case "tanh":
                return 1 - np.square(np.tanh(x))

    def train(self, x, y, epochs, learning_rate):
        """
        Runs for a specified number of epochs, calling the back-propagation method on each epoch, and updating the
        weights and biases. Every 1000 epochs, the loss (mean squared error) is printed to show how the model is
        improving.
        """

        for epoch in range(epochs):
            self.back_propagate(x, y, learning_rate)
            if epoch % 1000 == 0:
                loss = self.calculate_loss(x=x, y=y)
                log.info(f"Epoch {epoch}, Loss: {loss}")

    def calculate_loss(self, x, y):
        """
        Calculating the loss is essential in machine learning because it serves as a measure of how well or poorly a
        model is performing on a given task. Functions of the loss calculation:
        • The loss is critical for guiding the learning process of the model.
        • It provides a quantitative measure of how well the model is performing, which can be used for optimization.
        • It helps in evaluating the model's accuracy, generalization, and helps prevent overfitting or underfitting.
        • Without calculating the loss, there would be no feedback loop for the model to adjust and improve its
          predictions.
        """

        match self.loss_function:
            case "MSE":
                """
                Name - Mean Squared Error (MSE).
                Formula: ??
                Type: Regression.
                Pros:
                • Easy to understand and compute.
                • Works well when the distribution of errors is Gaussian (i.e., normally distributed).
                • Differentiable, so it can be used in gradient-based optimization algorithms.
                Cons:
                • Sensitive to outliers, as large errors are squared, which can disproportionately affect the loss.
                • It assumes homoscedasticity (constant variance of errors), which may not be valid for all data sets.
                """
                return np.mean(np.square(y - self.feed_forward(x)))
            case "MAE":
                """
                Name - Mean Absolute Error (MAE).
                Formula: ??
                Type: Regression.
                Pros:
                • Less sensitive to outliers compared to MSE.
                • Often more interpretable, as it represents the average absolute error between the predicted and actual 
                  values.
                Cons:
                • Not differentiable at 0 (although sub-differentiable, it may cause issues with optimization).
                • Can be less sensitive to large errors in some cases, which could be problematic for certain problems.
                """
                return np.mean(np.abs(y - self.feed_forward(x)))
            case "BCE":
                """
                Name - Binary Cross-Entropy (Log Loss).
                Formula: ??
                Type: Binary classification.
                Pros:
                • Works well for binary classification problems where output is probabilistic (between 0 and 1).
                • Encourages models to output probabilities rather than just class labels.
                • Differentiable, which makes it suitable for gradient descent optimization.
                Cons:
                • Sensitive to predictions that are too far from the true class (e.g., predicting 0.01 when the true 
                  value is 1 can result in a large loss).
                • Requires the model output to be between 0 and 1, making it suitable only for probability-like outputs.
                """
                return -np.mean(y * np.log(self.feed_forward(x)) + (1 - y) * np.log(1 - self.feed_forward(x)))
            case "CCE":
                """
                Name - Categorical Cross-Entropy.
                Formula: ??
                Type: Multi-class Classification.
                Pros:
                • Ideal for multi-class classification problems.
                • Encourages the model to output probabilities for each class (via softmax activation).
                • Differentiable and supports gradient-based optimization.
                Cons:
                • Sensitive to predictions that are far from the actual class (e.g., predicting a very low probability 
                  for the correct class).
                • Assumes mutually exclusive classes, so it may not work well for problems where classes overlap.
                """
                return -np.mean(np.sum(y * np.log(self.feed_forward(x)), axis=1))
            case "Hinge":
                """
                Name - Hinge Loss.
                Formula: ??
                Type: Binary Classification (used in Support Vector Machines).
                Pros:
                • Works well with margin-based classifiers, such as Support Vector Machines (SVMs).
                • Penalizes mis-classifications with a margin, which can lead to better generalization.
                Cons:
                • Not suitable for probabilistic outputs or multi-class problems (without modifications).
                • Can lead to large errors if the margin is not well-chosen.
                """
                return np.mean(np.maximum(0, 1 - y * self.feed_forward(x)))
            case "Huber":
                """
                Name - Huber Loss.
                Formula: ??
                Type: Regression.
                Pros:
                • Combines the advantages of both MAE and MSE: it's less sensitive to outliers than MSE, but still 
                  penalizes large errors.
                • Smooth, differentiable, and works well in a variety of situations.
                Cons:
                • The hyperparameter δ needs to be chosen carefully (if too large, it behaves like MSE; if too small, 
                  like MAE).
                • May still be a bit more complex to implement compared to simple MSE or MAE.
                """
                return np.mean(np.where(np.abs(y - self.feed_forward(x)) <= 1.0,
                                        0.5 * (y - self.feed_forward(x))**2,
                                        1.0 * (np.abs(y - self.feed_forward(x)) - 0.5 * 1.0)))
                # TODO: 1.0 is the delta (default value) which should be a parameter.
            case "KLD":
                """
                Name - Kullback-Leibler Divergence (KL Divergence).
                Formula: ??
                Type: Probability Distributions (often used in Variational Inference and GANs).
                Pros:
                • Measures how one probability distribution diverges from a second, expected probability distribution.
                • Common in generative models and in cases where you want to minimize the "distance" between two 
                  distributions.
                Cons:
                • Non-symmetric, which might lead to undesired results if not handled carefully.
                • Not suitable for non-probabilistic outputs.
                """
                return np.sum(y * np.log(y / self.feed_forward(x)))
            case "CSL":
                """
                Name - Cosine Similarity Loss.
                Formula: ??
                Type: Text, Word Embeddings, or Other Applications Where Angle is Important.
                Pros:
                • Measures the angle between two vectors, useful in problems like text classification where the 
                  direction of the vector matters more than its magnitude.
                • Works well with high-dimensional data, like word embeddings.
                Cons:
                • May not be the best for problems where the exact values of predictions are important.
                • Requires normalized input vectors to work optimally.
                """
                return 1 - np.dot(y, self.feed_forward(x)) / (np.linalg.norm(y) * np.linalg.norm(self.feed_forward(x)))
            case "TL":
                """
                Name - Triplet Loss.
                Formula: ??
                Type: Metric Learning, Face Recognition, etc.
                Pros:
                • Encourages the model to learn embeddings where the anchor is closer to positive samples than to 
                  negative ones, useful in tasks like face recognition.
                • Does not require explicit class labels.
                Cons:
                • Requires careful sampling of triplets to avoid difficulties in convergence.
                • Computation can be expensive when dealing with large datasets.
                """
                return "??"  # TODO: To be implemented.
            case "CL":
                """
                Name - Contrastive Loss.
                Formula: ??
                Type: Similarity Learning.
                Pros:
                • Useful in tasks like learning similarity between data points (e.g., face verification).
                • Helps the model learn to distinguish between similar and dissimilar items.
                Cons:
                • Requires careful selection of the margin 𝑚 and often needs hard-negative mining to avoid poor 
                  convergence.
                """
                return np.mean(y * 0.5 * (self.feed_forward(x))**2 + (1 - y) * 0.5 * np.maximum(0, 1.0 - self.feed_forward(x))**2)
                # TODO: 1.0 is the margin (default value) which should be a parameter.


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
nn = NeuralNetwork(input_size=2, hidden_sizes=[4], output_size=1)
nn.train(x=x1, y=y1, epochs=10000, learning_rate=0.1)

# Test the trained network.
log.debug("Predictions after training:")
log.print_data(data=nn.feed_forward(x1).tolist(), log_level="info")
