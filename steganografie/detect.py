import cv2
import numpy as np
import matplotlib.pyplot as plt

# Načtení šachovnicového obrázku
image = cv2.imread('C:\\Users\\yscxd\\OneDrive\Plocha\\vsb\\FA\\steganografie\\output.png', cv2.IMREAD_GRAYSCALE)

# Extrahujte nejnižší bity
lsb_bits = np.bitwise_and(image, 1)

# Spočítejte histogram nejnižších bitů
histogram = np.histogram(lsb_bits, bins=2, range=[0, 2])[0]

# Zobrazte histogram
plt.bar([0, 1], histogram)
plt.xticks([0, 1], ['0', '1'])
plt.xlabel('Nejnižší bity')
plt.ylabel('Počet pixelů')
plt.title('Histogram nejnižších bitů')
plt.show()

# Detekce steganografie na základě histogramu
threshold = 0.1  # Práh pro detekci steganografie (upravte podle potřeby)
if histogram[1] < threshold * image.size:
    print('Podezřelý histogram nejnižších bitů. Možná steganografie.')
else:
    print('Normální histogram nejnižších bitů.')
