## Deployment

First create main.tf , provider.tf and install.sh . After that goto aws->IAM -> create user  
 auername: clouduser
attach policies directly
permissions: AdministratorAccess

Now go inside that uer -> security credentials -> create access key -> CLI -> Description_tag_value:clouduser -> Create access key -> Copy the access key and secret key and also download that csv file

Now right click on Jenkins-SonarQube-VM folder and open it in integrated terminal

```bash
aws configure   #It will ask credentials
terraform init
terraform plan
terraform apply -auto-approve

```

Now in AWS EC2 , we can see our instance . Open it up and copy the public IP . Now open mobaxterm-> SSH -> give that IP as the host ip , username:ubuntu , use private key : browse and upload the key file that we have downloaded and hit ok .

Now goto the browser and paste the public ip of our ec2 instance:8080 . It will give a path copy and goto mobaxterm

```bash
sudo cat <path>

```

# Configure SonarQUbe and integrate SonarQube with jenkins

It will give a password copy that and paste that insied the box in the browser . Click on install suggested plugins . Now give the user name , passwords ... . After that goto Mange jenkins -> plugins->Available plugins -> select : Eclipse Temurin installer/SonarQube Scanner/Sonar Quality Gates/Quality Gates/ Flask / Docker/Docker common / Docker pipelines /Docker API / docker build step/ nodejs : install all of them -> No click on ' go back to home page'

Now again goto Manage Jenkins -> Tools -> click on flask and give version / click on JDK , Name:jdk17 and click on Add installer (still in jdk) select 'install from adoptium.net' and select jdk-17.0.8.1+1 , Now click on apply - > Save

Now again goto Manage Jenkins -> Tools -> Docker installation : name docker , click on Add installer and select 'Download from docker.com' / SonarQUbe Scanner installation : Name=sonarqube-scanner : install automatically : install from Maven Central -> apply and save

Now goto aws ec2 instance and copy the public IP , goto browser paste that:9000 and give admin as both user name as password . After that configure a new password (old password:admin) . Go to Administration
Security -> users -> tokens : generate t token and copy that , Now go to jenkins -> Manage jenkins -> credentials -> global -> add credentials : kind = secret text , id : token name that we gave , secret:paste that token and -> create

Now go to jenkins -> Manage jenkins -> system -> SonarQube servers : Add SonarQube server : name=SonarQube-Server : URL = http://<private ip of our ec2>:9000 : In the drop down select the token -> apply and save .

Now go back to sonar cube dashboard -> Quality gate -> create : Name = SonarQube-Quality-Gate -> Administration - > Configuration -> Webhooks -> create : Name = jenkins : uRL = <private ip of our ec2>:8080/sonarqube-webhook/ -> create

# Jenkins setup

Now goto jenkins -> New Item -> Name : Flask-CI/CD and hit ok -> select 'Discard old builds ' : Max = 2 -> pipeline script :

```bash
pipeline{
     pipeline{
     agent any

     tools{
         jdk 'jdk17'
         flask 'flask'
     }
     environment {
         SCANNER_HOME=tool 'sonarqube-scanner'
     }

     stages {
         stage('Clean Workspace'){
             steps{
                 cleanWs()
             }
         }
         stage('Checkout from Git'){
             steps{
                 git branch: 'main', url: 'https://github.com/tharindu-frd/ML-FLOW-integration-with-AWS-SAGEMAKER.git'
             }
         }
         stage("Sonarqube Analysis "){
             steps{
                 withSonarQubeEnv('SonarQube-Server') {
                     sh ''' $SCANNER_HOME/bin/sonar-scanner -Dsonar.projectName=flask-CI \
                     -Dsonar.projectKey=flask-CI '''
                 }
             }
         }
         stage("Quality Gate"){
            steps {
                 script {
                     waitForQualityGate abortPipeline: false, credentialsId: 'SonarQube-Token'
                 }
             }
         }
         stage('Install Dependencies') {
             steps {
                 sh "npm install"
             }
         }
         stage('TRIVY FS SCAN') {
             steps {
                 sh "trivy fs . > trivyfs.txt"
             }
         }


     }
 }
```

Click on apply and save

Now click Build Now

We can see that inside SonarQUbe dashboard -> projects

## Integrate docker hub with jenkins

goto docker dektop -> account settings -> security -> new access token and copy the token
Now goto jenkins -> Manage jenkins -> credentials -> add credentials: global and add credentials
give the username as docker hub user name and give that access token as the password , ID:dockerhub and click on create .

Now goto jenkins -> click the pipeline -> Configure -> add the rest to the script

```bash
pipeline{
     agent any

     tools{
         jdk 'jdk17'
         nodejs 'node16'
     }
     environment {
         SCANNER_HOME=tool 'sonarqube-scanner'
     }

     stages {
         stage('Clean Workspace'){
             steps{
                 cleanWs()
             }
         }
         stage('Checkout from Git'){
             steps{
                 git branch: 'main', url: 'https://github.com/tharindu-frd/ML-FLOW-integration-with-AWS-SAGEMAKER.git'
             }
         }
         stage("Sonarqube Analysis "){
             steps{
                 withSonarQubeEnv('SonarQube-Server') {
                     sh ''' $SCANNER_HOME/bin/sonar-scanner -Dsonar.projectName=flask-CI \
                     -Dsonar.projectKey=flask-CI '''
                 }
             }
         }
         stage("Quality Gate"){
            steps {
                 script {
                     waitForQualityGate abortPipeline: false, credentialsId: 'SonarQube-Token'
                 }
             }
         }
         stage('Install Dependencies') {
             steps {
                 sh "npm install"
             }
         }
         stage('TRIVY FS SCAN') {
             steps {
                 sh "trivy fs . > trivyfs.txt"
             }
         }
          stage("Docker Build & Push"){
             steps{
                 script{
                    withDockerRegistry(credentialsId: 'dockerhub', toolName: 'docker'){
                        sh "docker build -t swiggy-clone ."
                        sh "docker tag swiggy-clone chandima35687729/flask-app:latest "
                        sh "docker push chandima35687729/flask-app:latest "
                     }
                 }
             }
         }
         stage("TRIVY"){
             steps{
                 sh "trivy image chandima35687729/flask-app:latest > trivyimage.txt"
             }
         }




     }
 }

```

# Create AWS EKS cluster

Now goto mobaxterm ->

```bash
sudo apt update
sudo apt install curl
curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl


curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt install unzip
unzip awscliv2.zip
sudo ./aws/install
aws --version

curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
cd /tmp
sudo mv /tmp/eksctl /bin
eksctl version



```

Now goto aws -> IAM -> roles -> create role : aws service : usecase=ec2 -> next -> Admin access -> next->rolename:ekctlrole -> create role
Now go to ec2 instance and select the instance -> actions-> security -> modify IAM role -> select the role -> update

Now goback to mobaxterm

```bash

eksctl create cluster --name virtualtechbox-cluster \   # hit an enter
--region ap-south-1 \
--node-type t2.small \
--nodes 3 \


$ kubectl get nodes
$ kubectl get svc

```

Now in the mobaxterm in the right side panel refresh it couple of times then .kube file will appear . Go inside that -> right click on config and download it to our local project folder. Now go to that folder select the file open it and inside that notepad file goto file , save a copy as -> save in the same location but change the name as secret.txt

# Configure the jenkins pipeline to deploy on AWS EKS

Now goto jenkins -> Manage jenkins -> plugins -> avilable plugins -> select : Kubernetes/Kubernetes Credentials / Kubernetes Client APi / Kubernetes CLI : install all of them -> Go back to dashboard

Now goto jenkins -> Manage jenkins -> credentials -> global:add credentials , kind=scretfile : ID=kubernetes : Description=kubernetes : in there choose the file that we have created and renamed as secret.txt

Now click on our jenkins pipeline -> configure -> Go to our script :

```bash


pipeline{
     agent any

     tools{
         jdk 'jdk17'
         nodejs 'node16'
     }
     environment {
         SCANNER_HOME=tool 'sonarqube-scanner'
     }

     stages {
         stage('Clean Workspace'){
             steps{
                 cleanWs()
             }
         }
         stage('Checkout from Git'){
             steps{
                 git branch: 'main', url: 'https://github.com/tharindu-frd/ML-FLOW-integration-with-AWS-SAGEMAKER.git'
             }
         }
         stage("Sonarqube Analysis "){
             steps{
                 withSonarQubeEnv('SonarQube-Server') {
                     sh ''' $SCANNER_HOME/bin/sonar-scanner -Dsonar.projectName=flask-CI \
                     -Dsonar.projectKey=flask-CI '''
                 }
             }
         }
         stage("Quality Gate"){
            steps {
                 script {
                     waitForQualityGate abortPipeline: false, credentialsId: 'SonarQube-Token'
                 }
             }
         }
         stage('Install Dependencies') {
             steps {
                 sh "npm install"
             }
         }
         stage('TRIVY FS SCAN') {
             steps {
                 sh "trivy fs . > trivyfs.txt"
             }
         }
          stage("Docker Build & Push"){
             steps{
                 script{
                    withDockerRegistry(credentialsId: 'dockerhub', toolName: 'docker'){
                        sh "docker build -t swiggy-clone ."
                        sh "docker tag swiggy-clone chandima35687729/flask-app:latest "
                        sh "docker push chandima35687729/flask-app:latest "
                     }
                 }
             }
         }
         stage("TRIVY"){
             steps{
                 sh "trivy image chandima35687729/flask-app:latest > trivyimage.txt"
             }
         }
          stage('Deploy to Kubernets'){
             steps{
                 script{
                     dir('Kubernetes') {
                         <see  below how to generate this command> {
                         sh 'kubectl delete --all pods'
                         sh 'kubectl apply -f deployment.yml'
                         sh 'kubectl apply -f service.yml'
                         }
                     }
                 }
             }
         }



     }
 }




```

Now before save that -> click on pipeline Syntax -> in the drop down of sample step select "withKubeConfig: Configure Kubernetes CLI(kubectl)" and in credentials select secret.txt -> click on Generate Pipeline Script -> copy that command and paste that in above script

Now click on apply and save .

# Set the trigger

Now select our jenkins pipeline -> configure -> put a tick on Github project and give our project url and under the build triggers , put a tick on 'Githubhook trigger for GITScm polling' , Now to to git project repo -> settings -> webhooks (on the left pane ) -> add webhook -> in there as the url : go to jenkins and copy and paste the url from the browser and paste it and type /github-webhook (for ex http://15.206.94.253.8080/github-webhook) and click on add webhook

Now goto mobaxterm

```bash
kubectl get svc # this will give us a service name under EXTERNAL-IP and that is the link for our website

```
