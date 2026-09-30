#Librerias Python estándar y de terceros
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml


#modulos de la carpeta src
import src.extract.extract_csv as extract_csv
import src.transform.clean_excel as clean_excel
import src.load.load_database as load

def main():

    #configuracion del archivo yaml
    with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file)
        

    #extraer datos desde students_basic

    
    students_basic_df = extract_csv.extract_csv(
    f"{config['paths']['bronze_dir']}/{config['source']['students_basic']}"
    )

    #llamar a la transformacion para limpiar el DataFrame
    students_basic_df = clean_excel.limpiar_excel()


    


if __name__ == "__main__":
    main()