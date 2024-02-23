**FEM-based machine learning in childbirth simulations**

1 - Generate data: generate and run a specific number of finite element simulations.
    Includes:
    
        1 - Morphing algorithm to modify the initial geometry of the pelvic floor muscles (main_morphing.py).
        
        2 - Change initial parameters for each simulation.
        
        3 - Checks whether the simulation is successfully completed or not. If yes, saves the results from the odb file (results.py). 

2 - Get data: retrieve the results of the finite element simulations performed and create a structured dataset. 

3 - Train model: pipeline to train a machine learning model with the dataset created.
