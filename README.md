# SkinAI - Skin Cancer Detection App

An AI-powered web application that analyzes dermoscopy images and classifies skin lesions as Benign or Malignant using a VGG16 deep learning model.

---

## Demo Video

[Click here to watch the demo](https://drive.google.com/file/d/17FpdV6-fj8Dk4WilaH8hpSMdGY9RPn0F/view?usp=sharing)

---

## Features

- Doctor login system
- Dashboard with statistics (total patients, malignant cases, benign cases)
- Upload dermoscopy images for AI analysis
- Diagnosis with confidence score
- Patient history management
- PDF report export per patient

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python + Flask |
| AI Model | VGG16 (Transfer Learning + Fine-Tuning) |
| Database | MySQL |
| Frontend | HTML + Tailwind CSS |
| Training | Google Colab + TensorFlow |

---

## Model

- Architecture: VGG16 pretrained on ImageNet, fine-tuned on skin lesion images
- Task: Binary classification (Benign / Malignant)
- Validation Accuracy: 81%
- Training set: 493 dermoscopy images
- Test set: 132 dermoscopy images
- Blocks 4 and 5 of VGG16 were unfrozen for fine-tuning

---

## Project Structure

skin_cancer_detect/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   └── schema.sql
├── model/
│   └── vgg16_skin_cancer.h5
├── static/
│   └── uploads/
└── templates/
├── base.html
├── login.html
├── dashboard.html
├── predict.html
├── result.html
└── patients.html
---

## How to Run Locally

1. Clone the repository
git clone https://github.com/wassiLabsx/skin-cancer_detection-.git
cd skin-cancer_detection-

2. Install dependencies
pip install -r requirements.txt

3. Set up MySQL database using database/schema.sql

4. Add the trained model to model/vgg16_skin_cancer.h5

5. Run the app
python app.py

6. Open your browser at http://localhost:5000

Default login: admin / admin123

---

## Disclaimer

This application is AI-assisted and should not replace professional medical judgment. 
Always consult a certified dermatologist.
