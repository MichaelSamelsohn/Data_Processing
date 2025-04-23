# Imports #
from Image_Processing.Basic.image import Image
from Image_Processing.Metashells.doublet_processing import doublet_processing
from Image_Processing.Metashells.spatial_comparison import spatial_comparison
from Image_Processing.Metashells.spatial_conversion import spatial_conversion


# Loading the doublet image.
doublet = Image("C:\\Users\\micha\\PycharmProjects\\Data_Processing\\Images\\Noiseless_Doublet.mat")

# Image processing #
thinned_image = doublet_processing(doublet=doublet.image)

# Spatial conversion #
x1, y1 = spatial_conversion(thinned_image=thinned_image)

# Spatial plotting #
spatial_comparison(x1=x1, y1=y1)
