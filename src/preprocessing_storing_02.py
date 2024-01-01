#######  Get all the csv files from  artifacts->ValidatedTrainingData  and store them
### inside the database  


from src.utils.allutils import *
import os 
from sklearn.model_selection import train_test_split
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import ADASYN
from imblearn.over_sampling import SMOTE



      

class StoringData:
    def __init__(self, db_config_file='config.yaml'):
        self.logger = App_Logger()
        self.s3handler = S3BucketHandler(bucket_type='trainingdata')

    def preprocessing_and_storing(self, data):
        try:
            ####### split the data and perform preprocessing and store them in the training data bucket 
            #####  as x_train , x_test , y_train , y_test 
            #### If those files are already exists add our data to them 

            ###### Remove duplicates ############
            data= data.drop_duplicates()
            self.logger.log(f"Removed duplicates, now DataFrame has  unique rows")


       
            ## apply_transformations(self,data):
            columns = ['amount','age','duration']
            data['amount'] = round(np.log(data['amount']),2)
            data['age'] = round(np.log(data['age']),2)
            data['duration'] = round(np.log(data['duration']),2)
            data.drop(columns,axis=1,inplace=True)
            self.logger.log('transformations for training data has been added ')
              

            ## seperate_label_feature(self,data):
            # "credit_risk"
            X = data.drop('credit_risk',axis=1)
            y = data['credit_risk']
            self.logger.log('Featue column is  being seperated ')
              
            ## splitting_data:
            x_train, x_test, y_train, y_test = train_test_split(X,y,test_size=0.2)
            self.logger.log('Split the data ')
            


            #########   handling_missing_values:
            # Get numerical and categorical features
            numerical_features = x_train.select_dtypes(include=['float64', 'int64']).columns.tolist()
            categorical_features = x_train.select_dtypes(include=['object']).columns

            # Impute numerical features using KNN
            numerical_imputer = KNNImputer(n_neighbors=5)
            x_train[numerical_features] = numerical_imputer.fit_transform(x_train[numerical_features])
            x_test[numerical_features] = numerical_imputer.transform(x_test[numerical_features])

            # Check if there are any categorical features
            if len(categorical_features) >= 1:
                     # Impute categorical features using Random Forest
                     categorical_imputer = RandomForestClassifier(n_estimators=100, random_state=42)

                     # Fit the imputer on the observed categorical data
                     categorical_imputer.fit(x_train[categorical_features], y_train)

                     # Predict missing values in both training and test sets
                     x_train[categorical_features] = categorical_imputer.predict(x_train[categorical_features])
                     x_test[categorical_features] = categorical_imputer.predict(x_test[categorical_features])

            self.logger.log('Missing values handled for categorical features')
    
            


            ###  handling_class_imbalances
            ### Since this is a binary classification there are ony 2 classes in my response
            ##  feature . If the % of either class is less than 30% imma perform ADASYN
            '''
            ###########  Little intro the ADASYN (Adaptive Synthetic Sampling)

              technique used for handling imbalanced datasets in machine learning. It is specifically designed to oversample the minority class by generating synthetic examples. This helps in addressing the class imbalance problem, where one class has significantly fewer examples than the other.
            
            
              sampling_strategy='minority': This parameter determines the ratio of the number of synthetic samples to generate for the minority class compared to the majority class. In this case, it's set to 'minority', meaning ADASYN will adjust the sampling strategy based on the size of the minority class.

              random_state=42: This parameter sets the seed for the random number generator. Setting a seed ensures reproducibility; if you use the same seed, you'll get the same results when running the algorithm multiple times.

              n_neighbors=7: This parameter determines the number of nearest neighbors to consider when generating synthetic samples. ADASYN generates synthetic samples for each minority class example, and the number of neighbors influences how similar the synthetic samples are to the original examples.
            
            
            '''
            class_counts = np.bincount(y_train)
            threshold = 30  # 30%
            total_instances = len(y_train)
            for class_label, count in enumerate(class_counts):
                     class_percentage = (count / total_instances) * 100
                     if class_percentage < threshold:
                          ada = ADASYN(sampling_strategy='minority',random_state=42,n_neighbors=7)
                          x_res,y_res = ada.fit_resample(x_train,y_train)
                          

            
            

            ############# Now we have to store x_res , y_res , x_test , y_test in our training data bucket
            self.s3handler.write_csv_to_s3('x_train',x_res)
            self.s3handler.write_csv_to_s3('x_test',x_test)
            self.s3handler.write_csv_to_s3('y_train',y_res)
            self.s3handler.write_csv_to_s3('y_test',y_test)





        except Exception as e:
            self.logger.log(f"Error storing data from CSV files to database: {e}")
            raise
        finally:
            # Close the database connection
            self.db_handler.close_connection()




'''
############ 

if __name__ == "__main__":
    data_storer = StoringData()
     preprocessing_and_storing()

    config = read_yaml('config.yaml')


    csv_folder_path = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['training_validated_local_dir'])
    data_storer.preprocessing_and_storing()

'''

