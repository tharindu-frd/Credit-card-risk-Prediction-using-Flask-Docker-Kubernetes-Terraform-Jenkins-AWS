
from src.utils.allutils import *
from sklearn.linear_model import SGDClassifier,LogisticRegression
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier,AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_predict, cross_val_score,KFold, RepeatedStratifiedKFold
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, BaggingClassifier, AdaBoostClassifier
import botocore
from sklearn.metrics import accuracy_score


class Model_Training():
       def __init__(self):
              self.logger = App_Logger()
              self.awshandler = S3BucketHandler(bucket_type='loggs')
              self.awshandler2= S3BucketHandler(bucket_type='models')
              self.awshandler3 = S3BucketHandler(bucket_type='trainingdata')
              self.best_models = []
              self.best_params = []
              self.scoring ='accuracy'
              self.best_model = None 

       def training(self):
              
              x_train = self.awshandler3.read_csv_from_s3('x_train')
              y_train = self.awshandler3.read_csv_from_s3('y_train')
              x_test = self.awshandler3.read_csv_from_s3('x_test')
              y_test = self.awshandler3.read_csv_from_s3('y_test')


              self.models = [
              ('RF', RandomForestClassifier(), {'n_estimators': [10, 50, 100, 200]}),
              ('GB', GradientBoostingClassifier(), {'n_estimators': [50, 100, 150], 'learning_rate': [0.01, 0.1, 0.2]}),
              ('SVC', SVC(), {'C': [0.1, 1, 10], 'kernel': ['linear', 'rbf']}),
              ('SGD', SGDClassifier(), {'alpha': [0.0001, 0.001, 0.01], 'penalty': ['l1', 'l2', 'elasticnet']}),
              ('LogReg', LogisticRegression(), {'C': [0.1, 1, 10], 'penalty': ['l1', 'l2']}),
              ('AdaBoost', AdaBoostClassifier(), {'n_estimators': [50, 100, 200], 'learning_rate': [0.01, 0.1, 0.2]}),
              ('Bag', BaggingClassifier(), {'n_estimators': [10, 50, 100, 200]}),
              ('xgboost', XGBClassifier(), {'n_estimators': [50, 100, 150], 'learning_rate': [0.01, 0.1, 0.2]}),
              ('lightgbm', LGBMClassifier(), {'n_estimators': [50, 100, 150], 'learning_rate': [0.01, 0.1, 0.2]}),
              ('Dtree', DecisionTreeClassifier(), {'max_depth': [None, 10, 20, 30]})
         ]

             

              for name, model, param_grid in self.models:
                     grid_search = GridSearchCV(model, param_grid, cv=5, scoring=self.scoring)
                     grid_search.fit(x_train, y_train)

                     best_model = grid_search.best_estimator_
                     best_param = grid_search.best_params_

                     self.logger.log(f"Best parameters for {name}: {best_param}")
                     self.logger.log(f"Best {self.scoring} score for {name}: {grid_search.best_score_}")

                     self.best_models.append((name, best_model))
                     self.best_params.append((name, best_param))



              '''
               # Evaluate the best models using cross-validation
              for _, model in self.best_models:
                     cv_results = cross_val_score(model, x_train, y_train, cv=5, scoring=self.scoring)
                     avg_score = cv_results.mean()

                     self.logger.log(f"Average {self.scoring} score: {avg_score}")

                     # Check if this model has a higher score than the current best model
                     if self.best_model is None or avg_score > self.best_model[1]:
                            self.best_model = (model, avg_score)


              '''
              ####  Evaluate the model using x_test and y_test 
              for name, model in self.best_models:
                     
                     y_pred_proba = model.predict_proba(x_test)[:, 1]
                     accuracy = accuracy_score(y_test, y_pred_proba.round())

                     self.logger.log(f"Test set accuracy for {name}: {accuracy}")

                     # Check if this model has a higher accuracy than the current best model
                     if self.best_model is None or accuracy > self.best_model[1]:
                            self.best_model = (model, accuracy)



              new_model_info = {
                     'model': self.best_model[0],  # Replace 'current_model' with the actual model object
                     'accuracy': self.best_model[1],  # Replace 'current_accuracy' with the actual accuracy
                     'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              }

              self.awshandler2.write_pickle_to_s3('final_model', new_model_info)