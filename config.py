import os

class Config:
    SECRET_KEY = "skinai-secret-key-change-in-production"

    # File upload
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # Database
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_NAME = "skin_cancer_db"

    # Model
    MODEL_PATH = os.path.join("model", "vgg16_skin_cancer.h5")
    IMG_SIZE = (224, 224)

    # HAM10000 — 7 class labels
    CLASS_LABELS = {
        0: {"name": "Actinic Keratoses",    "short": "AKIEC", "risk": "Pre-malignant"},
        1: {"name": "Basal Cell Carcinoma", "short": "BCC",   "risk": "Malignant"},
        2: {"name": "Benign Keratosis",     "short": "BKL",   "risk": "Benign"},
        3: {"name": "Dermatofibroma",       "short": "DF",    "risk": "Benign"},
        4: {"name": "Melanoma",             "short": "MEL",   "risk": "Malignant"},
        5: {"name": "Melanocytic Nevi",     "short": "NV",    "risk": "Benign"},
        6: {"name": "Vascular Lesions",     "short": "VASC",  "risk": "Benign"},
    }