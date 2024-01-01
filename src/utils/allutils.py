import yaml
import os 
import boto3
import pandas as pd
import pickle
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from botocore.exceptions import NoCredentialsError
import shutil
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import ADASYN
from imblearn.over_sampling import SMOTE





###############  Lets define a function to  read yaml files ########################
def read_yaml(path_to_yaml:str)-> dict:
       '''
              This function takes a string as an input and returns a dictionary

       '''
       with open(path_to_yaml) as yaml_file:
              content = yaml.safe_load(yaml_file)
       # print(content)
       return content






###########################################################################################
############################################################################################
############################################################################################
##### Lets write a function to perform  the task of downloading all the csv files from the 
#####   trainingdata-> training-data-bucket-35687 
def save_all_csv_from_s3():
    """
    Loop through all CSV files in the S3 bucket and save them locally.

    :param bucket_name: The name of the S3 bucket.
    :param local_folder: The local folder to save CSV files.
    :param aws_access_key_id: AWS access key ID.
    :param aws_secret_access_key: AWS secret access key.
    """
    try:
        config = read_yaml('config.yaml')
        local_folder = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['raw_training_dir'])
        aws_access_key_id = config['trainingdata']['aws_access_key_id']
        aws_secret_access_key = config['trainingdata']['aws_secret_access_key']
        bucket_name = config['trainingdata']['bucket_name']

        # Create an S3 client
        s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

        # List objects in the S3 bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)

        # Create the local folder if it doesn't exist
        os.makedirs(local_folder, exist_ok=True)

        # Loop through each object in the S3 bucket
        for obj in response.get('Contents', []):
            key = obj['Key']
            if key.endswith('.csv'):  # Check if the object is a CSV file
                local_filename = os.path.join(local_folder, f"{key.replace('/', '_')}")

                # Download the CSV file from S3
                download_csv_from_s3(s3_client, bucket_name, key, local_filename)

                print(f"Downloaded and saved: {key} as {local_filename}")

    except Exception as e:
        print(f"Error saving CSV files from S3: {str(e)}")
        raise



def download_csv_from_s3(s3_client, bucket_name, key, local_filename):
    """
    Download a CSV file from S3.

    :param s3_client: The S3 client.
    :param bucket_name: The name of the S3 bucket.
    :param key: The key of the object in S3.
    :param local_filename: The local filename to save the CSV file.
    """
    try:
        response = s3_client.download_file(bucket_name, key, local_filename)
    except NoCredentialsError as e:
        print(f"Error downloading CSV file from S3: {str(e)}")
        raise

'''
##### Example usage:
       save_all_csv_from_s3(
              bucket_name='your_bucket_name',
              local_folder='your_local_folder',
              aws_access_key_id='your_aws_access_key_id',
              aws_secret_access_key='your_aws_secret_access_key'
)


'''





########## Lets define a function to remove all the files inside a directory ########
def remove_all_files_in_directory(directory):
    try:
        # Get the list of files in the directory
        files = os.listdir(directory)

        # Iterate through the files and remove each one
        for file_name in files:
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"File '{file_name}' successfully removed.")

        print(f"All files in directory '{directory}' successfully removed.")
    except Exception as e:
        print(f"Error removing files from directory '{directory}': {str(e)}")
        raise




#### Lets define a function to delete a directory 
def delete_directory(directory):
    try:
        # Check if the directory exists
        if os.path.exists(directory):
            # Remove the directory and its contents
            shutil.rmtree(directory)
            print(f"Directory '{directory}' successfully deleted.")
        else:
            print(f"Directory '{directory}' does not exist.")

    except Exception as e:
        print(f"Error deleting directory '{directory}': {str(e)}")
        raise














##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
#######################  Lets create a class to work with a s3 bucket   ##########################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
class S3BucketHandler:
       def __init__(self,bucket_type,config_file='config.yaml'):
              '''
                     I have stored all the credentials related to s3 bucket in a seperate file called
                     config.yaml . In this file earlier I have created a function called 'read_yaml' 
                     which takes the path of the yaml file as an argument and returns the content of the yaml file as a dictionary. 


                     bucket_type: Inside my config.yaml I have stored the data in the following manner.
                                   trainingdata:
                                          bucket_name: training-data-bucket-35687
                                          destination: 
                                          aws_access_key_id: 
                                          aws_secret_access_key: 

                                   loggs:
                                          bucket_name: loggs35687
                                          destination: 
                                          aws_access_key_id: 
                                          aws_secret_access_key: 

                     So inorder to get the credentials of a specific bucket , first I need to know the 
                     type (trainingdata,loggs) . That's why I'm using an attribute called 'bucket_config' 

              '''
              config = read_yaml(config_file)
              self.bucket_config = config[bucket_type]
              self.bucket_name = self.bucket_config['bucket_name']
              self.destination_url = self.bucket_config['destination']
              self.aws_access_key_id = self.bucket_config['aws_access_key_id']
              self.aws_secret_access_key = self.bucket_config['aws_secret_access_key']
              self.s3_client = boto3.client(
                     's3',
                     aws_access_key_id= self.aws_access_key_id,
                     aws_secret_access_key = self.aws_secret_access_key


              )





       def write_csv_to_s3(self,file_name,data_frame):
                try:
                    existing_csv = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
                    existing_data = pd.read_csv(existing_csv['Body'])
            
                    # Merge the existing data with the new data
                    merged_data = pd.concat([existing_data, data_frame], ignore_index=True)

                    # Convert the merged data to CSV format
                    merged_csv = merged_data.to_csv(index=False).encode()

                    # Upload the merged data back to the S3 bucket
                    response = self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=file_name,
                        Body=merged_csv
                    )

                   
                    return response

                except self.s3_client.exceptions.NoSuchKey:
                    # The file doesn't exist, upload the new data directly
                    csv_file = data_frame.to_csv(index=False).encode()

                    try:
                            response = self.s3_client.put_object(
                            Bucket=self.bucket_name,
                            Key=file_name,
                            Body=csv_file
                            )
                            return response

                    except Exception as e:
                        print(f"Error uploading CSV to S3 bucket: {str(e)}")
                        raise

                except Exception as e:
                    print(f"Error checking CSV existence in S3 bucket: {str(e)}")
                    raise



       

       def read_csv_from_s3(self,file_name):
              '''
                     objective : Read a csv file from a s3 bucket and return it as a pandas data frame
              
              '''

              try:
                     response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
                     data_frame = pd.read_csv(response['Body'])
                     print(f"CSV file '{file_name}' successfully read from S3 bucket '{self.bucket_name}'.")
                     return data_frame
              
              except Exception as e:
                     print(f"Error reading CSV from S3 bucket: {str(e)}")
                     raise




       def delete_from_s3(self,file_name):
              '''
                     objective : Delete a file from a s3 bucket 
              '''
              try:
                     response = self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=file_name
            )
                     print(f"File '{file_name}' successfully deleted from S3 bucket '{self.bucket_name}'.")
                     return response
              except Exception as e:
                      print(f"Error deleting file from S3 bucket: {str(e)}")
                      raise



       def write_pickle_to_s3(self, file_name, data):
              '''
                     objective: save data in a s3 bucket in  pickle format. We use this to store our best model inside a s3 bucket . 
              
              '''
              pickle_buffer = pickle.dumps(data)
              try:
                     response = self.s3_client.put_object(
                            Bucket=self.bucket_name,
                            Key=file_name,
                            Body=pickle_buffer
             )
                     print(f"Pickle file '{file_name}' successfully written to S3 bucket '{self.bucket_name}'.")
                     return response
              
              except Exception as e:
                     print(f"Error writing Pickle to S3 bucket: {str(e)}")
                     raise
        





       
       # def read_pickle_from_s3(self, file_name):
              


       def read_pickle_from_s3(self, file_name):
              '''
                     objective : To read a pickle file from a s3 bucket . Whenever user hits the training endpoint we trian a new model and compare it with the previos best model that we stored in a pickle file and update it if the new model works well  . To make that comparison we need a function to  read the data from a pickle file 
              '''

              try:
                     response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
                     pickle_data = pickle.loads(response['Body'].read())
                     print(f"Pickle file '{file_name}' successfully read from S3 bucket '{self.bucket_name}'.")
                     return pickle_data
              except Exception as e:
                     print(f"Error reading Pickle from S3 bucket: {str(e)}")
                     raise


       

       def read_txt_from_s3(self, file_name):
        """
        Read text content from a file in an S3 bucket.

        :param file_name: The name of the file to be read from the S3 bucket.
        :return: The text content of the file.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
            text_content = response['Body'].read().decode()
            return text_content

        except NoCredentialsError as e:
            print(f"Error reading text file from S3 bucket: {str(e)}")
            raise




       def write_txt_to_s3(self, file_name, text_content):
        """
        Write text content to a file in an S3 bucket.

        :param file_name: The name of the file to be created in the S3 bucket.
        :param text_content: The text content to be written to the file.
        """
        txt_buffer = text_content.encode()

        try:
            # Check if the file already exists in the S3 bucket
            existing_keys = [obj['Key'] for obj in self.s3_client.list_objects_v2(Bucket=self.bucket_name).get('Contents', [])]

            if file_name in existing_keys:
                # File already exists, append the text content
                existing_content = self.read_txt_from_s3(file_name)
                text_content = existing_content + text_content

            else:
                # File doesn't exist, create it
                response = self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_name,
                    Body=txt_buffer
                )

            # Write or overwrite the file in the S3 bucket
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=txt_buffer
            )

            print(f"Text content successfully written to S3 bucket '{self.bucket_name}/{file_name}'.")
            return response

        except NoCredentialsError as e:
            print(f"Error writing text file to S3 bucket: {str(e)}")
            raise



       def write_txt_to_s3(self, file_name, text_content):
              """
                     Write text content to a file in an S3 bucket.

                     :param file_name: The name of the file to be created in the S3 bucket.
                     :param text_content: The text content to be written to the file.
              """
              txt_buffer = text_content.encode()
              try:
                     response = self.s3_client.put_object(
                            Bucket=self.bucket_name,
                            Key=file_name,
                            Body=txt_buffer
            )
                     print(f"Text file '{file_name}' successfully written to S3 bucket '{self.bucket_name}'.")
                     return response
              except NoCredentialsError as e:
                     print(f"Error writing text file to S3 bucket: {str(e)}")
                     raise










##################################################################################################
##################################################################################################
#################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
############################ Lets create a class to work with  Loggers   #########################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################


class App_Logger:
       def __init__(self, bucket_type='loggs'):
              # Initialize an S3BucketHandler with the specified bucket type
               self.s3_handler = S3BucketHandler(bucket_type=bucket_type)

       def log(self, log_message, file_name='TrainingLogs.txt'):
              """
                     Log messages to S3 bucket using S3BucketHandler.

                            :param log_message: The log message to be written.
                            :param file_name: The name of the file in the S3 bucket (default is "TrainingLogs.txt").
              """
              self.now = datetime.now()
              self.date = self.now.date()
              self.current_time = self.now.strftime("%H:%M:%S")

               # Log messages to S3 bucket using S3BucketHandler
              log_content = f"{str(self.date)}/{str(self.current_time)}\t\t{log_message}\n"
              self.s3_handler.write_txt_to_s3(file_name, log_content)
              print(f"Log message: {log_message}")





'''
########## How to use that logger class 

        # Create an instance of App_Logger with a custom file name
              logger = App_Logger()

        # Use the log method to log messages to the 'loggs' S3 bucket with a custom file name
              logger.log("This is a log message.", file_name="CustomLogFile.txt")

#### All the loggs related to training must be saved inside : Trainingloggs.txt
#### All the loggs related to predicting must be saved inside  : Predictionloggs.txt
'''







################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
############################ Lets create a class to work  with databases #######################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################

'''
All the validated and preprocessed training  data gonna be stored in the table called : ValidatedTraining

All the validated and preprocessed prediction  data gonna be stored in the table called : ValidatedPredicting


'''

class DatabaseHandler:
       def __init__(self, config_file='config.yaml'):
              config = read_yaml(config_file)
              self.db_config = config['database']

              self.host = 'myproject.c3om4gaouryi.ap-south-1.rds.amazonaws.com'

              self.host = 'localhost'

              self.username = self.db_config['username']
              self.password = self.db_config['password']
              self.database = self.db_config['dbname']
              self.logger = App_Logger()
              self.connection = None  # Initialize connection
              self.cursor = None  # Initialize cursor




       def connect(self):
              try:
                      self.connection = mysql.connector.connect(
                     host=self.host,
                     user=self.username,
                     password=self.password,
                     database=self.database
                     )
                      if self.connection.is_connected():
                             self.logger.log(f"Connected to MySQL database '{self.database}'")
                             print('connection established')
                             self.cursor = self.connection.cursor()
              except Error as e:
                      self.logger.log(f"Error connecting to MySQL database: {e}")
                      
                      raise
              return self.connection

   



       def close_connection(self):
              if self.connection.is_connected():
                     self.connection.close()
                     self.logger.log("Connection to MySQL database closed")



       def create_validated_training_table(self):
        """
                     Create a table named 'ValidatedTraining' with 22 columns using the provided column names and data types.
        """
        try:
            cursor = self.connection.cursor()
            
            # Sample column names and data types (replace with your actual dictionary)
            column_data_types = {
                'Id':  'INTEGER', # 'VARCHAR(255)',
                'status': 'INT',
                 'duration'
                 'credit_history' : 'INTEGER',
                 'purpose' : 'INTEGER',
                 'amount' : 'INTEGER',
                 'savings' : 'INTEGER',
                 'employment_duration' : 'INTEGER',
                 'installment_rate' : 'INTEGER',
                 'personal_status_sex' : 'INTEGER',
                 'other_debtors' : 'INTEGER',
                 'present_residence' : 'INTEGER',
                 'property' : 'INTEGER',
                ' age' : 'INTEGER',
                 'other_installment_plans' : 'INTEGER',
                 'housing' : 'INTEGER',
                 'number_credits' : 'INTEGER',
                 'job ': 'INTEGER',
                 'people_liable':  'INTEGER',
                 'telephone' : 'INTEGER',
                 'foreign_worker': 'INTEGER',
                 'credit_risk' : 'INTEGER'
               
            }


    
            columns = ', '.join([f'{name} {data_type}' for name, data_type in column_data_types.items()])
            create_table_query = f"CREATE TABLE ValidatedTraining ({columns})"
            
            cursor.execute(create_table_query)
            self.connection.commit()
            
            self.logger.log("Table 'ValidatedTraining' created successfully")
        except Error as e:
            self.logger.log(f"Error creating 'ValidatedTraining' table: {e}")
            raise
        finally:
            cursor.close()





      

       def create_validated_predicting_table(self):
        """
                     Create a table named 'ValidatedTraining' with 22 columns using the provided column names and data types.
        """
        try:
            cursor = self.connection.cursor()
            
           
            column_data_types = {
                'Id':  'INTEGER', 
                'status': 'INT',
                 'duration'
                 'credit_history' : 'INTEGER',
                 'purpose' : 'INTEGER',
                 'amount' : 'INTEGER',
                 'savings' : 'INTEGER',
                 'employment_duration' : 'INTEGER',
                 'installment_rate' : 'INTEGER',
                 'personal_status_sex' : 'INTEGER',
                 'other_debtors' : 'INTEGER',
                 'present_residence' : 'INTEGER',
                 'property' : 'INTEGER',
                ' age' : 'INTEGER',
                 'other_installment_plans' : 'INTEGER',
                 'housing' : 'INTEGER',
                 'number_credits' : 'INTEGER',
                 'job ': 'INTEGER',
                 'people_liable':  'INTEGER',
                 'telephone' : 'INTEGER',
                 'foreign_worker': 'INTEGER',
                 
               
            }


    
            columns = ', '.join([f'{name} {data_type}' for name, data_type in column_data_types.items()])
            create_table_query = f"CREATE TABLE ValidatedPredicting ({columns})"
            
            cursor.execute(create_table_query)
            self.connection.commit()
            
            self.logger.log("Table 'ValidatedPredicting' created successfully")
        except Error as e:
            self.logger.log(f"Error creating 'ValidatedPredicting' table: {e}")
            raise
        finally:
            cursor.close()





       def append_rows_to_validated_training(self, data):
        """
        Append rows to the 'ValidatedTraining' table using the provided data.
        """
        try:
            cursor = self.connection.cursor()
            
            # Sample data (replace with your actual data)
            # data = [(value1, value2, ...), (value1, value2, ...), ...]
            
            insert_query = "INSERT INTO ValidatedTraining VALUES (" + ', '.join(['%s'] * len(data[0])) + ")"
            
            cursor.executemany(insert_query, data)
            self.connection.commit()
            
            self.logger.log(f"{len(data)} rows appended to 'ValidatedTraining' table")
        except Error as e:
            self.logger.log(f"Error appending rows to 'ValidatedTraining' table: {e}")
            raise
        finally:
            cursor.close()




 

       def append_rows_to_validated_predicting(self, data):
        """
        Append rows to the 'ValidatedTraining' table using the provided data.
        """
        try:
            cursor = self.connection.cursor()
            
            # Sample data (replace with your actual data)
            # data = [(value1, value2, ...), (value1, value2, ...), ...]
            
            insert_query = "INSERT INTO ValidatedPredicting VALUES (" + ', '.join(['%s'] * len(data[0])) + ")"
            
            cursor.executemany(insert_query, data)
            self.connection.commit()
            
            self.logger.log(f"{len(data)} rows appended to 'ValidatedPredicting' table")
        except Error as e:
            self.logger.log(f"Error appending rows to 'ValidatedPredicting' table: {e}")
            raise
        finally:
            cursor.close()












       def append_rows_from_csv_folder_to_validated_training(self, folder_path):
        """
        Append rows from all CSV files in a folder to the 'ValidatedTraining' table.
        """
        try:
            # Iterate through all files in the folder
            for file_name in os.listdir(folder_path):
                if file_name.endswith(".csv"):
                    file_path = os.path.join(folder_path, file_name)

                    # Read data from CSV file using pandas
                    df = pd.read_csv(file_path)

                    # Convert DataFrame to a list of tuples (each tuple represents a row)
                    data = [tuple(row) for row in df.itertuples(index=False, name=None)]

                    # Call the existing append_rows_to_validated_training method
                    self.append_rows_to_validated_training(data)

            self.logger.log(f"All rows from CSV files in folder '{folder_path}' appended to 'ValidatedTraining' table")
        except Exception as e:
            self.logger.log(f"Error appending rows from CSV files to 'ValidatedTraining' table: {e}")
            raise
        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()







       def remove_all_rows_from_validated_training(self):
        """
          Remove all rows from the 'ValidatedTraining' table.
       """
        try:
            cursor = self.connection.cursor()
            
            delete_query = "DELETE FROM ValidatedTraining"
            
            cursor.execute(delete_query)
            self.connection.commit()
            
            self.logger.log("All rows removed from 'ValidatedTraining' table")
        except Error as e:
            self.logger.log(f"Error removing rows from 'ValidatedTraining' table: {e}")
            raise
        finally:
            cursor.close()




       def fetch_all_rows_as_dataframe(self):
        """
        Fetch all rows from the 'ValidatedTraining' table and convert them into a Pandas DataFrame.
        """
        try:
            cursor = self.connection.cursor()

            # Query to select all rows from the table
            select_query = "SELECT * FROM ValidatedTraining"

            # Execute the query
            cursor.execute(select_query)

            # Fetch all rows
            rows = cursor.fetchall()

            # Get column names from the description
            column_names = [desc[0] for desc in cursor.description]

            # Convert rows to a list of dictionaries
            rows_dict_list = [dict(zip(column_names, row)) for row in rows]

            # Convert the list of dictionaries to a Pandas DataFrame
            df = pd.DataFrame(rows_dict_list)

            self.logger.log(f"Fetched {len(df)} rows from 'ValidatedTraining' table")

            return df

        except Error as e:
            self.logger.log(f"Error fetching rows from 'ValidatedTraining' table: {e}")
            raise









       def append_rows_from_csv_folder_to_validated_predicting(self, folder_path):
        """
       Append rows from all CSV files in a folder to the 'ValidatedTraining' table.
       """
        try:
            # Iterate through all files in the folder
            for file_name in os.listdir(folder_path):
                if file_name.endswith(".csv"):
                    file_path = os.path.join(folder_path, file_name)

                    # Read data from CSV file using pandas
                    df = pd.read_csv(file_path)

                    # Convert DataFrame to a list of tuples (each tuple represents a row)
                    data = [tuple(row) for row in df.itertuples(index=False, name=None)]

                    # Call the existing append_rows_to_validated_training method
                    self.append_rows_to_validated_predicting(data)

            self.logger.log(f"All rows from CSV files in folder '{folder_path}' appended to 'ValidatedPredicting' table")
        except Exception as e:
            self.logger.log(f"Error appending rows from CSV files to 'ValidatedPredicting' table: {e}")
            raise
        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()









       def remove_all_rows_from_validated_predicting(self):
        """
        Remove all rows from the 'ValidatedPredicting' table.
        """
        try:
            cursor = self.connection.cursor()
            
            delete_query = "DELETE FROM ValidatedPredicting"
            
            cursor.execute(delete_query)
            self.connection.commit()
            
            self.logger.log("All rows removed from 'ValidatedPredicting' table")
        except Error as e:
            self.logger.log(f"Error removing rows from 'ValidatedPredicting' table: {e}")
            raise

        finally:
            cursor.close()

















      
       




  











       
