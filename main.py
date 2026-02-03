import cv2 as cv
from pydicom import dcmread
import numpy as np 
import tkinter
from tkinter import filedialog
import os
import sys

def show_menu():
    """Display main menu"""
    print("\n" + "="*50)
    print("        DICOM Image Processor")
    print("="*50)
    print("1. Load DICOM file")
    print("2. Exit")
    print("="*50)
    
    while True:
        choice = input("Select option (1-2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Invalid choice. Please enter 1 or 2.")

def select_file():
    """Opens a file dialog and returns the selected file path."""
    try:
        # Создаем отдельное окно Tkinter
        root = tkinter.Tk()
        root.withdraw()  # Скрываем основное окно
        root.attributes('-topmost', True)  # Делаем окно поверх всех
        
        # Устанавливаем начальную директорию
        initial_dir = os.getcwd()
        
        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            parent=root,
            initialdir=initial_dir,
            title='Please select a DICOM file',
            filetypes=[
                ("DICOM files", "*.dcm"),
                ("All files", "*.*")
            ]
        )
        
        # Закрываем Tkinter
        root.destroy()
        
        return file_path
        
    except Exception as e:
        print(f"Error opening file dialog: {e}")
        return None

def process_dicom_file(file_path):
    """Process DICOM file and save results"""
    try:
        print(f"\nProcessing file: {file_path}")
        
        # Получаем имя файла без расширения
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        FLIP_ANGLE = [0x0018, 0x1314]  # sop uid metadata
        SEQUENCE_NAME = [0x0018, 0x0024]

        def convert_dtype(img: np.ndarray, out_dtype: np.dtype) -> np.ndarray:
            """Convert images to another dtype preserving relative intensities"""
            info = np.iinfo(img.dtype)
            data = img.astype(np.float64) / info.max
            data = np.iinfo(out_dtype).max * data
            img_new = data.astype(out_dtype)
            return img_new

        def binary_mask(arr: np.ndarray, contours):
            """Draws a mask or contours"""
            signal_mask = np.zeros(arr.shape, dtype=np.uint8) 
            cv.drawContours(signal_mask, contours, contourIdx=-1, color=(255, 255, 255), thickness=-1)
            return signal_mask

        # Читаем DICOM файл
        ds = dcmread(file_path)
        image_raw = ds.pixel_array
        flip_angle = ds[FLIP_ANGLE]
        seq_name = ds[SEQUENCE_NAME]

        img_norm = convert_dtype(image_raw, np.uint8)

        # Бинаризация изображения
        ret, thresh = cv.threshold(img_norm, 80, 255, 0)

        contours, hierarchy = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # ROI бинарная маска
        phnatom_mask = binary_mask(image_raw, contours)

        # Эрозия и дилатация для внутренних и внешних контуров
        kernel = np.ones((3, 3), np.uint8)
        inner_mask = cv.erode(phnatom_mask, kernel, iterations=5)
        external_mask = cv.dilate(phnatom_mask, kernel, iterations=5)
        mask_noise = cv.subtract(external_mask, phnatom_mask)

        # Расчет SNR
        signal_pixels = image_raw[inner_mask == 255]
        S_std = np.std(signal_pixels)
        S_mean = np.mean(signal_pixels)
        S_min = np.min(signal_pixels)
        S_max = np.max(signal_pixels)   

        noise_pixels = image_raw[mask_noise == 255]
        N_std = np.std(noise_pixels)
        N_mean = np.mean(noise_pixels)
        N_min = np.min(noise_pixels)
        N_max = np.max(noise_pixels)   

        # Контуры
        inner_contours, _ = cv.findContours(inner_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        external_contours, _ = cv.findContours(external_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # Конвертация в RGB для отрисовки цветов
        img_vis = cv.cvtColor(img_norm, cv.COLOR_GRAY2BGR)

        # Рисуем контуры
        cv.drawContours(img_vis, inner_contours, contourIdx=-1, color=(255, 0, 0), thickness=1)
        cv.drawContours(img_vis, external_contours, contourIdx=-1, color=(0, 0, 255), thickness=1)

        w, h, _ = img_vis.shape

        # Добавляем текст
        font = cv.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        font_thickness = 1
        color = (255, 255, 255)

        # Вывод информации о файле
        print(f"  Sequence: {seq_name.value}")
        print(f"  Flip Angle: {flip_angle.value}")
        print(f"  Image size: {w}x{h}")
        
        # Результаты анализа
        print("\n  Signal Analysis:")
        print(f"    Std: {S_std:.2f}")
        print(f"    Mean: {S_mean:.2f}")
        print(f"    Min: {S_min}")
        print(f"    Max: {S_max}")
        
        print("\n  Noise Analysis:")
        print(f"    Std: {N_std:.2f}")
        print(f"    Mean: {N_mean:.2f}")
        print(f"    Min: {N_min}")
        print(f"    Max: {N_max}")
        
        # Расчет SNR
        if N_std > 0:
            snr = S_mean / N_mean
            print(f"\n  SNR: {snr:.2f}")

        # Текст слева на изображении
        y_offset = 20
        left_texts = [
            f"Sstd: {S_std:.2f}",
            f"Smean: {S_mean:.2f}",
            f"Smin: {S_min}",
            f"Smax: {S_max}"
        ]
        
        for text in left_texts:
            cv.putText(img_vis, text, (10, y_offset), font, font_scale, color, font_thickness)
            y_offset += 20

        # Текст справа на изображении
        y_offset = 20
        right_texts = [
            f"Nstd: {N_std:.2f}",
            f"Nmean: {N_mean:.2f}",
            f"Nmin: {N_min}",
            f"Nmax: {N_max}"
        ]
        
        for text in right_texts:
            text_size = cv.getTextSize(text, font, font_scale, font_thickness)[0]
            x = w - text_size[0] - 10
            cv.putText(img_vis, text, (x, y_offset), font, font_scale, color, font_thickness)
            y_offset += 20

        cv.putText(img_vis, f"Flip Ang: {flip_angle.value}", (10, h-20),
        cv.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    
        cv.putText(img_vis, f"Seq: {seq_name.value}", (10, h-40),
        cv.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

        cv.putText(img_vis, f"SNR: {snr:.2f}", (w - text_size[0] - 10, h-20),
        cv.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

        # Сохраняем результат
        output_file = f"{base_name}.png"
        cv.imwrite(output_file, img_vis)
        print(f"\n  Result saved as: {output_file}")
        
        # Возвращаемся в меню
        print("\nPress Enter to continue...")
        input()
        
        return True
        
    except Exception as e:
        print(f"\nError processing file: {e}")
        print("Press Enter to continue...")
        input()
        return False

def main():
    """Main function with menu-driven interface"""
    print("Starting DICOM Image Processor...")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Загрузка файла
            file_path = select_file()
            
            if file_path:
                if os.path.exists(file_path):
                    process_dicom_file(file_path)
                else:
                    print(f"\nFile not found: {file_path}")
                    print("Press Enter to continue...")
                    input()
            else:
                print("\nNo file selected.")
                print("Press Enter to continue...")
                input()
                
        elif choice == '2':
            print("\nThank you for using DICOM Image Processor!")
            print("Exiting...")
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Press Enter to exit...")
        input()
        sys.exit(1)
