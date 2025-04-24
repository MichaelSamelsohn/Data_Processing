from meta_shells import MetaShell

doublet = MetaShell(shell_path="C:\\Users\\micha\\PycharmProjects\\Data_Processing\\Images\\Noiseless_Doublet.mat")
doublet.doublet_processing()
doublet.spatial_conversion()
doublet.spatial_comparison()
doublet.dft_2d()
