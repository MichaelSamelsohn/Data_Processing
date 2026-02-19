# Imports #
from image import Image


def reset_image(image):
    image.reset_to_original_image()
    image.convert_to_grayscale()
    image._image_buffer = image._image_buffer[:-1]


def intensity_transformations(image):
    image.negative()

    reset_image(image=image)

    image.gamma_correction(gamma=0.5)
    reset_image(image=image)
    image.gamma_correction(gamma=2)

    reset_image(image=image)

    image.display_all_images()
    image._image_buffer = image._image_buffer[:-3]

    image.bit_plane_reconstruction(degree_of_reduction=1)
    reset_image(image=image)
    image.bit_plane_reconstruction(degree_of_reduction=4)
    reset_image(image=image)
    image.bit_plane_reconstruction(degree_of_reduction=7)

    reset_image(image=image)

    image.display_all_images()
    image._image_buffer = image._image_buffer[:-3]

    image.bit_plane_slicing(bit_plane=1)
    reset_image(image=image)
    image.bit_plane_slicing(bit_plane=4)
    reset_image(image=image)
    image.bit_plane_slicing(bit_plane=7)

    reset_image(image=image)

    image.display_all_images()


def noise_models(image):
    image.add_gaussian_noise(sigma=0.02)
    reset_image(image=image)
    image.add_rayleigh_noise()
    reset_image(image=image)
    image.add_erlang_noise()
    reset_image(image=image)
    image.add_exponential_noise()
    reset_image(image=image)
    image.add_uniform_noise()
    reset_image(image=image)
    image.add_salt_and_pepper(salt=0.01, pepper=0.01)

    reset_image(image=image)

    image.display_all_images()

def main():
    image = Image(image_path=r"C:\Users\micha\PycharmProjects\Data_Processing\Image_Processing\Images\Lena.png")
    image.convert_to_grayscale()

    # Intensity transformations.
    # intensity_transformations(image=image)
    # Nosie models.
    noise_models(image=image)


if __name__ == "__main__":
    main()
