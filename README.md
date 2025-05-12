# Exam App - Setup Instructions

Follow the steps below to set up the environment and install necessary dependencies for the project.

---

## 1. Download Models

Download the required models from the following Google Drive link:

🔗 [Google Drive - Models](https://drive.google.com/drive/folders/1aKDETzxYmWh5b4HcS1tUOJLwV_SwMeBk)

After downloading, place all the model files into the following directory:

```
exam_app/cv/Code/models
```

---

## 2. Create and Activate Conda Environment

Open your terminal or Anaconda prompt and run:

```bash
conda create -n ai python==3.7.0
conda activate ai
```

---

## 3. Install dlib

To install `dlib`, run:

```bash
conda install -c conda-forge dlib
```

---

## 4. Install Project Dependencies

Ensure you're in the directory containing `requirements.txt`, then install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## 5. Run the Application

### Terminal 1 – Start the Django Server

Navigate to the root project directory (where `manage.py` is located) and run:

```bash
python manage.py runserver
```

### Terminal 2 – Run the Proctoring Worker

Navigate to the CV processing directory and run:

```bash
cd exam_app/cv/Code
python proctoring_worker.py
```

---
