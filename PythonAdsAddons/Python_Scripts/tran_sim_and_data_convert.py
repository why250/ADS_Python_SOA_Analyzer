from keysight.ads import de
from keysight.ads.de import db_uu as db
from keysight.ads.de.db import LayerId
from keysight.edatoolbox import ads
import os
import keysight.ads.dataset as dataset
import matplotlib.pyplot as plt
from IPython.core import getipython
from pathlib import Path
import numpy as np
import seaborn as sns

def tran_sim_and_data_convert(design_name:str,workspace_path:str):

    # workspace = de.open_workspace(workspace_path)

    lib_name,cell_name,view_name = design_name.split(":");
    design = db.open_design(f"{design_name}")

    # netlist creation and simulation
    netlist = design.generate_netlist()

    target_output_dir = os.path.join(workspace_path,"data")
    simulator = ads.CircuitSimulator()
    simulator.run_netlist(netlist,output_dir = target_output_dir)
    print("Run successfully.")

    output_data = dataset.open(Path(os.path.join(target_output_dir,f"{cell_name}"+".ds")))
    #print(output_data.varblock_names)

    for data_block in output_data.find_varblocks_with_var_name("time"):
        print("time is found in:",data_block.name)
        time_block_name = data_block.name

    mydata = output_data[time_block_name].to_dataframe().reset_index()
    csv_file_path = os.path.join(target_output_dir,f"{cell_name}"+".csv")
    mydata.to_csv(csv_file_path)
    print("Ds is converted to Dataframe.")


if __name__ == "__main__":

    pass