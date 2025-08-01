import pandas as pd
from typing import Tuple, Dict, Set, List
from numpy import ndarray

from sklearn.neural_network import MLPClassifier
from numpy.typing import ArrayLike
from sklearn.metrics import classification_report, accuracy_score

from Modeling.Model import Model

class NeuralNetworkWrapper(Model):

    '''
       NeuralNetworkWrapper is a wrapper around the MLPClassifier from sklearn
       It inherits from the Model class and implements the necessary methods for training and evaluation
    '''

    model:MLPClassifier
    def __init__(self, training_set:Tuple[pd.Series] , testing_set:Tuple[pd.Series], 
                 neural_network:MLPClassifier, dev_set:Tuple[pd.Series]=None ):
        
        super().__init__(training_set, testing_set, dev_set)
        self.model = neural_network
    def train_model(self):
        '''Method that over rides the parent method for training the model'''
        self.model.fit(self.training_input, self.training_output)

    def make_predictions(self, query_vector: ArrayLike) ->ndarray:
        return self.model.predict(query_vector)



    def evaluate_model(self, query_inputs: pd.Series, actual_outputs: pd.Series) -> Dict:
        '''Evaluates the model and returns the output in a dictionary,
            The keys for the dictionary are 'accuracy', and the name of each class.
            Each class dictionary contains precision, recall, and f1-score key-value pairs.
        '''
        predictions = self.model.predict(query_inputs)
        accuracy = accuracy_score(actual_outputs, predictions)
        report = classification_report(actual_outputs, predictions, zero_division=0, output_dict=True)
        report['accuracy'] = accuracy
        return report


