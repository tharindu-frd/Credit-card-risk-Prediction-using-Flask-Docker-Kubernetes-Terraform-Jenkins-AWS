from setuptools import setup

with open("README.md",'r',encoding="utf-8") as f :
       long_description = f.read()


setup(
       name="src",
       version="0.0.1",
       author= "Tharindu",
       description="API with deployment",
       long_description=long_description,
       long_description_content_type="text/markdown",
       author_email="chandima35687@gmail.com",
       packages=["src"],
       python_requires=">3.7",
       install_requires = [
              
              'pandas',
              'scikit-learn'
              
       ]





)