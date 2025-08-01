import pandas as pd
import json # Import the json library
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from typing import Tuple
from collections.abc import Iterable

class Model:
    '''
    Base class for a machine learning model, handles things like evaluation and training the model
    The class expects you to already have a train/test split prior to creation
    The dev set is optional, however if you do not provide a dev set then you obviously
    cannot evaluate against it.
    
    '''
    training_input: pd.Series
    training_output: pd.Series
    
    testing_input: pd.Series
    testing_output: pd.Series

    dev_input: pd.Series
    dev_output: pd.Series


    def __init__(self, training_set:Tuple[pd.Series], testing_set:Tuple[pd.Series], dev_set:Tuple[pd.Series]=None):
        '''training_set, testing_set, dev_set are all tuples where the first element is the input series
            The second element is the output series
        '''
        self.training_input, self.training_output = training_set
        self.testing_input, self.testing_output = testing_set
        if dev_set is not None and isinstance(dev_set, Iterable) and len(dev_set) == 2:
            self.dev_input, self.dev_output = dev_set
                

    def training_evaluation(self):
        self.evaluate_model(self.training_input, self.training_output)
        pass

    def test_set_evaluation(self):
        self.evaluate_model(self.testing_input, self.testing_output)

    def validation_set_evaluation(self):
        if not all( len(dev) > 0 and type(dev) is pd.Series for dev in  [self.dev_input, self.dev_output]):#self.self.dev_input, self.dev_output == None:
            raise IOError("You do not have a dev set specified for your model")
        self.evaluate_model(self.dev_input, self.dev_output)


    def train_model(self):
        '''Interface method a la Java, that trains the specific model meant to be 
        overridden'''
        pass    
    


    def evaluate_model(self, input_data:pd.Series, predictions:pd.Series):
        '''Interface method a la Java, meant to be overridden'''
        pass

    