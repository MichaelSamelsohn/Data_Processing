# Imports #
from Image_Processing.Settings.meta_shells_settings import *
from meta_shells import MetaShell

# # Noiseless doublet.
# doublet = MetaShell(shell_path="C:\\Users\\micha\\PycharmProjects\\Data_Processing\\Images\\Noiseless_Doublet.mat",
#                     processing_parameters = PROCESSING_PARAMETERS,
#                     multifoil_parameters = MULTIFOIL_PARAMETERS,
#                     number_of_coefficients = NUMBER_OF_COEFFICIENTS,
#                     scaling_factor = SCALING_FACTOR)

# Noisy doublet.
doublet = MetaShell(shell_path="C:\\Users\\micha\\PycharmProjects\\Data_Processing\\Images\\Noisy_Doublet.mat",
                    processing_parameters=PROCESSING_PARAMETERS,
                    multifoil_parameters=MULTIFOIL_PARAMETERS,
                    number_of_coefficients=NUMBER_OF_COEFFICIENTS,
                    scaling_factor=SCALING_FACTOR,
                    debug_mode=DEBUG_MODE,
                    display_time=DISPLAY_TIME)

doublet.process()
