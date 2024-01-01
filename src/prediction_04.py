from src.utils.allutils import * 
import json
from src.preprocessing_storing_02 import *

class PredictionValidation:
       def __init__(self,schema_file):
              self.logger = App_Logger()
              self.preprocessor = StoringData()
              self.awshandler_1 = S3BucketHandler(bucket_type='loggs')
              self.awshandler_2 = S3BucketHandler(bucket_type='models')
              self.schema = schema_file




       def pred_preprocess(self,data):
                    data.drop(columns=['id'],inplace=True)
                    data.dropna(inplace=True)
                    columns = ['amount','age','duration']
                    data['amount'] = round(np.log(data['amount']),2)
                    data['age'] = round(np.log(data['age']),2)
                    data['duration'] = round(np.log(data['duration']),2)
                    data.drop(columns,axis=1,inplace=True)
                    self.logger.log('transformations for training data has been added ')
                    
                    return data 




       def load_model_from_s3(self, model_key='final_model'):
        try:
            
            model = self.awshandler_2.read_pickle_from_s3(model_key)
            return model['model']
        except Exception as e:
            self.logger.log(f"Error loading model from S3: {e}")
            


       def predict_and_merge(self, df, model_key='final_model'):
        try:
            # Load the model from S3
            model = self.load_model_from_s3(model_key)

            if model is not None:
                # Preprocess the data
                data = self.pred_preprocess(df)

                # Make predictions
                predictions = model.predict(data)

                # Create a new data frame to display predictions
                result = pd.DataFrame()
                result['ID'] = df.index
                result['predictions'] = predictions

                return result
            else:
                self.logger.log("No valid model found.")
                
        except Exception as e:
            self.logger.log(f"Error in predict_and_merge: {e}")
            


