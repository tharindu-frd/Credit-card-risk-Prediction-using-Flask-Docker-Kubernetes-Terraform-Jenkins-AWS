from wsgiref import simple_server
from flask import Flask, render_template, request, redirect, url_for
import os
from flask_cors import CORS, cross_origin
from src.utils.allutils import *
from src.training_validation_01 import *
from src.preprocessing_storing_02 import *
from src.model_training_03 import *
from src.prediction_04 import *
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
import json
from flask import jsonify
from flask import flash

ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


  
def create_app():
    app = Flask(__name__)

    def create_upload_training_directory():
        config = read_yaml('config.yaml')
        upload_directory = os.path.join(config['artifacts']['artifacts_dir'], config['artifacts']['training_uploads'])
        if not os.path.exists(upload_directory):
            os.makedirs(upload_directory)


    def create_upload_predicting_directory():
        config = read_yaml('config.yaml')
        upload_directory = os.path.join(config['artifacts']['artifacts_dir'], config['artifacts']['predicting_uploads'])
        if not os.path.exists(upload_directory):
            os.makedirs(upload_directory)

    @app.route('/train', methods=['GET', 'POST'])
    def train():
        ## create artifacts -> training_uploads
        create_upload_training_directory()
       
        if request.method == 'POST':

            files = request.files.getlist('file')

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_location = os.path.join('artifacts', 'training_uploads', filename)
                    file.save(save_location)
            
            
       
       

            ##### Now get all the csv files from artifacts->training_uploads and validate them and store them inside artifacts/training_validated_local_dir
            schema_file = 'schema_training.json'
            csv_validator = CsvValidator(schema_file)

            
            
                
            config = read_yaml('config.yaml')
            local_folder_destination = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['training_validated_local_dir'])
            local_folder_source = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['training_uploads'])

            # Validate and store the downloaded CSV files
            for csv_file in os.listdir(local_folder_source):
                        csv_path = os.path.join(local_folder_source, csv_file)
                        if csv_validator.validate_csv(csv_path):
                                csv_validator.store_valid_csv(csv_path, local_folder_destination)        




            
            # Get a list of all CSV files in the artifacts/training_validated_local_dir convert them into a single df and perform preprocessing and store them seperately as x_train,x_test,y_tain,y_test  in our trainingdata s3 bucket 
            csv_files = [file for file in os.listdir(local_folder_destination) if file.endswith('.csv')]
            merged_df = pd.DataFrame()   # Initialize an empty DataFrame to store the merged data
            for csv_file in csv_files:
                file_path = os.path.join(local_folder_destination, csv_file)
                df = pd.read_csv(file_path)
                merged_df = pd.concat([merged_df, df], ignore_index=True)
           
                                
            storing = StoringData()
            storing.preprocessing_and_storing(merged_df)  # this will store x_train , x_test , y_train , y_test  in our s3bucket 

          

                
            ##### Now perform training 
            training = Model_Training()
            training.training()


                
            ###### Delete the artifacts directory
            delete_directory('artifacts')
            return jsonify({'message': 'Successfully trained'})
        
        
        
        return render_template('upload.html')







    @app.route('/predict',methods=['GET', 'POST'])
    def predict():
        create_upload_predicting_directory()

        if request.method == 'POST':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                new_filename = 'predicting_uploads.csv'
                local_save_location = os.path.join('artifacts', 'predicting_uploads', new_filename)
                file.save(local_save_location)

                

        ########  Now lets validate the predicting data set 
        schema_file = 'schema_training.json'
        csv_validator = CsvValidator(schema_file)

        config = read_yaml('config.yaml')
        local_folder_destination = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts'][' predicting_validated_local_dir'])
        local_folder_source = os.path.join(config['artifacts']['artifacts_dir'],config['artifacts']['predicting_uploads'])

        # Validate and store the downloaded CSV files
        for csv_file in os.listdir(local_folder_source):
                        csv_path = os.path.join(local_folder_source, csv_file)
                        if csv_validator.validate_csv(csv_path):
                                csv_validator.store_valid_csv(csv_path, local_folder_destination)        


       ####  Now we have stored the data files inside artifacts/predicting_uploads
       
        project_root = os.getcwd()
        csv_path = os.path.join(project_root, 'artifacts',  local_folder_destination)
        df = pd.read_csv(csv_path)
        predicting = PredictionValidation()
        data = predicting.pred_preprocess(df)
        result = predicting.predict_and_merge(df=data)

        ###### Delete the artifacts directory
        delete_directory('artifacts')

        # return render_template('predict.html')   : If we want to display another page 
        # Render the DataFrame in the HTML template
        return render_template('df.html', df=result)

    return app





if __name__ == "__main__":
    # This block will only be executed if the script is run directly, not imported
    app = create_app()