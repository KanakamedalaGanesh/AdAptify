# AdAptify

AdAptify – AI-Driven Personalized Marketing Platform.

AdAptify is an AI-powered, cloud-native marketing platform designed to automate and personalize customer engagement across multiple industries. Built using Flask and MySQL, and deployed on AWS EC2 with Amazon RDS, this platform enables businesses to manage tailored marketing campaigns, schedule WhatsApp messages, and analyze user behavior in real-time.

🚀 Features

🎯 Personalized marketing campaign creation

📊 Real-time customer insights and behavior tracking

📱 WhatsApp message scheduling and automation

🔐 Secure user authentication with session management

☁️ AWS-based scalable and secure deployment

📂 Storage of media assets using Amazon S3

🔍 Monitoring and performance tracking with CloudWatch


🧱 Tech Stack

Backend: Python (Flask), MySQL, SQLAlchemy

Frontend: HTML5, CSS3, JavaScript

Cloud Services: AWS EC2, RDS (MySQL), S3, Lambda, CloudWatch

DevOps: MobaXterm (for remote SSH), Git, Apache/Nginx


🛠 Setup Instructions

1. Clone this repo:

git clone https://github.com/your-username/AdAptify.git
cd AdAptify


2. Set up your virtual environment and install dependencies:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


3. Configure your database connection in config.py with your RDS credentials.


4. Run the Flask app:

python app.py



🧪 Testing

Manual and unit tests for user registration, login, campaign creation

Database updates verified via MySQL Workbench

UI tested for responsiveness and error handling


📈 Use Cases

E-commerce platforms delivering tailored product recommendations

Healthcare apps automating patient reminders

SaaS tools offering client-specific marketing analytics


📄 License

This project is for educational/demo purposes. For licensing or deployment inquiries, please contact the maintainer. 
