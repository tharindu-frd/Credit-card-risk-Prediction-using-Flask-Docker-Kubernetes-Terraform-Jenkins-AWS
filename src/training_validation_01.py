import json
from src.utils.allutils import *
import argparse





# self.logger.log("Table 'ValidatedTraining' created successfully")
 #       except Error as e:
 #           self.logger.log(f"Error creating 'ValidatedTraining' table: {e}")


####### Loop through all the csv files stored in the training data bucket validate them and store 
## them inside a local directory called  'artifacts' -> 'Validated_Data' -> data1.csv,data2.csv,..

class CsvValidator:
    def __init__(self, schema_file):
        self.schema = self.load_schema(schema_file)
        self.logger = App_Logger()

    def load_schema(self, schema_file):
        try:
            with open(schema_file, 'r') as file:
                return json.load(file)
        except Exception as e:
            self.logger.log(f"Error loading schema from {schema_file}: {e}")
            raise

    def validate_csv(self, csv_file):
        try:
            # Load CSV file into a DataFrame
            df = pd.read_csv(csv_file)

            # Convert all column names to lowercase
            df.columns = map(str.lower, df.columns)
            
            # Check the number of columns
            if len(df.columns) != self.schema['NumberofColumns']:
                self.logger.log(f"Error: Number of columns in {csv_file} doesn't match the schema.")
                return False

            # Check column names and data types
            for col_name, col_dtype in self.schema['ColName'].items():
                if col_name not in df.columns:
                    self.logger.log(f"Error: Column '{col_name}' is missing in {csv_file}.")
                    return False

                if df[col_name].dtype.name != col_dtype:
                    self.logger.log(f"Error: Data type of column '{col_name}' in {csv_file} is incorrect.")
                    return False

            return True
        except Exception as e:
            self.logger.log(f"Error validating CSV file {csv_file}: {e}")
            return False

    def store_valid_csv(self, csv_file, output_folder):
        try:
            if self.validate_csv(csv_file):
                output_file = os.path.join(output_folder, os.path.basename(csv_file))
                os.makedirs(output_folder, exist_ok=True)
                os.rename(csv_file, output_file)
                self.logger.log(f"Valid CSV: {csv_file} stored as {output_file}")
        except Exception as e:
            self.logger.log(f"Error storing valid CSV file {csv_file}: {e}")


'''
The if __name__ == "__main__": block is a common Python idiom. It checks whether the Python script is being run as the main program (as opposed to being imported as a module into another script).

When a Python script is run, the interpreter sets a special variable called __name__ to the string "__main__" if the script is the main program being executed. If the script is being imported as a module into another script, then __name__ is set to the name of the module.

The purpose of the if __name__ == "__main__": block is to contain the code that should only run when the script is executed directly, not when it's imported as a module. This is useful for separating code that sets up the script's behavior (when executed directly) from code that might be reused in other scripts (when imported as a module).


'''





'''  We can use the following part just to check if this python files works as intended 

>>>>>>> 3d22bce9d64a38174399f6e47ae0e07fd46b7d67
if __name__ == "__main__":
    schema_file = 'schema_training.json'
    csv_validator = CsvValidator(schema_file)

   
    # Call the save_all_csv_from_s3 function and it will download all the csv files in our training
    # bucket and save them inside the artifacts->raw_training_dir
    save_all_csv_from_s3()
    
    config = read_yaml('config.yaml')
    local_folder_destination = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['training_validated_local_dir'])
    local_folder_source = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['raw_training_dir'])

    # Validate and store the downloaded CSV files
    
    for csv_file in os.listdir(local_folder_source):
              csv_path = os.path.join(local_folder_source, csv_file)
              if csv_validator.validate_csv(csv_path):
                     csv_validator.store_valid_csv(csv_path, local_folder_destination)
              else:
                      print(f"Skipping invalid CSV: {csv_file}")


    
                      

  '''  
