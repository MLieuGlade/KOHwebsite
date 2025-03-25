import os.path
from PIL import Image
from flask import Flask, request, jsonify
import requests
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

UPPLOAD_FOLDER = 'images'
TARGET_URL = "http://localhost:5000/"



def convert_image(filepath_main: str, filepath_watermark: str, location: str, opacity: float):
    image_main = Image.open(filepath_main)
    image_watermark = Image.open(filepath_watermark)

    try:
        # Преобразуем изображение в формат RGBA, если он еще не в этом формате
        if image_watermark.mode != 'RGBA':
            image_watermark = image_watermark.convert('RGBA')

        # Получаем данные изображения
        img_data = image_watermark.getdata()

        # Создаем новый список пикселей с измененной непрозрачностью
        new_data = []
        for item in img_data:
            # item - это кортеж (R, G, B, A)
            r, g, b, a = item
            new_alpha = int(a * opacity)  # Умножаем текущий альфа-канал на заданную непрозрачность
            new_data.append((r, g, b, new_alpha))

        # Обновляем данные изображения
        image_watermark.putdata(new_data)

        # Сохраняем измененное изображение
        image_watermark.save(filepath_watermark[0 : len(filepath_watermark)-3]+"png", "PNG")  # Важно сохранить в PNG, чтобы сохранить прозрачность

        print(f"Непрозрачность изображения изменена и сохранена в {filepath_watermark}")

    except FileNotFoundError:
        print(f"Ошибка: Файл {filepath_watermark} не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

    x=0
    y=0

    match location:
        case 'center':
            x = (image_main.width - image_watermark.width) * 0.5
            y = (image_main.height - image_watermark.height) * 0.5
        case 'right_up':
            x = (image_main.width - image_watermark.width) * 0.9
            y = (image_main.height - image_watermark.height) * 0.1
        case 'right_down':
            x = (image_main.width - image_watermark.width) * 0.9
            y = (image_main.height - image_watermark.height) * 0.9
        case 'left_up':
            x = (image_main.width - image_watermark.width) * 0.1
            y = (image_main.height - image_watermark.height) * 0.1
        case 'left_down':
            x = (image_main.width - image_watermark.width) * 0.1
            y = (image_main.height - image_watermark.height) * 0.9

    if image_watermark.mode in ("RGBA", "LA") or (image_watermark.mode == "P" and 'transparency' in image_watermark.info):
        # Если есть прозрачность, используем ее как маску
        image_main.paste(image_watermark, (int(x), int(y)), image_watermark)
    else:
        # Если нет прозрачности, просто вставляем изображение
        image_main.paste(image_watermark, (int(x), int(y)))

    return image_main

@app.route('/imagepost', methods=['POST'])
def upload_image():
    position = request.form.get('position')
    opacity = request.form.get('opacity')
    image_main = request.files['image']
    image_watermark = request.files['watermark']
    filepath_main = os.path.join(UPPLOAD_FOLDER, image_main.filename)
    image_main.save(filepath_main)
    filepath_watermark = os.path.join(UPPLOAD_FOLDER, image_watermark.filename)
    image_watermark.save(filepath_watermark)

    convert_image(filepath_main, filepath_watermark, position, float(opacity)).save("watermark.jpg")

    files = {}
    response = requests.post(TARGET_URL, files = files)

    return jsonify({'result': "watermark.jpg"}), 200

