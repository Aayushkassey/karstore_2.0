# Smart Retention System for E-Commerce

<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-green?style=for-the-badge&logo=django" />
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-blue?style=for-the-badge&logo=postgresql" />
  <img src="https://img.shields.io/badge/XGBoost-Churn%20Prediction-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/LightFM-Recommendation%20Engine-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FastAPI-ML%20Serving-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Render-Deployed-purple?style=for-the-badge" />
</p>


<p style="color:red;">
NOTICE: The automated retraining has failed because the database was automatically dropped from the free hosting service. As a result, our retraining model cannot fetch new data.
</p>

---

# Overview

Smart Retention System for E-Commerce is an intelligent retention-focused e-commerce platform designed to proactively reduce customer churn using Machine Learning.

Unlike traditional recommendation systems, this platform combines:

- **XGBoost-based Churn Prediction**
- **LightFM Hybrid Recommendation System**
- **Automated Personalized Email Retention**
- **Autonomous Daily Model Retraining**
- **Dynamic User-Specific Shopping Experience**

The system continuously analyzes user interactions and predicts users likely to churn.  
Users above a predefined churn threshold are automatically targeted with personalized product recommendations generated based on their interaction history and interests.

The entire workflow is designed to be autonomous and scalable.

---

# Core Features

## Intelligent Churn Prediction
- Built using **XGBoost**
- Predicts probability of user churn
- Users above a churn threshold (`0.75`) are flagged as high-risk users
- Enables proactive customer retention strategies

---

## Hybrid Recommendation System
- Built using **LightFM**
- Generates personalized product recommendations
- Recommendation results vary dynamically for every user
- Learns from:
  - User interactions
  - Product engagement
  - Shopping behavior

---

## Automated Retention Email System
- Personalized recommendation emails sent automatically
- Triggered for users with high churn probability
- Weekly recommendation campaign system
- Admin can:
  - Send emails manually
  - Or allow automated scheduled delivery

---

## Autonomous Model Retraining

The recommendation engine is retrained automatically every day at:

```bash
00:00 UTC
```

Retraining is handled through:
- GitHub Actions
- Hugging Face Spaces automation pipeline

This ensures recommendation quality improves continuously as user interaction data evolves.

---

# System Architecture

```text
User Interaction Data
          │
          ▼
 PostgreSQL Database
          │
          ├──────────────► XGBoost Churn Prediction
          │                         │
          │                         ▼
          │               High Churn Users
          │                         │
          ▼                         ▼
 LightFM Recommendation Engine ─────┘
          │
          ▼
 Personalized Product Recommendations
          │
          ▼
 Automated Email Retention Campaign
```

---

# Tech Stack

| Category | Technology |
|---|---|
| Backend | Django 6 |
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Database | PostgreSQL |
| ML Frameworks | XGBoost, LightFM |
| API Serving | FastAPI |
| Deployment | Render |
| Automation | GitHub Actions |
| Retraining Infrastructure | Hugging Face Spaces |
| Programming Language | Python 3.12.2 |

---

# Machine Learning Modules

## Churn Prediction Model

Repository:  
🔗 https://github.com/kamalpokhara/XGBoost-Churn-Prediction-Model

### Responsibilities
- Predict user churn probability
- Identify high-risk customers
- Provide churn scores for retention workflow

### Model Used
- XGBoost Classifier

---

## Recommendation Engine

Repository:  
🔗 https://github.com/kamalpokhara/LightFM-Recommendation-System

### Responsibilities
- Generate personalized recommendations
- Learn from user-product interactions
- Improve recommendation quality over time

### Model Used
- LightFM Hybrid Recommendation Model

---

## ML API Service

Repository:  
🔗 https://github.com/kamalpokhara/srs-api

### Responsibilities
- Serve ML models through FastAPI
- Connect Django application with ML services
- Provide prediction and recommendation endpoints

---

## Main E-Commerce Platform

Repository:  
🔗 https://github.com/Aayushkassey/karstore_2.0

### Responsibilities
- Complete e-commerce workflow
- User interaction system
- Product management
- Cart and shopping experience
- Admin dashboard
- Frontend and backend integration

---

# Admin Dashboard Features

The system includes an administrative dashboard capable of:

- Monitoring churn distribution
- Viewing churn-risk user percentages
- Triggering manual retention emails
- Monitoring user activity trends
- Managing recommendation campaigns

---

# Personalized Shopping Experience

Each user receives:
- Different product recommendations
- Dynamic shopping experience
- Personalized retention campaigns
- Customized engagement workflow

The system behavior adapts based on:
- Interaction history
- Product engagement
- Predicted retention probability

---

# Contributors

<table>
<tr>

<td align="center" width="50%">

<img src="https://github.com/kamalpokhara.png" width="120px;" alt="Kamal Poudel"/>

### Kamal Poudel

Machine Learning   
Research & System Integration

<a href="https://github.com/kamalpokhara">GitHub Profile</a>

#### Contributions
- Original project idea
- Churn prediction system
- Recommendation engine
- ML integration
- FastAPI model serving
- Automation pipeline
- Hugging Face retraining workflow
- GitHub Actions scheduling

</td>

<td align="center" width="50%">

<img src="https://github.com/Aayushkassey.png" width="120px;" alt="Aayush K.C"/>

### Aayush K.C

Django Full Stack Developer

<a href="https://github.com/Aayushkassey">GitHub Profile</a>

#### Contributions
- Django e-commerce application
- Frontend implementation
- Backend development
- Authentication system
- Shopping workflow
- Product management
- UI integration
- Admin dashboard

</td>

</tr>
</table>

---

# Future Improvements

- Real-time recommendation retraining
- Live behavioral analytics
- Multi-model ensemble churn prediction
- Advanced email personalization
- User segmentation using clustering
- Real-time event streaming pipeline
- Containerized microservice architecture

---

# Installation

```bash
git clone <your prefered repo link>
```

```bash
cd project-directory
```

```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py runserver
```

---

# Research Focus

This project focuses on:

- Predictive customer retention
- Autonomous recommendation systems
- Hybrid recommender systems
- Behavioral analytics
- Proactive engagement strategies
- AI-driven e-commerce personalization

---

# License

This project is developed for educational and research purposes.

---

# Project Status

✅ Active Development  
✅ Autonomous Retraining Pipeline  
✅ Integrated ML Recommendation System  
✅ Integrated Churn Prediction System  
✅ Personalized Retention Workflow  

<p align="center"> <i> We recently discovered a **data leakage issue** in the churn prediction model (identified on **26th July**).  
All other components and workflows are stable and can be used as reference for architecture and integration patterns.
</i><p>


<p align="center">
  Built with Django, FastAPI, XGBoost, LightFM, and PostgreSQL
</p>
